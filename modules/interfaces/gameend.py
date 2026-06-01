import pygame


TEXT_COLOR = (83, 83, 83)
_REPLAY_CACHE = {}


def _render_centered(surface, font, text, y, color=TEXT_COLOR):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(surface.get_width() // 2, int(y)))
    surface.blit(text_surface, rect)


def _get_replay_image(cfg):
    cached = _REPLAY_CACHE.get(cfg.IMAGE_PATHS['replay'])
    if cached is not None:
        return cached
    image = pygame.image.load(cfg.IMAGE_PATHS['replay']).convert_alpha()
    image = pygame.transform.scale(image, (200, 200))
    _REPLAY_CACHE[cfg.IMAGE_PATHS['replay']] = image
    return image


def GameEndInterface(screen, game_surface, cfg, score, highest_score, is_new_record, sounds, coins=0):
    """
    游戏结束界面。进入界面时预渲染静态内容，循环中只处理事件和缩放显示。
    """
    logical_w, logical_h = cfg.LOGICAL_SIZE

    restart_img = _get_replay_image(cfg)
    restart_rect = restart_img.get_rect(center=(logical_w // 2, int(logical_h * 0.70)))

    font_large = cfg.get_font(56)
    font_small = cfg.get_font(26)
    font_score = cfg.get_font(34)
    font_new = cfg.get_font(44)

    end_surface = pygame.Surface(cfg.LOGICAL_SIZE)
    end_surface.fill((255, 255, 255))
    _render_centered(end_surface, font_large, '游戏结束', logical_h * 0.18)
    _render_centered(end_surface, font_score, f'分数 {min(score, 99999):05d}', logical_h * 0.31)
    _render_centered(end_surface, font_score, f'最高 {min(highest_score, 99999):05d}', logical_h * 0.39)
    if is_new_record:
        _render_centered(end_surface, font_new, '新的最高分！', logical_h * 0.49, (255, 60, 60))
    _render_centered(end_surface, font_small, f'金币 {min(coins, 99999):05d}', logical_h * 0.56)
    end_surface.blit(restart_img, restart_rect)
    _render_centered(end_surface, font_small, '按 空格 / ↑ 重新开始', logical_h * 0.86)
    _render_centered(end_surface, font_small, '按 S 打开商城    按 ESC 退出游戏', logical_h * 0.93)

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

            if event.type == pygame.VIDEORESIZE:
                screen = cfg.resize_screen(event.size)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    return 'restart'
                if event.key == pygame.K_s:
                    sounds['button'].play()
                    return 'shop'
                if event.key == pygame.K_ESCAPE:
                    return 'quit'

            if event.type == pygame.MOUSEBUTTONDOWN:
                game_pos = cfg.screen_to_game_pos(event.pos, screen, game_surface)
                if game_pos is not None and restart_rect.collidepoint(game_pos):
                    sounds['button'].play()
                    return 'restart'

        game_surface.blit(end_surface, (0, 0))
        cfg.blit_scaled(game_surface, screen)
        clock.tick(cfg.FPS)
