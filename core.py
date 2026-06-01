import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SCREENSIZE = (1200, 600)
SCREENSIZE = DEFAULT_SCREENSIZE  # 当前窗口宽度和高度，初始化显示模式后会更新。
FULLSCREEN = True
FPS = 60  # 每秒帧数
# 统一的地面表面基准线：角色脚底、仙人掌底部、金币和翼龙高度都围绕这里对齐。
GROUND_Y = int(SCREENSIZE[1] * 0.82)
# 仙人掌在裁掉透明边距后轻微下沉，确保视觉底部彻底贴住地面表面。
CACTUS_GROUND_OFFSET = 4
# 难度速度范围。Slow Start 升级会把起始速度降到 8。
BASE_GAME_SPEED = 10
SLOW_START_GAME_SPEED = 8
MAX_GAME_SPEED = 24



def set_screen_size(size):
    """Update screen-dependent layout constants after pygame creates the window."""
    global SCREENSIZE, GROUND_Y
    width, height = size
    SCREENSIZE = (int(width), int(height))
    GROUND_Y = int(SCREENSIZE[1] * 0.82)


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
