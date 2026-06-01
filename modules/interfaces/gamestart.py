import pygame
from ..sprites import Dinosaur


TEXT_COLOR = (83, 83, 83)


def _render_centered(surface, font, text, y, color=TEXT_COLOR):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(surface.get_width() // 2, int(y)))
    surface.blit(text_surface, rect)


def GameStartInterface(screen, game_surface, sounds, cfg, coins=0, equipped_skin='default'):
    """
    游戏开始界面
    Args:
        screen: Pygame真实窗口对象
        game_surface: 固定逻辑分辨率画布
        sounds (dict): 音效字典
        cfg: 配置模块
    Returns:
        str: 'start' 开始游戏, 'shop' 打开商城, 'quit' 退出
    """
    title_font = cfg.get_font(60)
    designer_font = cfg.get_font(22)
    tip_font = cfg.get_font(28)
    coin_font = cfg.get_font(26)

    # 创建恐龙对象用于展示
    dino = Dinosaur(cfg.IMAGE_PATHS['dino'], skin=equipped_skin)
    dino.rect.bottom = cfg.GROUND_Y
    dino.rect.left = int(cfg.LOGICAL_SIZE[0] * 0.10)

    # 加载地面图片，按逻辑画布尺寸裁定高度。
    ground_img = pygame.image.load(cfg.IMAGE_PATHS['ground']).convert_alpha()
    ground_height = max(70, cfg.LOGICAL_SIZE[1] - cfg.GROUND_Y)
    ground_width = max(1, int(ground_img.get_width() * ground_height / ground_img.get_height()))
    ground_img = pygame.transform.scale(ground_img, (ground_width, ground_height))
    ground_rect = ground_img.get_rect(topleft=(0, cfg.GROUND_Y))

    clock = pygame.time.Clock()

    # 主循环
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

            if event.type == pygame.VIDEORESIZE:
                screen = cfg.resize_screen(event.size)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    return 'start'
                if event.key == pygame.K_s:
                    sounds['button'].play()
                    return 'shop'
                if event.key == pygame.K_ESCAPE:
                    return 'quit'

        # 更新恐龙动画
        dino.update()

        # 绘制到固定逻辑画布，再整体缩放到真实窗口。
        game_surface.fill((255, 255, 255))
        ground_x = 0
        while ground_x < cfg.LOGICAL_SIZE[0]:
            game_surface.blit(ground_img, (ground_x, ground_rect.top))
            ground_x += ground_img.get_width()

        _render_centered(game_surface, title_font, '像素恐龙快跑', cfg.LOGICAL_SIZE[1] * 0.13)
        _render_centered(game_surface, designer_font, 'PYGAME 课程项目', cfg.LOGICAL_SIZE[1] * 0.25)
        _render_centered(game_surface, tip_font, '按 空格 / ↑ 开始游戏', cfg.LOGICAL_SIZE[1] * 0.57)
        _render_centered(game_surface, tip_font, '按 S 打开商城', cfg.LOGICAL_SIZE[1] * 0.64)
        _render_centered(game_surface, tip_font, '按 ESC 退出游戏', cfg.LOGICAL_SIZE[1] * 0.71)
        _render_centered(game_surface, coin_font, f'金币 {min(coins, 99999):05d}', cfg.LOGICAL_SIZE[1] * 0.80)
        dino.draw(game_surface)

        cfg.blit_scaled(game_surface, screen)
