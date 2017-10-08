"""Functions to deal with Revit curtain wall and curtain panel elements."""
import clr
clr.AddReference("RevitNodes")
from Revit import GeometryConversion
# Import ToProtoType, ToRevitType geometry conversion extension methods
clr.ImportExtensions(GeometryConversion)


def extract_curtain_panel_vertices(curtain_panels, base_face, tol=None):
    """Return lists of lists of vertices for a panel grid."""
    tol = tol or 50
    outer_faces = tuple(
        sorted(s.Faces, key=lambda x: x.Area, reverse=True)[0]
        for s in curtain_panels if s and s.Faces.Length != 0)
    # filtered panels
    panels = tuple(p for p in curtain_panels if p and p.Faces.Length != 0)
    # find center points
    center_pts = tuple(face.PointAtParameter(0.5, 0.5) for face in outer_faces)

    pattern = tuple(base_face.DistanceTo(pt) < tol for pt in center_pts)

    panel_element_ids = tuple(panel for count, panel in enumerate(panels)
                              if pattern[count])
    vertices = ((base_face.ClosestPointTo(v.PointGeometry) for v in face.Vertices)
                for count, face in enumerate(outer_faces)
                if pattern[count])
    return panel_element_ids, vertices


def extract_panels_vertices(host_element, base_face, opt):
    """Return lists of lists of vertices for a panel grid."""
    if not host_element.CurtainGrid:
        return (), ()
    opt.ComputeReferences = True
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
