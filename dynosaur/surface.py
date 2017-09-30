"""dynosaur room face."""

_surface = {
    'name': None,
    'vertices': [],
    'fen_surfaces': [],
    'parent_id': None
}

_fensurface = {
    'name': None,
    'vertices': [],
    'parent_id': None
}


def create_surface(name, parent_id=None, vertices=None):
    """Create a new surface."""
    vertices = vertices or []
    new_surface = dict(_surface)
    new_surface['name'] = name
    new_surface['parent_id'] = parent_id
    new_surface['vertices'] = vertices
    return new_surface


def create_fen_surface(name, parent_id=None, vertices=None):
    """Create a new fenestration surface."""
    vertices = vertices or []
    new_surface = dict(_fensurface)
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
