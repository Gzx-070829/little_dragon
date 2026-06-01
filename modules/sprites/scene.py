import pygame
import core


class Ground(pygame.sprite.Sprite):
    """地面类（无限滚动）"""

    def __init__(self, imagepath, position=(0, core.GROUND_Y), **kwargs):
        super().__init__()
        # 加载地面图片
        self.image = pygame.image.load(imagepath).convert_alpha()

        sw, sh = core.SCREENSIZE

        # 缩放到屏幕宽度，并让地面图片上沿对齐统一的 GROUND_Y 地面表面。
        self.image = pygame.transform.scale(self.image, (sw, 70))
        self.rect = self.image.get_rect()
        self.rect.topleft = position

        # 创建第二个地面实现无缝滚动
        self.rect2 = self.image.get_rect()
        self.rect2.left = self.rect.right  # 放在第一个地面右边紧挨着
        self.rect2.bottom = self.rect.bottom

        self.speed = -10  # 地面向左移动，主循环会同步为当前 game_speed

    def update(self):
        # 两个地面同时向左移动
        self.rect.x += self.speed
        self.rect2.x += self.speed

        # 当第一个地面完全移出屏幕左侧，立刻放到第二个地面右边
        if self.rect.right < 0:
            self.rect.left = self.rect2.right

        # 当第二个地面完全移出屏幕左侧，立刻放到第一个地面右边
        if self.rect2.right < 0:
            self.rect2.left = self.rect.right

    def draw(self, screen):
        # 绘制两个地面
        screen.blit(self.image, self.rect)
        screen.blit(self.image, self.rect2)


class Cloud(pygame.sprite.Sprite):
    """云朵类"""

    def __init__(self, imagepath, position, **kwargs):
        super().__init__()
        # 加载并缩放云朵图片
        self.image = pygame.image.load(imagepath).convert_alpha()
        self.image = pygame.transform.scale(self.image, (80, 40))  # 合适大小
        self.rect = self.image.get_rect()
        self.rect.topleft = position

        self.speed = -1  # 比地面慢，营造远景效果

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        # 向左缓慢移动
        self.rect.x += self.speed
        # 出屏幕自动销毁
        if self.rect.right < 0:
            self.kill()


class Coin(pygame.sprite.Sprite):
    """像素风金币精灵，不依赖额外图片资源。"""

    def __init__(self, position, speed=10, radius=14, **kwargs):
        """
        Args:
            position (tuple): 金币初始中心点坐标 (centerx, centery)
            speed (int): 从右向左移动的速度，通常与 game_speed 一致
            radius (int): 金币半径
        """
        super().__init__()
        size = radius * 2 + 4
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)

        # 用简单图形画出金币，避免新增或替换图片资源。
        pygame.draw.circle(self.image, (178, 111, 0), center, radius + 1)
        pygame.draw.circle(self.image, (255, 205, 55), center, radius)
        pygame.draw.circle(self.image, (255, 235, 120), (center[0] - 4, center[1] - 5), radius // 3)
        pygame.draw.rect(self.image, (204, 132, 0), (center[0] - 2, center[1] - 8, 4, 16))

        self.rect = self.image.get_rect(center=position)
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = -abs(speed)

    def set_speed(self, speed):
        """同步金币移动速度。"""
        self.speed = -abs(speed)

    def update(self):
        self.rect.x += self.speed
        if self.rect.right < 0:
            self.kill()

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Scoreboard(pygame.sprite.Sprite):
    """计分板类"""

    def __init__(self, score, fontpath, position, prefix=None, font_size=24):
        super().__init__()
        self.font = pygame.font.Font(fontpath, font_size)
        self.position = position
        self.score = score
        self.prefix = prefix
        self.color = (83, 83, 83)  # 深灰色字体

    def draw(self, screen):
        # 显示层限制到 5 位，避免异常历史分数把右上角计分板挤在一起。
        safe_score = max(0, min(int(self.score), 99999))
        score_str = f"{safe_score:05d}"
        text = f"{self.prefix} {score_str}" if self.prefix else score_str

        surface = self.font.render(text, True, self.color)
        screen.blit(surface, self.position)
