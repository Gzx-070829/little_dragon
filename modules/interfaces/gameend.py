import pygame


def GameEndInterface(screen, cfg, score, highest_score, is_new_record, sounds):
    """
    游戏结束界面

    Args:
        screen: Pygame屏幕对象
        cfg: 配置模块
    Returns:
        bool: True 表示重新开始，False 表示退出游戏
    """
    restart_img = pygame.image.load(cfg.IMAGE_PATHS['replay']).convert_alpha()
    restart_img = pygame.transform.scale(restart_img, (200, 200))
    restart_rect = restart_img.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 150))

    font_large = pygame.font.Font(cfg.FONT_PATHS['joystix'], 50)
    font_small = pygame.font.Font(cfg.FONT_PATHS['joystix'], 22)
    font_score = pygame.font.Font(cfg.FONT_PATHS['joystix'], 40)
    font_new = pygame.font.Font(cfg.FONT_PATHS['joystix'], 50)

    game_over_text = font_large.render("GAME OVER", True, (83, 83, 83))
    game_over_rect = game_over_text.get_rect(center=(screen.get_width() // 2, 180))

    tip_text = font_small.render("SPACE/UP: RESTART    ESC: QUIT", True, (83, 83, 83))
    tip_rect = tip_text.get_rect(center=(screen.get_width() // 2, 550))

    score_text = font_score.render(f"SCORE: {score}", True, (83, 83, 83))
    score_rect = score_text.get_rect(center=(screen.get_width() // 2, 260))

    highest_text = font_score.render(f"HIGHEST: {highest_score}", True, (83, 83, 83))
    highest_rect = highest_text.get_rect(center=(screen.get_width() // 2, 300))

    new_record_text = None
    new_record_rect = None
    if is_new_record:
        new_record_text = font_new.render("NEW RECORD!", True, (255, 60, 60))
        new_record_rect = new_record_text.get_rect(center=(screen.get_width() // 2, 340))

    clock = pygame.time.Clock()
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_rect.collidepoint(event.pos):
                    sounds['button'].play()
                    return True

        screen.fill((255, 255, 255))
        screen.blit(game_over_text, game_over_rect)
        screen.blit(score_text, score_rect)
        screen.blit(highest_text, highest_rect)
        if is_new_record:
            screen.blit(new_record_text, new_record_rect)
        screen.blit(tip_text, tip_rect)
        screen.blit(restart_img, restart_rect)

        pygame.display.update()
