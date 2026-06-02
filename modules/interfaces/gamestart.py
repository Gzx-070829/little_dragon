import pygame
from ..sprites import Dinosaur, Ground


TEXT_COLOR = (83, 83, 83)


def _centered_surface(font, text, y, width, color=TEXT_COLOR):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(width // 2, int(y)))
    return text_surface, rect


def GameStartInterface(screen, game_surface, sounds, cfg, coins=0, equipped_skin='default'):
    """
    游戏开始界面。固定中文文字预渲染，循环中只 blit Surface。
    """
    title_font = cfg.get_font(60)
    designer_font = cfg.get_font(22)
    tip_font = cfg.get_font(28)
    coin_font = cfg.get_font(26)
    logical_w, logical_h = cfg.LOGICAL_SIZE

    static_texts = [
        _centered_surface(title_font, '像素恐龙快跑', logical_h * 0.11, logical_w),
        _centered_surface(designer_font, 'PYGAME 课程项目', logical_h * 0.22, logical_w),
        _centered_surface(tip_font, '按 空格 / ↑ 开始游戏', logical_h * 0.46, logical_w),
        _centered_surface(tip_font, '按 S 打开商城', logical_h * 0.53, logical_w),
        _centered_surface(tip_font, '按 A AI演示', logical_h * 0.60, logical_w),
        _centered_surface(tip_font, '按 T 继续训练AI', logical_h * 0.67, logical_w),
        _centered_surface(tip_font, '按 R 重置AI训练', logical_h * 0.74, logical_w),
        _centered_surface(tip_font, '按 D 清除存档', logical_h * 0.80, logical_w),
        _centered_surface(tip_font, '按 ESC 退出游戏', logical_h * 0.86, logical_w),
        _centered_surface(coin_font, f'金币 {min(coins, 99999):05d}', logical_h * 0.93, logical_w),
    ]

    dino = Dinosaur(cfg.IMAGE_PATHS['dino'], skin=equipped_skin)
    dino.rect.bottom = cfg.GROUND_Y
    dino.rect.left = int(logical_w * 0.10)

    ground_img = Ground._get_image(cfg.IMAGE_PATHS['ground'])
    ground_top = cfg.GROUND_Y

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

            if event.type == pygame.VIDEORESIZE:
                screen = cfg.resize_screen(event.size)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    return 'start'
                if event.key == pygame.K_a:
                    sounds['button'].play()
                    return 'ai_demo'
                if event.key == pygame.K_t:
                    sounds['button'].play()
                    return 'ai_train'
                if event.key == pygame.K_d:
                    sounds['button'].play()
                    return 'clear_save'
                if event.key == pygame.K_r:
                    sounds['button'].play()
                    return 'ai_reset'
                if event.key == pygame.K_s:
                    sounds['button'].play()
                    return 'shop'
                if event.key == pygame.K_ESCAPE:
                    return 'quit'

        dino.update()

        game_surface.fill((255, 255, 255))
        ground_x = 0
        while ground_x < logical_w:
            game_surface.blit(ground_img, (ground_x, ground_top))
            ground_x += ground_img.get_width()

        for text_surface, rect in static_texts:
            game_surface.blit(text_surface, rect)
        dino.draw(game_surface)

        cfg.blit_scaled(game_surface, screen)
        clock.tick(cfg.FPS)
