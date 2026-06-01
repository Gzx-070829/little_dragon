#### 代码框架

import pygame


class Dinosaur(pygame.sprite.Sprite):
    """恐龙角色类"""

    def __init__(self, imagepaths, position=(40, 565), size=[(100, 110), (110, 70)], **kwargs):
        """        初始化恐龙角色
        Args:
            imagepaths (list): 恐龙图片路径列表 [正常状态, 下蹲状态]
            position (tuple): 恐龙在屏幕上的初始位置
            size (list): 恐龙图片的缩放尺寸 [正常尺寸, 下蹲尺寸]
        """
        pygame.sprite.Sprite.__init__(self)
        super().__init__()

        # 加载恐龙的所有动画帧图片
        # # 初始化：images 一定是列表！
        # self.images = []

        # # 循环加载恐龙动画帧（正确代码）
        # for path in imagepaths:
        #     img = pygame.image.load(path).convert_alpha()
        #     img = pygame.transform.scale(img, (50, 50))
        #     self.images.append(img)
        #
        # # 然后才能取第一帧
        # self.image = self.images[0]
        # self.rect = self.image.get_rect()
        self.images = []
        # 提示：正常状态有5帧动画，下蹲状态有2帧动画
        image = pygame.image.load(imagepaths[0])
        for i in range(5):
            self.images.append(pygame.transform.scale(image.subsurface((i * 270, 0), (270, 410)), size[0]))
        image = pygame.image.load(imagepaths[1])
        for i in range(1):
            self.images.append(pygame.transform.scale(image.subsurface((i * 2015, 0), (2015, 1338)), size[1]))

        # TODO: 设置恐龙的初始图片和位置
        self.image_idx = 0
        self.image = self.images[self.image_idx]
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.bottom = position
        self.mask = pygame.mask.from_surface(self.image)

        # 恐龙的物理属性
        self.init_position = position
        self.refresh_rate = 5  # 动画刷新频率
        self.refresh_counter = 0
        self.speed = 18  # 跳跃初始速度
        self.gravity = 0.7  # 重力加速度
        self.is_jumping = False
        self.is_ducking = False
        self.is_dead = False
        self.movement = [0, 0]  # [水平移动, 垂直移动]

    def jump(self, sounds):
        """
        恐龙跳跃方法
        Args:
            sounds (dict): 音效字典
        """
        # TODO: 实现跳跃逻辑# 提示：检查是否已经在跳跃或死亡状态，播放跳跃音效，设置垂直移动速度
        if not self.is_jumping and not self.is_dead and not self.is_ducking:
            sounds['jump'].play()  # 播放跳跃音效
            self.is_jumping = True  # 标记跳跃中
            self.movement[1] = -self.speed  # 向上跳

    def duck(self):
        """恐龙下蹲方法"""
        # TODO: 实现下蹲逻辑# 提示：检查是否在跳跃或死亡状态，设置下蹲标志
        if not self.is_jumping and not self.is_dead:
            self.is_ducking = True

    def unduck(self):
        """恐龙停止下蹲方法"""
        # TODO: 取消下蹲状态
        self.is_ducking = False


    def die(self, sounds):
        """
        恐龙死亡方法
        Args:
            sounds (dict): 音效字典
        """
        # TODO: 实现死亡逻辑
        # 提示：播放死亡音效，设置死亡标志
        sounds['die'].play()  # 播放死亡音效
        self.is_dead = True

    def draw(self, screen):
        """
        在屏幕上绘制恐龙

        Args:
            screen: Pygame屏幕对象
        """
        # TODO: 将恐龙图片绘制到屏幕上
        screen.blit(self.image, self.rect)

    def loadImage(self):
        """加载当前帧的图片并更新碰撞遮罩"""
        # TODO: 根据当前图片索引加载图片，更新rect和mask
        self.image = self.images[self.image_idx]
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
        self.mask = pygame.mask.from_surface(self.image)


    def update(self):
        """更新恐龙状态（每帧调用）"""
        # TODO: 实现恐龙状态更新逻辑
        # 包括：死亡状态、跳跃物理、下蹲动画、正常跑步动画
        if self.is_dead:
            self.image_idx = 4
            self.loadImage()
            return

            # 重力下落
        if self.is_jumping:
            self.movement[1] += self.gravity
            self.rect.y += self.movement[1]
            # 落地
            if self.rect.bottom >= self.init_position[1]:
                self.rect.bottom = self.init_position[1]
                self.is_jumping = False
                self.movement[1] = 0

            # 动画切换
        self.refresh_counter += 1
        if self.refresh_counter >= self.refresh_rate:
            self.refresh_counter = 0

            # 下蹲动画（5、6帧）
            if self.is_ducking:
                self.image_idx = 5 if self.image_idx == 5 else 5

            # 正常跑步（0-4帧）
            else:
                self.image_idx = (self.image_idx + 1) % 5

            self.loadImage()

