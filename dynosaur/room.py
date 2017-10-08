"""Revit room functions."""
import util
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import Point, Surface

clr.AddReference("RevitNodes")
from Revit import GeometryConversion
# Import ToProtoType, ToRevitType geometry conversion extension methods
clr.ImportExtensions(GeometryConversion)

import sys
sys.path.append(r'C:\Program Files (x86)\IronPython 2.7\Lib')
import collections


def get_dynamo_room_faces(revit_room_geometry):
    rounding = 4
    try:
        room_faces_dyn = \
            tuple(face.ToProtoType()[0] for face in revit_room_geometry.Faces)
    except StandardError:
        scale = util.unit_conversion()
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
        xyz_unique = (list(collections.OrderedDict.fromkeys(pts)) for pts in points)

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
