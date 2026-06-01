import pygame
import core


class Ground(pygame.sprite.Sprite):
    """地面类（无限滚动）"""

    _IMAGE_CACHE = {}

    @classmethod
    def _get_image(cls, imagepath):
        ground_height = max(70, core.SCREENSIZE[1] - core.GROUND_Y)
        cache_key = (imagepath, ground_height)
        cached = cls._IMAGE_CACHE.get(cache_key)
        if cached is not None:
            return cached

        original_image = pygame.image.load(imagepath).convert_alpha()
        tile_width = max(1, original_image.get_width())
        tile_height = max(1, original_image.get_height())
        scaled_width = max(1, int(tile_width * ground_height / tile_height))
        image = pygame.transform.scale(
            original_image,
            (scaled_width, ground_height),
        )
        cls._IMAGE_CACHE[cache_key] = image
        return image

    def __init__(self, imagepath, position=None, **kwargs):
        super().__init__()
        if position is None:
            position = (0, core.GROUND_Y)

        self.image = self._get_image(imagepath)
        self.rect = self.image.get_rect(topleft=position)
        self.speed = -10  # 地面向左移动，主循环会同步为当前 game_speed

    def update(self):
        self.rect.x += self.speed
        image_width = self.image.get_width()
        while self.rect.right <= 0:
            self.rect.left += image_width

    def draw(self, screen):
        x = self.rect.left
        while x > 0:
            x -= self.image.get_width()

        while x < core.SCREENSIZE[0]:
            screen.blit(self.image, (x, self.rect.top))
            x += self.image.get_width()


class Cloud(pygame.sprite.Sprite):
    """云朵类"""

    _IMAGE_CACHE = {}

    @classmethod
    def _get_image(cls, imagepath):
        cached = cls._IMAGE_CACHE.get(imagepath)
        if cached is not None:
            return cached
        image = pygame.image.load(imagepath).convert_alpha()
        image = pygame.transform.scale(image, (80, 40))
        cls._IMAGE_CACHE[imagepath] = image
        return image

    def __init__(self, imagepath, position, **kwargs):
        super().__init__()
        self.image = self._get_image(imagepath)
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

    _IMAGE_CACHE = {}

    @classmethod
    def _get_image(cls, radius):
        cached = cls._IMAGE_CACHE.get(radius)
        if cached is not None:
            return cached

        size = radius * 2 + 4
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)

        # 用简单图形画出金币，避免新增或替换图片资源。
        pygame.draw.circle(image, (178, 111, 0), center, radius + 1)
        pygame.draw.circle(image, (255, 205, 55), center, radius)
        pygame.draw.circle(image, (255, 235, 120), (center[0] - 4, center[1] - 5), radius // 3)
        pygame.draw.rect(image, (204, 132, 0), (center[0] - 2, center[1] - 8, 4, 16))

        cls._IMAGE_CACHE[radius] = image
        return image

    def __init__(self, position, speed=10, radius=14, **kwargs):
        """
        Args:
            position (tuple): 金币初始中心点坐标 (centerx, centery)
            speed (int): 从右向左移动的速度，通常与 game_speed 一致
            radius (int): 金币半径
        """
        super().__init__()
        self.image = self._get_image(radius)
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
