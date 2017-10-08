"""Functions to collect a certain type of object from Revit document."""

import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilyInstance

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
# from RevitServices.Transactions import TransactionManager

# Add ToDSType method for curtain panels
clr.AddReference('RevitNodes')
import Revit
clr.ImportExtensions(Revit.Elements)


def collect_rooms():
    """Collect all the rooms in the current Revit document."""
    document = DocumentManager.Instance.CurrentDBDocument
    collector = FilteredElementCollector(document)
    collector.OfCategory(BuiltInCategory.OST_Rooms)
    room_iter = collector.GetElementIdIterator()
    room_iter.Reset()
    return tuple(document.GetElement(el_id) for el_id in room_iter)


def collect_spaces():
    """Collect all the spaces in the current Revit document."""
    document = DocumentManager.Instance.CurrentDBDocument
    collector = FilteredElementCollector(document)
    collector.OfCategory(BuiltInCategory.OST_MEPSpaces)
    room_iter = collector.GetElementIdIterator()
    room_iter.Reset()
    return tuple(document.GetElement(el_id) for el_id in room_iter)


def collect_curtain_panels():
    doc = DocumentManager.Instance.CurrentDBDocument

    collector = FilteredElementCollector(doc)
    collector.OfCategory(BuiltInCategory.OST_CurtainWallPanels)
    collector.OfClass(FamilyInstance)

    cw_element_collector = collector.GetElementIdIterator()
    cw_element_collector.Reset()

    cw_collector = (doc.GetElement(cw_id) for cw_id in cw_element_collector)
    return tuple(cw.ToDSType(True) for cw in cw_collector
                 if cw.Symbol.Family.Name == 'System Panel')
