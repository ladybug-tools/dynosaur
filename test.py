"""test dynosaur!"""
# add IronPython to sys.path
import sys
sys.path.append(r'C:\Program Files (x86)\IronPython 2.7\Lib')
sys.path.append(r'C:\Users\Mostapha\Documents\code\ladybug-tools\dynosaur')

import traceback


def extract_vertices(rooms):
    """extract vertices from the room for quick visualization."""
    vertices = []
    glz_vertices = []
    for room in rooms:
        for surface in room['surfaces']:
            vertices.append(surface['vertices'])
            if 'fen_surfaces' in surface:
                # add child surfaces
                for fen_surface in surface['fen_surfaces']:
                    ver = fen_surface['vertices']
                    try:
                        # curtain wall. This should be fixed in the code itself
                        ver[0][0]
                        glz_vertices.extend(ver)
                    except TypeError:
                        glz_vertices.append(ver)

    return vertices, glz_vertices


try:
    # import dynosaur
    # reload(dynosaur)
    # reload(dynosaur.revit)
    import dynosaur.revit as revitosaurus
    rooms = revitosaurus.collect_rooms()
    roomosaurus, elements = revitosaurus.analyze_rooms((rooms[2],))
    OUT = extract_vertices(roomosaurus)
except Exception as e:
    OUT = traceback.format_exc()
