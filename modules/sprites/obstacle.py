import random
import pygame

import core


def trim_surface(surface):
    """裁掉透明边距，避免图片内容看起来悬浮并让 mask 更贴合。"""
    bounds = pygame.mask.from_surface(surface).get_bounding_rects()
    bounds = (
        surface.get_bounding_rect()
        if not bounds
        else bounds[0].unionall(bounds[1:])
    )
    if bounds.width == 0 or bounds.height == 0:
        return surface.copy()
    return surface.subsurface(bounds).copy()


def scale_to_height(surface, height):
    """按目标高度等比缩放 Surface。"""
    width, current_height = surface.get_size()
    if current_height == 0:
        return surface.copy()
    target_width = max(1, int(width * height / current_height))
    return pygame.transform.scale(surface, (target_width, height))


class Cactus(pygame.sprite.Sprite):
    """仙人掌障碍物类"""

    _IMAGE_CACHE = {}

    @classmethod
    def _get_images(cls, imagepaths, heights):
        cache_key = (tuple(imagepaths), tuple(heights))
        cached = cls._IMAGE_CACHE.get(cache_key)
        if cached is not None:
            return cached

        images = []
        image = pygame.image.load(imagepaths[0]).convert_alpha()
        for i in range(4):
            frame = image.subsurface((i * 349, 0), (341, 575))
            frame = trim_surface(frame)
            images.append(scale_to_height(frame, heights[0]))

        image = pygame.image.load(imagepaths[1]).convert_alpha()
        for i in range(2):
            frame = image.subsurface((i * 329, 0), (329, 565))
            frame = trim_surface(frame)
            images.append(scale_to_height(frame, heights[1]))

        cls._IMAGE_CACHE[cache_key] = images
        return images

    def __init__(self, imagepaths, position=None, heights=None, speed=10, **kwargs):
        """
        初始化仙人掌障碍物
        Args:
            imagepaths (list): 仙人掌图片路径列表 [大仙人掌, 小仙人掌]
            position (tuple): 初始位置，含义为 (left, bottom)
            heights (tuple): 不同类型仙人掌的目标高度 [大仙人掌, 小仙人掌]
            speed (int): 从右向左移动的速度
        """
        super().__init__()
        if position is None:
            position = (core.SCREENSIZE[0], core.GROUND_Y)
        if heights is None:
            heights = (118, 82)

        self.images = self._get_images(imagepaths, heights)
        self.image = random.choice(self.images)
        self.rect = self.image.get_rect()
        self.rect.left = position[0]
        self.rect.bottom = position[1] + core.CACTUS_GROUND_OFFSET
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = -abs(speed)
        self.counted = False

    def draw(self, screen):
        """绘制仙人掌到屏幕"""
        screen.blit(self.image, self.rect)

    def update(self):
        """更新仙人掌位置，移出屏幕后自动销毁。"""
        self.rect.x += self.speed
        if self.rect.right < 0:
            self.kill()


class Ptera(pygame.sprite.Sprite):
    """翼龙障碍物类"""

    _IMAGE_CACHE = {}

    @classmethod
    def _get_images(cls, imagepath, height):
        cache_key = (imagepath, height)
        cached = cls._IMAGE_CACHE.get(cache_key)
        if cached is not None:
            return cached

        images = []
        image = pygame.image.load(imagepath).convert_alpha()
        for i in range(2):
            frame = image.subsurface((i * 1900, 0), (1900, 1047))
            frame = trim_surface(frame)
            images.append(scale_to_height(frame, height))

        cls._IMAGE_CACHE[cache_key] = images
        return images

    def __init__(self, imagepath, position=None, height=70, speed=10, **kwargs):
        """
        初始化翼龙障碍物
        Args:
            imagepath (str): 翼龙图片路径
            position (tuple): 初始位置，含义为 (left, centery)
            height (int): 翼龙目标高度
            speed (int): 从右向左移动的速度
        """
        super().__init__()
        if position is None:
            position = (core.SCREENSIZE[0], core.GROUND_Y - 100)

        self.images = self._get_images(imagepath, height)
        self.image_idx = 0
        self.image = self.images[self.image_idx]
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.centery = position
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = -abs(speed)
        self.refresh_rate = 10
        self.refresh_counter = 0
        self.counted = False

    def draw(self, screen):
        """绘制翼龙到屏幕"""
        screen.blit(self.image, self.rect)

    def update(self):
        """更新翼龙位置和动画。"""
        self.rect.x += self.speed

        self.refresh_counter += 1
        if self.refresh_counter >= self.refresh_rate:
            self.refresh_counter = 0
            self.image_idx = 1 - self.image_idx
            self.loadImage()

        if self.rect.right < 0:
            self.kill()

    def loadImage(self):
        center = self.rect.center
        self.image = self.images[self.image_idx]
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)
