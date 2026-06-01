import os

SCREENSIZE = (1200, 600)  # 窗口宽度和高度
FPS = 60  # 每秒帧数

# 音频资源路径
AUDIO_PATHS = {
    'die': os.path.join(os.getcwd(), 'resources/audios/die.wav'),
    'jump': os.path.join(os.getcwd(), 'resources/audios/jump.wav'),
    'point': os.path.join(os.getcwd(), 'resources/audios/point.mp3'),
    'button': os.path.join(os.getcwd(), 'resources/audios/button.mp3')
}

# 图片资源路径
IMAGE_PATHS = {
    'cacti': [
        os.path.join(os.getcwd(), 'resources/images/cacti-big.png'),
        os.path.join(os.getcwd(), 'resources/images/cacti-small.png')
    ],
    'cloud': os.path.join(os.getcwd(), 'resources/images/cloud.png'),
    'dino': [
        os.path.join(os.getcwd(), 'resources/images/dino1.png'),
        os.path.join(os.getcwd(), 'resources/images/dino2.png')
    ],
    'ground': os.path.join(os.getcwd(), 'resources/images/ground-4x.png'),
    'ptera': os.path.join(os.getcwd(), 'resources/images/ptera.png'),
    'replay': os.path.join(os.getcwd(), 'resources/images/replay.png')
}
# 字体资源路径
FONT_PATHS = {
    'joystix': os.path.join(os.getcwd(), 'resources/fonts/joystix-monospace-2.ttf')
}

# 颜色定义
BACKGROUND_COLOR = (235, 235, 235)  # 浅灰色背景
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

