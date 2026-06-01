import pygame

import core


def trim_surface(surface):
    """裁掉 Surface 四周的透明边距，保证贴地和碰撞区域更准确。"""
    bounds = surface.get_bounding_rect()
    if bounds.width == 0 or bounds.height == 0:
        return surface.copy()
    return surface.subsurface(bounds).copy()


def scale_to_height(surface, height):
    """按目标高度等比缩放 Surface。"""
    width, current_height = surface.get_size()
    if current_height == 0:
        return surface.copy()
    target_width = max(1, int(width * height / current_height))
    return pygame.transform.smoothscale(surface, (target_width, height))


class Dinosaur(pygame.sprite.Sprite):
    """恐龙玩家角色。"""

    def __init__(self, imagepaths, position=None, heights=(110, 78), **kwargs):
        """
        初始化恐龙角色
        Args:
            imagepaths (list): 恐龙图片路径列表 [正常状态, 下蹲状态]
            position (tuple): 恐龙初始位置，含义为 (left, bottom)
            heights (tuple): 恐龙图片的目标高度 [正常高度, 下蹲高度]
        """
        super().__init__()
        if position is None:
            position = (40, core.GROUND_Y)

        self.images = []
        image = pygame.image.load(imagepaths[0]).convert_alpha()
        for i in range(5):
            frame = image.subsurface((i * 270, 0), (270, 410))
            frame = trim_surface(frame)
            self.images.append(scale_to_height(frame, heights[0]))

        image = pygame.image.load(imagepaths[1]).convert_alpha()
        duck_frame = image.subsurface((0, 0), (2015, 1338))
        duck_frame = trim_surface(duck_frame)
        self.images.append(scale_to_height(duck_frame, heights[1]))

        self.image_idx = 0
        self.image = self.images[self.image_idx]
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.bottom = position
        self.mask = pygame.mask.from_surface(self.image)

        self.init_position = position
        self.refresh_rate = 5
        self.refresh_counter = 0
        self.speed = 18
        self.gravity = 0.7
        self.is_jumping = False
        self.is_ducking = False
        self.is_dead = False
        self.movement = [0, 0]

    def jump(self, sounds):
        """让恐龙跳跃。"""
        if not self.is_jumping and not self.is_dead and not self.is_ducking:
            sounds['jump'].play()
            self.is_jumping = True
            self.movement[1] = -self.speed

    def duck(self):
        """让恐龙下蹲。"""
        if not self.is_jumping and not self.is_dead:
            self.is_ducking = True

    def unduck(self):
        """取消下蹲状态。"""
        self.is_ducking = False

    def die(self, sounds):
        """播放死亡音效并标记死亡状态。"""
        if not self.is_dead:
            sounds['die'].play()
            self.is_dead = True

    def draw(self, screen):
        """在屏幕上绘制恐龙。"""
        screen.blit(self.image, self.rect)

    def loadImage(self):
        """加载当前帧的图片并更新碰撞遮罩。"""
        self.image = self.images[self.image_idx]
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        """更新恐龙跳跃、下蹲和跑步动画状态。"""
        if self.is_dead:
            self.image_idx = 4
            self.loadImage()
            return

        if self.is_jumping:
            self.movement[1] += self.gravity
            self.rect.y += self.movement[1]
            if self.rect.bottom >= self.init_position[1]:
                self.rect.bottom = self.init_position[1]
                self.is_jumping = False
                self.movement[1] = 0

        self.refresh_counter += 1
        if self.refresh_counter >= self.refresh_rate:
            self.refresh_counter = 0
            if self.is_ducking:
                self.image_idx = 5
            else:
                self.image_idx = (self.image_idx + 1) % 5
            self.loadImage()
