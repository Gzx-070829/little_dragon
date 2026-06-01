import random
import pygame


class Cactus(pygame.sprite.Sprite):
    """仙人掌障碍物类"""

    def __init__(self, imagepaths, position=(1200, 595), sizes=None, **kwargs):
        """
        初始化仙人掌障碍物
        Args:
            imagepaths (list): 仙人掌图片路径列表
            position (tuple): 初始位置
            sizes (list): 不同类型仙人掌的尺寸
        """
        super().__init__()
        if sizes is None:
            sizes = [(200, 220), (180, 150)]

        self.images = []
        image = pygame.image.load(imagepaths[0]).convert_alpha()
        for i in range(4):
            self.images.append(pygame.transform.scale(image.subsurface((i * 349, 0), (341, 575)), sizes[0]))

        image = pygame.image.load(imagepaths[1]).convert_alpha()
        for i in range(2):
            self.images.append(pygame.transform.scale(image.subsurface((i * 329, 0), (329, 565)), sizes[1]))

        self.image = random.choice(self.images)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.bottom = position
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = -10

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

    def __init__(self, imagepath, position=(1200, 300), size=(138, 126), **kwargs):
        """
        初始化翼龙障碍物
        Args:
            imagepath (str): 翼龙图片路径
            position (tuple): 初始位置
            size (tuple): 翼龙尺寸
        """
        super().__init__()

        self.images = []
        image = pygame.image.load(imagepath).convert_alpha()
        for i in range(2):
            self.images.append(pygame.transform.scale(image.subsurface((i * 1900, 0), (1900, 1047)), size))

        self.image_idx = 0
        self.image = self.images[self.image_idx]
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.centery = position
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = -10
        self.refresh_rate = 10
        self.refresh_counter = 0

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
        self.image = self.images[self.image_idx]
        self.mask = pygame.mask.from_surface(self.image)
