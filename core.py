import os

import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGICAL_SIZE = (1200, 600)
WINDOW_SIZE = LOGICAL_SIZE
SCREENSIZE = LOGICAL_SIZE  # 游戏内部始终使用固定逻辑分辨率。
FPS = 60  # 每秒帧数
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


def get_font(size):
    """Return a font that can render Chinese text when the system provides one."""
    for font_name in CHINESE_FONT_NAMES:
        try:
            matched_font = pygame.font.match_font(font_name)
            if matched_font:
                return pygame.font.Font(matched_font, size)
        except Exception:
            continue
    return pygame.font.Font(None, size)


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


def blit_scaled(game_surface, screen):
    """Scale the fixed logical game surface into the real window with letterboxing."""
    window_w, window_h = screen.get_size()
    logical_w, logical_h = game_surface.get_size()

    scale = min(window_w / logical_w, window_h / logical_h)
    scaled_w = max(1, int(logical_w * scale))
    scaled_h = max(1, int(logical_h * scale))

    scaled_surface = pygame.transform.smoothscale(game_surface, (scaled_w, scaled_h))

    offset_x = (window_w - scaled_w) // 2
    offset_y = (window_h - scaled_h) // 2

    screen.fill((0, 0, 0))
    screen.blit(scaled_surface, (offset_x, offset_y))
    pygame.display.flip()


def screen_to_game_pos(pos, screen, game_surface):
    """Map a real-window mouse position back to fixed logical game coordinates."""
    window_w, window_h = screen.get_size()
    logical_w, logical_h = game_surface.get_size()

    scale = min(window_w / logical_w, window_h / logical_h)
    scaled_w = int(logical_w * scale)
    scaled_h = int(logical_h * scale)

    offset_x = (window_w - scaled_w) // 2
    offset_y = (window_h - scaled_h) // 2

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
    'replay': resource_path('images', 'replay.png')
}

# 字体资源路径
FONT_PATHS = {
    'joystix': resource_path('fonts', 'joystix-monospace-2.ttf')
}

# 颜色定义
BACKGROUND_COLOR = (235, 235, 235)  # 浅灰色背景
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
