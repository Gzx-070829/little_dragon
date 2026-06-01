import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCREENSIZE = (1200, 600)  # 窗口宽度和高度
FPS = 60  # 每秒帧数
# 统一的地面基准线：角色脚底、仙人掌底部和地面滚动图片都围绕这里对齐。
GROUND_Y = int(SCREENSIZE[1] * 0.86)


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
