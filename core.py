import os

import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGICAL_SIZE = (1200, 600)
WINDOW_SIZE = LOGICAL_SIZE
SCREENSIZE = LOGICAL_SIZE  # 游戏内部始终使用固定逻辑分辨率。
FPS = 60  # 每秒帧数
USE_SMOOTH_SCALE = False  # 默认优先流畅度；需要更平滑缩放时可改为 True。
# 统一的地面表面基准线：角色脚底、仙人掌底部、金币和翼龙高度都围绕这里对齐。
GROUND_Y = int(LOGICAL_SIZE[1] * 0.86)
# 仙人掌在裁掉透明边距后轻微下沉，确保视觉底部彻底贴住地面表面。
CACTUS_GROUND_OFFSET = 4
# 难度速度范围。Slow Start 升级会把起始速度降到 8。
BASE_GAME_SPEED = 10
SLOW_START_GAME_SPEED = 8
MAX_GAME_SPEED = 24


CHINESE_FONT_NAMES = (
    'Noto Sans CJK SC',
    'Noto Sans CJK',
    'WenQuanYi Micro Hei',
    'Microsoft YaHei',
    'SimHei',
    'Source Han Sans SC',
    'Arial Unicode MS',
)


_FONT_CACHE = {}
_SCALE_CACHE = {}


def get_font(size):
    """Return and cache a font that can render Chinese text when available."""
    size = int(size)
    cached_font = _FONT_CACHE.get(size)
    if cached_font is not None:
        return cached_font

    for font_name in CHINESE_FONT_NAMES:
        try:
            matched_font = pygame.font.match_font(font_name)
            if matched_font:
                font = pygame.font.Font(matched_font, size)
                _FONT_CACHE[size] = font
                return font
        except Exception:
            continue
    font = pygame.font.Font(None, size)
    _FONT_CACHE[size] = font
    return font


def set_screen_size(size):
    """Keep compatibility with older callers without changing logical layout."""
    return LOGICAL_SIZE


def resize_screen(size):
    """Resize the real window while preserving fixed in-game coordinates."""
    width, height = size
    return pygame.display.set_mode(
        (max(1, int(width)), max(1, int(height))),
        pygame.RESIZABLE,
    )


def _scaled_layout(window_size, logical_size):
    """Return cached size and letterbox offset for fixed logical scaling."""
    cache_key = (window_size, logical_size)
    cached = _SCALE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    window_w, window_h = window_size
    logical_w, logical_h = logical_size
    scale = min(window_w / logical_w, window_h / logical_h)
    scaled_w = max(1, int(logical_w * scale))
    scaled_h = max(1, int(logical_h * scale))
    offset_x = (window_w - scaled_w) // 2
    offset_y = (window_h - scaled_h) // 2
    layout = ((scaled_w, scaled_h), (offset_x, offset_y), scale)
    if len(_SCALE_CACHE) > 32:
        _SCALE_CACHE.clear()
    _SCALE_CACHE[cache_key] = layout
    return layout


def blit_scaled(game_surface, screen):
    """Scale the fixed logical game surface into the real window with letterboxing."""
    scaled_size, offset, _ = _scaled_layout(screen.get_size(), game_surface.get_size())
    if USE_SMOOTH_SCALE:
        scaled_surface = pygame.transform.smoothscale(game_surface, scaled_size)
    else:
        scaled_surface = pygame.transform.scale(game_surface, scaled_size)

    screen.fill((0, 0, 0))
    screen.blit(scaled_surface, offset)
    pygame.display.flip()


def screen_to_game_pos(pos, screen, game_surface):
    """Map a real-window mouse position back to fixed logical game coordinates."""
    window_w, window_h = screen.get_size()
    logical_w, logical_h = game_surface.get_size()

    (scaled_w, scaled_h), (offset_x, offset_y), scale = _scaled_layout(
        (window_w, window_h),
        (logical_w, logical_h),
    )

    x, y = pos
    if (
        x < offset_x
        or y < offset_y
        or x > offset_x + scaled_w
        or y > offset_y + scaled_h
    ):
        return None

    game_x = int((x - offset_x) / scale)
    game_y = int((y - offset_y) / scale)

    return game_x, game_y


def resource_path(*parts):
    """Return an absolute path inside the project resources directory."""
    return os.path.join(BASE_DIR, 'resources', *parts)

# 音频资源路径
AUDIO_PATHS = {
    'die': resource_path('audios', 'die.wav'),
    'jump': resource_path('audios', 'jump.wav'),
    'point': resource_path('audios', 'point.mp3'),
    'button': resource_path('audios', 'button.mp3')
}

# 图片资源路径
IMAGE_PATHS = {
    'cacti': [
        resource_path('images', 'cacti-big.png'),
        resource_path('images', 'cacti-small.png')
    ],
    'cloud': resource_path('images', 'cloud.png'),
    'dino': [
        resource_path('images', 'dino1.png'),
        resource_path('images', 'dino2.png')
    ],
    'ground': resource_path('images', 'ground-4x.png'),
    'ptera': resource_path('images', 'ptera.png'),
    'replay': resource_path('images', 'replay.png'),
    'custom_icecream_coin': resource_path('images', 'custom', 'icecream_coin.jpg'),
    'custom_text_cloud': resource_path('images', 'custom', 'text_cloud.jpg'),
    'custom_runner_sheet': resource_path('images', 'custom', 'runner_sheet.jpg')
}

# 字体资源路径
FONT_PATHS = {
    'joystix': resource_path('fonts', 'joystix-monospace-2.ttf')
}

# 颜色定义
BACKGROUND_COLOR = (235, 235, 235)  # 浅灰色背景
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
