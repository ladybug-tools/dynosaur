"""dynosaur objects: room, surface and child surface."""
# TODO: change the objects to classes


def create_room(name):
    """Create a new room."""
    new_room = {
        'name': None,
        'surfaces': []
    }
    new_room['name'] = name
    return new_room


def add_surface_to_room(room, surface):
    """Add a surface to the room."""
    room['surfaces'].append(surface)
    return room


def add_surfaces_to_room(room, surfaces):
    """Add surfaces to the room."""
    room['surfaces'].extend(surfaces)
    return room


def change_room_name(room, new_name):
    """Change name of room."""
    room['name'] = new_name
    return room


# dynosaur surfaces
def create_surface(name, parent_id=None, vertices=None):
    """Create a new surface."""
    vertices = vertices or []
    new_surface = {
        'name': None,
        'vertices': [],
        'fen_surfaces': [],
        'parent_id': None
    }
    new_surface['name'] = name
    new_surface['parent_id'] = parent_id
    new_surface['vertices'] = vertices
    return new_surface


def create_fen_surface(name, parent_id=None, vertices=None):
    """Create a new fenestration surface."""
    vertices = vertices or []
    new_surface = {
        'name': None,
        'vertices': [],
        'parent_id': None
    }
    new_surface['name'] = name
    new_surface['parent_id'] = parent_id
    new_surface['vertices'] = vertices
    return new_surface


def add_fenestration_to_surface(surface, fenestration):
    """Add a fenestration surface to a surface."""
    surface['fen_surfaces'].append(fenestration)
    return surface


def add_fenestrations_to_surface(surface, fenestrations):
    """Add several fenestration surfaces to surface."""
    surface['fen_surfaces'].extend(fenestrations)
    return surface


def change_surface_name(surface, new_name):
    """Change name of surface."""
    surface['name'] = new_name
    return surface
