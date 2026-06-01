import pygame
from ..sprites import Dinosaur

def GameStartInterface(screen, sounds, cfg, coins=0):
    """
    游戏开始界面
    Args:
        screen: Pygame屏幕对象
        sounds (dict): 音效字典
        cfg: 配置模块
    Returns:
        str: 'start' 开始游戏, 'shop' 打开商城, 'quit' 退出
    """
    # 游戏标题文本
    title_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 60)
    title_text = title_font.render("D I N O  R U S H", True, (83, 83, 83))
    title_rect = title_text.get_rect()
    title_rect.centerx = screen.get_rect().centerx
    title_rect.top = 80

    # 设计者信息文本
    designer_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 20)
    designer_text = designer_font.render("PYGAME COURSE PROJECT", True, (83, 83, 83))
    designer_rect = designer_text.get_rect()
    designer_rect.centerx = screen.get_rect().centerx
    designer_rect.top = 150

    # 开始提示文本
    tip_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 24)
    tip_text = tip_font.render("SPACE/UP: START    S: SHOP    ESC: QUIT", True, (83, 83, 83))
    tip_rect = tip_text.get_rect()
    tip_rect.centerx = screen.get_rect().centerx
    tip_rect.top = 360

    coin_font = pygame.font.Font(cfg.FONT_PATHS['joystix'], 22)
    coin_text = coin_font.render(f"COIN {str(coins).zfill(5)}", True, (83, 83, 83))
    coin_rect = coin_text.get_rect()
    coin_rect.centerx = screen.get_rect().centerx
    coin_rect.top = 410

    # 创建恐龙对象用于展示
    dino = Dinosaur(cfg.IMAGE_PATHS['dino'])
    dino.rect.bottom = 430
    dino.rect.left = 120

    # 加载地面图片
    ground_img = pygame.image.load(cfg.IMAGE_PATHS['ground']).convert_alpha()
    ground_img = pygame.transform.scale(ground_img, (cfg.SCREENSIZE[0], 100))
    ground_rect = ground_img.get_rect()
    ground_rect.bottom = cfg.SCREENSIZE[1]

    clock = pygame.time.Clock()

    # 主循环
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

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

        # 绘制
        screen.fill((255, 255, 255))
        screen.blit(ground_img, ground_rect)
        screen.blit(title_text, title_rect)
        screen.blit(designer_text, designer_rect)
        screen.blit(tip_text, tip_rect)
        screen.blit(coin_text, coin_rect)
        dino.draw(screen)

        pygame.display.update()
