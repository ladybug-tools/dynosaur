"""Utilities."""
import uuid
import clr
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import UnitUtils, UnitType, SpatialElementBoundaryLocation


def unit_conversion():
    """Convert Revit units to Dynamo Units."""
    doc = DocumentManager.Instance.CurrentDBDocument
    doc_units = doc.GetUnits()
    length_unit = doc_units.GetFormatOptions(UnitType.UT_Length).DisplayUnits

    return UnitUtils.ConvertFromInternalUnits(1.0, length_unit)


def create_uuid():
    """Return a random uuid."""
    return str(uuid.uuid4())


def get_internal_elements(elements):
    """Get internal element from dynamo objects.

    This is similar to UnwrapElement in dynamo but will work fine outside dynamo.
    """
    if not elements:
        return

    if hasattr(elements, '__iter__'):
        return (get_internal_elements(x) for x in elements)
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
