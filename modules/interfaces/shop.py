import pygame


SHOP_ITEMS = {
    pygame.K_1: {
        'key': 'jump_boost',
        'name': 'Jump Boost',
        'cost': 5,
        'effect': 'Higher jumps: speed 18 -> 21',
    },
    pygame.K_2: {
        'key': 'slow_start',
        'name': 'Slow Start',
        'cost': 8,
        'effect': 'Start slower: speed 10 -> 8',
    },
}


def _draw_centered(screen, font, text, y, color=(83, 83, 83)):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(screen.get_width() // 2, y))
    screen.blit(surface, rect)


def ShopInterface(screen, cfg, coins, upgrades, sounds=None):
    """简单商城界面。

    Args:
        screen: Pygame 屏幕对象
        cfg: 配置模块
        coins (int): 当前金币数
        upgrades (dict): 已购买升级状态
        sounds (dict): 可选音效字典

    Returns:
        tuple: (coins, upgrades)
    """
    upgrades = upgrades.copy()
    font_title = pygame.font.Font(cfg.FONT_PATHS['joystix'], 48)
    font_medium = pygame.font.Font(cfg.FONT_PATHS['joystix'], 26)
    font_small = pygame.font.Font(cfg.FONT_PATHS['joystix'], 18)
    clock = pygame.time.Clock()
    message = ''
    message_color = (83, 83, 83)

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return coins, upgrades

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if sounds:
                        sounds['button'].play()
                    return coins, upgrades

                item = SHOP_ITEMS.get(event.key)
                if item:
                    upgrade_key = item['key']
                    if upgrades.get(upgrade_key, 0):
                        message = f"{item['name']} already owned"
                        message_color = (83, 83, 83)
                    elif coins < item['cost']:
                        message = f"Need {item['cost']} coins"
                        message_color = (210, 60, 60)
                    else:
                        coins -= item['cost']
                        upgrades[upgrade_key] = 1
                        message = f"Bought {item['name']}!"
                        message_color = (46, 145, 70)
                        if sounds:
                            sounds['point'].play()

        screen.fill((255, 255, 255))
        _draw_centered(screen, font_title, 'SHOP', 90)
        _draw_centered(screen, font_medium, f'COINS: {str(coins).zfill(5)}', 155)

        y = 245
        for key_label, item in (('1', SHOP_ITEMS[pygame.K_1]), ('2', SHOP_ITEMS[pygame.K_2])):
            owned = bool(upgrades.get(item['key'], 0))
            status = 'OWNED' if owned else f"{item['cost']} COINS"
            color = (46, 145, 70) if owned else (83, 83, 83)
            _draw_centered(screen, font_medium, f"PRESS {key_label}: {item['name']} - {status}", y, color)
            _draw_centered(screen, font_small, item['effect'], y + 34, (105, 105, 105))
            y += 95

        if message:
            _draw_centered(screen, font_small, message, 455, message_color)
        _draw_centered(screen, font_small, 'ESC: RETURN', 520)

        pygame.display.update()
