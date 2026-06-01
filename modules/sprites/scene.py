import pygame
import core


class Ground(pygame.sprite.Sprite):
    """地面类（无限滚动）"""

    def __init__(self, imagepath, position, **kwargs):
        super().__init__()
        # 加载地面图片
        self.image = pygame.image.load(imagepath).convert_alpha()

        sw, sh = core.SCREENSIZE

        # 3. 缩放到 屏幕宽度 × 100高度（你可以自己改高度）
        self.image = pygame.transform.scale(self.image, (sw, 100))
        self.rect = self.image.get_rect()
        self.rect.topleft = position

        # 创建第二个地面实现无缝滚动
        self.rect2 = self.image.get_rect()
        self.rect2.left = self.rect.right  # 放在第一个地面右边紧挨着
        self.rect2.bottom = self.rect.bottom

        self.speed = -10  # 地面向左移动

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


class Scoreboard(pygame.sprite.Sprite):
    """计分板类"""

    def __init__(self, score, fontpath, position, is_highest=False):
        super().__init__()
        self.font = pygame.font.Font(fontpath, 30)  # 字体大小
        self.position = position
        self.is_highest = is_highest
        self.score = score
        self.color = (83, 83, 83)  # 深灰色字体

    def draw(self, screen):
        # 补零到 5 位：00000
        score_str = str(self.score).zfill(5)

        # 是最高分就加 HI
        if self.is_highest:
            text = f"HI {score_str}"
        else:
            text = score_str

        # 渲染文字
        surface = self.font.render(text, True, self.color)
        screen.blit(surface, self.position)
