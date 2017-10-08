"""Functions to deal with Revit Window elements."""
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import Solid

clr.AddReference("RevitNodes")
from Revit import GeometryConversion
# Import ToProtoType, ToRevitType geometry conversion extension methods
clr.ImportExtensions(GeometryConversion)


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
