"""dynosaur room."""

_room = {
    'name': None,
    'surfaces': []
}


def create_room(name):
    """Create a new room."""
    new_room = dict(_room)
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
