import pygame


class Dinosaur(pygame.sprite.Sprite):
    """恐龙玩家角色。"""

    def __init__(self, imagepaths, position=(40, 550), size=((80, 100), (120, 100)), **kwargs):
        """
        初始化恐龙角色
        Args:
            imagepaths (list): 恐龙图片路径列表 [正常状态, 下蹲状态]
            position (tuple): 恐龙在屏幕上的初始位置
            size (list): 恐龙图片的缩放尺寸 [正常尺寸, 下蹲尺寸]
        """
        super().__init__()

        self.images = []
        image = pygame.image.load(imagepaths[0]).convert_alpha()
        for i in range(5):
            self.images.append(pygame.transform.scale(image.subsurface((i * 270, 0), (270, 410)), size[0]))
        image = pygame.image.load(imagepaths[1]).convert_alpha()
        self.images.append(pygame.transform.scale(image.subsurface((0, 0), (2015, 1338)), size[1]))

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
