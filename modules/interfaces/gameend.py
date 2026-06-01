import pygame


def GameEndInterface(screen, game_surface, cfg, score, highest_score, is_new_record, sounds, coins=0):
    """
    游戏结束界面

    Args:
        screen: Pygame真实窗口对象
        game_surface: 固定逻辑分辨率画布
        cfg: 配置模块
    Returns:
        str: 'restart' 重新开始, 'shop' 打开商城, 'quit' 退出
    """
    logical_w, logical_h = cfg.LOGICAL_SIZE

    restart_img = pygame.image.load(cfg.IMAGE_PATHS['replay']).convert_alpha()
    restart_img = pygame.transform.scale(restart_img, (200, 200))
    restart_rect = restart_img.get_rect(center=(logical_w // 2, int(logical_h * 0.72)))

    font_large = pygame.font.Font(cfg.FONT_PATHS['joystix'], 50)
    font_small = pygame.font.Font(cfg.FONT_PATHS['joystix'], 22)
    font_score = pygame.font.Font(cfg.FONT_PATHS['joystix'], 40)
    font_new = pygame.font.Font(cfg.FONT_PATHS['joystix'], 50)

    game_over_text = font_large.render("GAME OVER", True, (83, 83, 83))
    game_over_rect = game_over_text.get_rect(center=(logical_w // 2, int(logical_h * 0.24)))

    tip_text = font_small.render("SPACE/UP: RESTART    S: SHOP    ESC: QUIT", True, (83, 83, 83))
    tip_rect = tip_text.get_rect(center=(logical_w // 2, int(logical_h * 0.92)))

    score_text = font_score.render(f"SCORE: {min(score, 99999):05d}", True, (83, 83, 83))
    score_rect = score_text.get_rect(center=(logical_w // 2, int(logical_h * 0.36)))

    highest_text = font_score.render(f"HIGHEST: {min(highest_score, 99999):05d}", True, (83, 83, 83))
    highest_rect = highest_text.get_rect(center=(logical_w // 2, int(logical_h * 0.43)))

    coin_text = font_small.render(f"COIN {min(coins, 99999):05d}", True, (83, 83, 83))
    coin_rect = coin_text.get_rect(center=(logical_w // 2, int(logical_h * 0.58)))

    new_record_text = None
    new_record_rect = None
    if is_new_record:
        new_record_text = font_new.render("NEW RECORD!", True, (255, 60, 60))
        new_record_rect = new_record_text.get_rect(center=(logical_w // 2, int(logical_h * 0.50)))

    clock = pygame.time.Clock()
    while True:
        clock.tick(60)

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

        game_surface.fill((255, 255, 255))
        game_surface.blit(game_over_text, game_over_rect)
        game_surface.blit(score_text, score_rect)
        game_surface.blit(highest_text, highest_rect)
        if is_new_record:
            game_surface.blit(new_record_text, new_record_rect)
        game_surface.blit(coin_text, coin_rect)
        game_surface.blit(tip_text, tip_rect)
        game_surface.blit(restart_img, restart_rect)

        cfg.blit_scaled(game_surface, screen)
