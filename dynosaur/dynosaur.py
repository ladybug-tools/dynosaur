"""Collection of functions for Revit."""
import objects
import window
import curtainwall
import util
import room
import collector

import clr
clr.AddReference("RevitAPI")
# DB for spatial element calculator
import Autodesk.Revit.DB as DB

# Import DocumentManager and TransactionManager
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager


def create_rooms(rooms, boundary_location=1):
    """Creat dynosaur rooms from revit rooms.

    This script will only work from inside Dynamo nodes. for a similar script
    forRrevit check this link for more details:
    https://github.com/jeremytammik/SpatialElementGeometryCalculator/
        blob/master/SpatialElementGeometryCalculator/Command.cs
    """
    # unwrap room elements
    # this is not the right way of logging in python and probably any other language
    log = []
    rooms = tuple(util.get_internal_elements(rooms))
    if not rooms:
        return []

    # start Transactions. This might look unnecessary but I had issues with permissions
    # when trying to access rooms.
    # Start Transaction
    # doc = DocumentManager.Instance.CurrentDBDocument
    # TransactionManager.Instance.EnsureInTransaction(doc)

    # create a spatial element calculator to calculate room data
    doc = rooms[0].Document
    options = DB.SpatialElementBoundaryOptions()
    options.SpatialElementBoundaryLocation = \
        util.get_boundary_location(boundary_location)
    calculator = DB.SpatialElementGeometryCalculator(doc, options)

    opt = DB.Options()
    element_collector = []
    room_collector = range(len(rooms))

    # all the curtain panels
    cps = collector.collect_curtain_panels()

    # surface_collector = {}  # collect hbSurfaces so I can set adjucent surfaces
    for room_count, revit_room in enumerate(rooms):
        # initiate zone based on room id
        element_collector.append([])
        new_room = objects.create_room(revit_room.Id)

        # calculate spatial data for revit room
        revit_room_spatial_data = calculator.CalculateSpatialElementGeometry(revit_room)

        # get the geometry of the room
        revit_room_geometry = revit_room_spatial_data.GetGeometry()

        # Cast revit room faces to dynamo geometry using ToProtoType method
        room_faces_dyn = room.get_dynamo_room_faces(revit_room_geometry)

        assert revit_room_geometry.Faces.Size == len(room_faces_dyn), \
            "Number of rooms elements ({}) doesn't match number of faces ({}).\n" \
            "Make sure the Room is bounded.".format(revit_room_geometry.Faces.Size,
                                                    len(room_faces_dyn))

        for count, face in enumerate(revit_room_geometry.Faces):
            # base face is useful to project the openings to room boundary
            base_face_dyn = room_faces_dyn[count]

            # Revit is strange! if two roofs have a shared wall then it will be
            # duplicated! By checking the values inside the _collector I try to avoid
            # that.
            _collector = []

            boundary_faces = revit_room_spatial_data.GetBoundaryFaceInfo(face)

            if len(boundary_faces) == 0:
                # There is no boundary face! I don't know what does this exactly mean
                # in the Revit world but now that there is no boundary face we can just
                # use the dynamo face and create the surface!
                face_vertices = tuple(v.PointGeometry for v in base_face_dyn.Vertices)

                new_surface = objects.create_surface(
                    "%s_%s" % (new_room['name'], util.create_uuid()),
                    new_room['name'],
                    face_vertices
                )

                objects.add_surface_to_room(new_room, new_surface)
                continue

            for boundary_face in boundary_faces:
                # boundary_face is a SpatialElementBoundarySubface
                # we need to get the element (Wall, Roof, etc) first
                boundary_element = doc.GetElement(
                    boundary_face.SpatialBoundaryElement.HostElementId
                )

                # initiate honeybee surface
                face_vertices = tuple(v.PointGeometry for v in base_face_dyn.Vertices)

                # TODO(mostapha) This should be done once when all the surfaces are
                # created.
                if face_vertices in _collector:
                    continue

                new_surface = objects.create_surface(
                    "%s_%s" % (new_room['name'], boundary_element.Id),
                    new_room['name'],
                    face_vertices
                )

                # TODO(mostapha) This should be done once when all the surfaces are
                # created.
                _collector.append(face_vertices)

                # collect element id for each face.
                # this can be part of the object itself. I need to think about it before
                # adding it to the object. Trying to keep it as light as possible
                element_collector[room_count].append(doc.GetElement(
                    boundary_face.SpatialBoundaryElement.HostElementId
                ))

                # I'm not sure how this works in Revit but I assume there is an easy
                # way to find the adjacent surface for an element. Let's hope this time
                # revit doesn't let me down!
                # if boundary_element.Id not in surface_collector:
                #     surface_collector[boundary_element.Id] = new_surface
                # else:
                #     # TODO(mostapha): set adjacent surface
                #     pass

                # -------------------------------------------------------------------- #
                # ----------------------- child surfaces ----------------------------- #
                # -------------------------------------------------------------------- #

                # time to find child surfaces (e.g. windows!)
                # this is the reason dynosaur exists in the first place

                # Take care of curtain wall systems
                # This will most likely fail for custom curtain walls
                if util.get_parameter(boundary_element, 'Family') == 'Curtain Wall':
                    # get cooredinates and element ids for this curtain wall.

                    # _elementIds, _coordinates = curtainwall.extract_panels_vertices(
                    #     boundary_element, base_face_dyn, opt)
                    _elementIds, _coordinates = \
                        curtainwall.extract_curtain_panel_vertices(cps, base_face_dyn)
                    for count, coordinate in enumerate(_coordinates):
                        if not coordinate:
                            log.append("{} has an opening with less than "
                                       "two coordinates. It has been removed!"
                                       .format(_elementIds[count]))
                            continue

                        # create honeybee surface - use element id as the name
                        new_fen_surface = objects.create_fen_surface(
                            _elementIds[count],
                            new_surface['name'],
                            coordinate)

                        # get element and add it to the collector
                        try:
                            elm = boundary_element.Document.GetElement(_elementIds[count])
                            element_collector[room_count].append(elm)
                        except TypeError:
                            element_collector[room_count].append(_elementIds[count])

                        # add fenestration surface to base surface
                        objects.add_fenestration_to_surface(new_surface,
                                                            new_fen_surface)
                else:
                    # collect child elements for non-curtain wall systems
                    childelement_collector = window.get_child_elemenets(boundary_element)

                    if not childelement_collector:
                        objects.add_surface_to_room(new_room, new_surface)
                        continue

                    _coordinates = window.exctract_glazing_vertices(
                        boundary_element,
                        base_face_dyn,
                        opt
                    )

                    for count, coordinate in enumerate(_coordinates):

                        if not coordinate:
                            log.append("{} in {} has an opening with less than "
                                       "two coordinates. It has been removed!"
                                       .format(
                                           childelement_collector[count].Id,
                                           new_room['name']
                                       ))

                        # create honeybee surface - use element id as the name
                        new_fen_surface = objects.create_fen_surface(
                            childelement_collector[count].Id,
                            new_room['name'],
                            coordinate
                        )

                        # add fenestration surface to base honeybee surface
                        element_collector[room_count].append(
                            childelement_collector[count]
                        )
                        # add fenestration surface to base surface
                        objects.add_fenestration_to_surface(
                            new_surface, new_fen_surface)

                # add surface to dynosaur room
                objects.add_surface_to_room(new_room, new_surface)
                # clean up!
                boundary_element.Dispose()

        room_collector[room_count] = new_room

        # clean up!
        revit_room_spatial_data.Dispose()

    calculator.Dispose()
    # End Transaction
    # TransactionManager.Instance.TransactionTaskDone()
    return room_collector, element_collector, log
