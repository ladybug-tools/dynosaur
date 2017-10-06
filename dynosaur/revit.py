"""Collection of functions for Revit."""
import room
import surface

import uuid

import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector, \
    BuiltInCategory, Options, Solid, UnitUtils

# objects for spatial calculation
from Autodesk.Revit.DB import SpatialElementGeometryCalculator, \
    SpatialElementBoundaryOptions, SpatialElementBoundaryLocation

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from Autodesk.Revit.DB import UnitType, DisplayUnitType

clr.AddReference("RevitNodes")
from Revit import GeometryConversion
# Import ToProtoType, ToRevitType geometry conversion extension methods
clr.ImportExtensions(GeometryConversion)

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import Point, Surface

import sys
sys.path.append(r'C:\Program Files (x86)\IronPython 2.7\Lib')
from collections import OrderedDict


def unit_conversion():
    """Convert Revit units to Dynamo Units."""
    doc = DocumentManager.Instance.CurrentDBDocument
    doc_units = doc.GetUnits()
    length_unit = doc_units.GetFormatOptions(UnitType.UT_Length).DisplayUnits

    return 1.0 / UnitUtils.ConvertToInternalUnits(1.0, length_unit)


def collect_rooms(document=None):
    """Collect all the rooms in the current Revit document."""
    if not document:
        document = DocumentManager.Instance.CurrentDBDocument
    collector = FilteredElementCollector(document)
    collector.OfCategory(BuiltInCategory.OST_Rooms)
    room_iter = collector.GetElementIdIterator()
    room_iter.Reset()
    return tuple(document.GetElement(el_id) for el_id in room_iter)


def collect_spaces(document=None):
    """Collect all the spaces in the current Revit document."""
    if not document:
        document = DocumentManager.Instance.CurrentDBDocument
    collector = FilteredElementCollector(document)
    collector.OfCategory(BuiltInCategory.OST_MEPSpaces)
    room_iter = collector.GetElementIdIterator()
    room_iter.Reset()
    return tuple(document.GetElement(el_id) for el_id in room_iter)


def get_child_elemenets(host_element, add_rect_openings=True, include_shadows=False,
                        include_embedded_walls=True,
                        include_shared_embedded_inserts=True):
    """Get child elemsts for a Revit element."""
    try:
        ids = host_element.FindInserts(add_rect_openings,
                                       include_shadows,
                                       include_embedded_walls,
                                       include_shared_embedded_inserts)
    except AttributeError:
        # host element is not a wall, roof, etc. It's something like a column
        return ()

    return tuple(host_element.Document.GetElement(i) for i in ids)


def extract_panels_vertices(host_element, base_face, opt):
    """Return lists of lists of vertices for a panel grid."""
    if not host_element.CurtainGrid:
        return (), ()

    _panelElementIds = []
    _panelVertices = []
    panel_ids = host_element.CurtainGrid.GetPanelIds()
    for panel_id in panel_ids:

        panel_el = host_element.Document.GetElement(panel_id)
        geometries = panel_el.get_Geometry(opt)
        # From here solids are dynamo objects
        solids = tuple(p.ToProtoType()
                       for geometry in geometries
                       for p in geometry.GetInstanceGeometry())

        if panel_el.Name == 'Curtain Wall Dbl Glass':
            # remove handle geometry
            solids = solids[2:]

        outer_faces = tuple(
            sorted(s.Faces, key=lambda x: x.SurfaceGeometry().Area, reverse=True)[0]
            for s in solids if s and s.Faces.Length != 0)

        vertices = tuple(
            tuple(ver.PointGeometry for ver in outer_face.Vertices)
            for outer_face in outer_faces
        )

        coordinates = tuple(
            (base_face.ClosestPointTo(ver) for ver in ver_group)
            for ver_group in vertices
        )

        for coords in coordinates:
            _panelElementIds.append(panel_id)
            _panelVertices.append(coords)

        # cleaning up
        (solid.Dispose() for solid in solids)

    return _panelElementIds, _panelVertices


def exctract_glazing_vertices(host_element, base_face, opt):
    """Return glazing vertices for a window family instance.

    I was hoping that revit supports a cleaner way for doing this but for now
    I calculate the bounding box and find the face that it's vertices are coplanar
    with the host face.
    """
    # get 3d faces for the geometry
    # TODO: Take all the vertices for daylight modeling
    faces = (clr.Convert(obj, Solid).Faces
             for obj in host_element.get_Geometry(opt))

    _outerFace = next(faces)[0].ToProtoType()[0]

    openings = (
        tuple(edge.StartVertex.PointGeometry for edge in loop.CoEdges)
        for face in _outerFace.Faces
        for loop in face.Loops[:-1]
    )

    coordinates = (
        tuple(
            tuple(base_face.ClosestPointTo(pt) for pt in opening)
            for opening in openings
        ))

    # cleaning up
    (pt.Dispose() for opening in openings for pt in opening)
    (face.Dispose() for faceGroup in faces for face in faceGroup)

    filtered_coordinates = tuple(coorgroup
                                 for coorgroup in coordinates
                                 if len(set(coorgroup)) > 2)

    return filtered_coordinates


def create_uuid():
    """Return a random uuid."""
    return str(uuid.uuid4())


def _get_internalelement_collector(elements):
    """Get internal element from dynamo objects.

    This is similar to UnwrapElement in dynamo but will work fine outside dynamo.
    """
    if not elements:
        return

    if hasattr(elements, '__iter__'):
        return (_get_internalelement_collector(x) for x in elements)
    elif hasattr(elements, 'InternalElement'):
        return elements.InternalElement
    else:
        return elements


def get_boundary_location(index=1):
    """Get SpatialElementBoundaryLocation.

    0 > Finish: Spatial element finish face.
    1 > Center: Spatial element centerline.
    """
    index = index or index % 2
    if index == 0:
        return SpatialElementBoundaryLocation.Finish
    else:
        return SpatialElementBoundaryLocation.Center


def get_parameters(el, parameter):
    """Get the list of available parameter for a revit element."""
    return tuple(p.Definition.Name for p in el.Parameters)


def get_parameter(el, parameter):
    """Get a parameter from a revit element."""
    return tuple(p.AsValueString() for p in el.Parameters
                 if p.Definition.Name == parameter)[0]


def get_dynamo_room_faces(revit_room_geometry):
    rounding = 4
    try:
        room_faces_dyn = \
            tuple(face.ToProtoType()[0] for face in revit_room_geometry.Faces)
    except StandardError:
        scale = unit_conversion()
        # try to recreate the faces from the edges
        loops = tuple(loop for face in revit_room_geometry.Faces
                      for loop in face.EdgeLoops)

        # collect all the start and end points
        start_ends = (((e.Evaluate(1), e.Evaluate(0)) if count == 0 else
                       (e.Evaluate(0), e.Evaluate(1))
                       for count, e in enumerate(loop)) for loop in loops)

        # round the values
        points = ((
            (round(pt.X, rounding), round(pt.Y, rounding), round(pt.Z, rounding))
            for edge in loop for pt in edge)
            for loop in start_ends)

        # remove duplicated points
        xyz_unique = (list(OrderedDict.fromkeys(pts)) for pts in points)

        room_faces_dyn = []
        for pgroup in xyz_unique:
            try:
                face = Surface.ByPerimeterPoints(Point.ByCoordinates(*p).Scale(scale)
                                                 for p in pgroup)
            except StandardError:
                # changing the order was not needed for this face
                pgroup[0], pgroup[1] = pgroup[1], pgroup[0]
                face = Surface.ByPerimeterPoints(Point.ByCoordinates(*p).Scale(scale)
                                                 for p in pgroup)

            room_faces_dyn.append(face)

    return room_faces_dyn


def analyze_rooms(rooms, boundary_location=1):
    """Convert revit rooms to dynosaur rooms.

    This script will only work from inside Dynamo nodes. for a similar script
    forRrevit check this link for more details:
    https://github.com/jeremytammik/SpatialElementGeometryCalculator/
        blob/master/SpatialElementGeometryCalculator/Command.cs
    """
    # unwrap room elements
    # this is not the right way of logging in python and probably any other language
    log = []
    rooms = tuple(_get_internalelement_collector(rooms))
    if not rooms:
        return []

    # create a spatial element calculator to calculate room data
    doc = rooms[0].Document
    options = SpatialElementBoundaryOptions()
    options.SpatialElementBoundaryLocation = get_boundary_location(boundary_location)
    calculator = SpatialElementGeometryCalculator(doc, options)

    opt = Options()
    element_collector = []
    room_collector = range(len(rooms))
    # surface_collector = {}  # collect hbSurfaces so I can set adjucent surfaces
    for room_count, revit_room in enumerate(rooms):
        # initiate zone based on room id
        element_collector.append([])
        new_room = room.create_room(revit_room.Id)

        # calculate spatial data for revit room
        revit_room_spatial_data = calculator.CalculateSpatialElementGeometry(revit_room)

        # get the geometry of the room
        revit_room_geometry = revit_room_spatial_data.GetGeometry()

        # Cast revit room faces to dynamo geometry using ToProtoType method
        room_faces_dyn = get_dynamo_room_faces(revit_room_geometry)

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

                new_surface = surface.create_surface(
                    "%s_%s" % (new_room['name'], create_uuid()),
                    new_room['name'],
                    face_vertices
                )

                room.add_surface_to_room(new_room, new_surface)
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

                new_surface = surface.create_surface(
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
                if get_parameter(boundary_element, 'Family') == 'Curtain Wall':
                    # get cooredinates and element ids for this curtain wall.

                    _elementIds, _coordinates = extract_panels_vertices(
                        boundary_element, base_face_dyn, opt)

                    for count, coordinate in enumerate(_coordinates):
                        if not coordinate:
                            log.append("{} has an opening with less than "
                                       "two coordinates. It has been removed!"
                                       .format(_elementIds[count]))
                            continue

                        # create honeybee surface - use element id as the name
                        new_fen_surface = surface.create_fen_surface(
                            _elementIds[count],
                            new_surface['name'],
                            coordinate)

                        # get element and add it to the collector
                        elm = boundary_element.Document.GetElement(_elementIds[count])
                        element_collector[room_count].append(elm)

                        # add fenestration surface to base surface
                        surface.add_fenestration_to_surface(new_surface, new_fen_surface)
                else:
                    # collect child elements for non-curtain wall systems
                    childelement_collector = get_child_elemenets(boundary_element)

                    if not childelement_collector:
                        room.add_surface_to_room(new_room, new_surface)
                        continue

                    _coordinates = exctract_glazing_vertices(
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
                        new_fen_surface = surface.create_fen_surface(
                            childelement_collector[count].Id,
                            new_room['name'],
                            coordinate
                        )

                        # add fenestration surface to base honeybee surface
                        element_collector[room_count].append(
                            childelement_collector[count]
                        )
                        # add fenestration surface to base surface
                        surface.add_fenestration_to_surface(new_surface,
                                                            new_fen_surface)

                # add surface to dynosaur room
                room.add_surface_to_room(new_room, new_surface)
                # clean up!
                boundary_element.Dispose()

        room_collector[room_count] = new_room

        # clean up!
        revit_room_spatial_data.Dispose()

    calculator.Dispose()
    return room_collector, element_collector, log
