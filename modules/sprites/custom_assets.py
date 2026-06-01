from collections import deque

import pygame

import core


def _matches_background(color, bg, tolerance):
    r, g, b = color[:3]
    if bg == 'white':
        return r >= 255 - tolerance and g >= 255 - tolerance and b >= 255 - tolerance
    if bg == 'black':
        return r <= tolerance and g <= tolerance and b <= tolerance
    return False


def remove_edge_background(surface, bg='white', tolerance=30):
    """Remove only edge-connected near-white/near-black pixels from a surface."""
    source = surface.convert_alpha()
    width, height = source.get_size()
    if width <= 0 or height <= 0:
        return source

    visited = set()
    queue = deque()

    def add_if_bg(x, y):
        if (x, y) in visited:
            return
        visited.add((x, y))
        if _matches_background(source.get_at((x, y)), bg, tolerance):
            queue.append((x, y))

    for x in range(width):
        add_if_bg(x, 0)
        add_if_bg(x, height - 1)
    for y in range(height):
        add_if_bg(0, y)
        add_if_bg(width - 1, y)

    while queue:
        x, y = queue.popleft()
        source.set_at((x, y), (0, 0, 0, 0))
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                visited.add((nx, ny))
                if _matches_background(source.get_at((nx, ny)), bg, tolerance):
                    queue.append((nx, ny))

    return source


def trim_transparent_surface(surface):
    """Crop transparent borders from a pygame Surface."""
    bounds = surface.get_bounding_rect()
    if bounds.width == 0 or bounds.height == 0:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    return surface.subsurface(bounds).copy()


def scale_to_fit(surface, max_width=None, max_height=None, target_height=None):
    """Scale a surface once while preserving aspect ratio."""
    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return surface.copy()
    if target_height is not None:
        scale = target_height / height
    else:
        scales = []
        if max_width is not None:
            scales.append(max_width / width)
        if max_height is not None:
            scales.append(max_height / height)
        scale = min(scales) if scales else 1
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    if new_size == (width, height):
        return surface.copy()
    return pygame.transform.smoothscale(surface, new_size)


def load_processed_custom_image(path, bg='white', tolerance=30):
    image = pygame.image.load(path).convert_alpha()
    image = remove_edge_background(image, bg=bg, tolerance=tolerance)
    return trim_transparent_surface(image)
