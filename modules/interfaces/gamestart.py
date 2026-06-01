import pygame
from ..sprites import Dinosaur


def GameStartInterface(screen, game_surface, sounds, cfg, coins=0):
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
    logical_rect = game_surface.get_rect()

    # 游戏标题文本
    title_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 60)
    title_text = title_font.render("D I N O  R U S H", True, (83, 83, 83))
    title_rect = title_text.get_rect()
    title_rect.centerx = logical_rect.centerx
    title_rect.top = int(cfg.LOGICAL_SIZE[1] * 0.13)

    # 设计者信息文本
    designer_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 20)
    designer_text = designer_font.render("PYGAME COURSE PROJECT", True, (83, 83, 83))
    designer_rect = designer_text.get_rect()
    designer_rect.centerx = logical_rect.centerx
    designer_rect.top = int(cfg.LOGICAL_SIZE[1] * 0.25)

    # 开始提示文本
    tip_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 24)
    tip_text = tip_font.render("SPACE/UP: START    S: SHOP    ESC: QUIT", True, (83, 83, 83))
    tip_rect = tip_text.get_rect()
    tip_rect.centerx = logical_rect.centerx
    tip_rect.top = int(cfg.LOGICAL_SIZE[1] * 0.60)

    coin_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 22)
    coin_text = coin_font.render(f"COIN {min(coins, 99999):05d}", True, (83, 83, 83))
    coin_rect = coin_text.get_rect()
    coin_rect.centerx = logical_rect.centerx
    coin_rect.top = int(cfg.LOGICAL_SIZE[1] * 0.68)

    # 创建恐龙对象用于展示
    dino = Dinosaur(cfg.IMAGE_PATHS['dino'])
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
        game_surface.blit(title_text, title_rect)
        game_surface.blit(designer_text, designer_rect)
        game_surface.blit(tip_text, tip_rect)
        game_surface.blit(coin_text, coin_rect)
        dino.draw(game_surface)

        cfg.blit_scaled(game_surface, screen)
