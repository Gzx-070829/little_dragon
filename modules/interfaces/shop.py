import pygame


UPGRADE_ITEMS = {
    pygame.K_1: {
        'key': 'jump_boost',
        'name': 'Jump Boost',
        'cost': 5,
        'effect': 'Higher jumps',
    },
    pygame.K_2: {
        'key': 'slow_start',
        'name': 'Slow Start',
        'cost': 8,
        'effect': 'Slower starting speed',
    },
    pygame.K_3: {
        'key': 'magnet',
        'name': 'Magnet',
        'cost': 10,
        'effect': 'Pull nearby coins to the dino',
    },
}

SKIN_ITEMS = {
    pygame.K_4: {
        'key': 'default',
        'owned_key': None,
        'name': 'Default Skin',
        'cost': 0,
        'cost_text': 'FREE',
    },
    pygame.K_5: {
        'key': 'blue',
        'owned_key': 'skin_blue',
        'name': 'Blue Dino',
        'cost': 6,
        'cost_text': '6 coins',
    },
    pygame.K_6: {
        'key': 'golden',
        'owned_key': 'skin_golden',
        'name': 'Golden Dino',
        'cost': 12,
        'cost_text': '12 coins',
    },
    pygame.K_7: {
        'key': 'night',
        'owned_key': 'skin_night',
        'name': 'Night Dino',
        'cost': 15,
        'cost_text': '15 coins',
    },
}


def _draw_centered(surface, font, text, y, color=(83, 83, 83)):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(surface.get_width() // 2, int(y)))
    surface.blit(text_surface, rect)


def _draw_text(surface, font, text, pos, color=(83, 83, 83)):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)


def _owns_skin(upgrades, skin_item):
    owned_key = skin_item['owned_key']
    return owned_key is None or bool(upgrades.get(owned_key, 0))


def _skin_status(upgrades, skin_item):
    if upgrades.get('equipped_skin', 'default') == skin_item['key']:
        return 'EQUIPPED'
    if _owns_skin(upgrades, skin_item):
        return 'OWNED / EQUIP'
    return 'BUY'


def _save_if_needed(save_callback, coins, upgrades):
    if save_callback:
        save_callback(coins, upgrades)


def ShopInterface(screen, game_surface, cfg, coins, upgrades, sounds=None, save_callback=None):
    """简单商城界面。所有内容先绘制到固定逻辑画布。"""
    upgrades = upgrades.copy()
    font_title = pygame.font.Font(cfg.FONT_PATHS['joystix'], 42)
    font_medium = pygame.font.Font(cfg.FONT_PATHS['joystix'], 21)
    font_small = pygame.font.Font(cfg.FONT_PATHS['joystix'], 16)
    clock = pygame.time.Clock()
    message = ''
    message_color = (83, 83, 83)

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return coins, upgrades

            if event.type == pygame.VIDEORESIZE:
                screen = cfg.resize_screen(event.size)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if sounds:
                        sounds['button'].play()
                    return coins, upgrades

                upgrade = UPGRADE_ITEMS.get(event.key)
                if upgrade:
                    upgrade_key = upgrade['key']
                    if upgrades.get(upgrade_key, 0):
                        message = f"{upgrade['name']} OWNED"
                        message_color = (83, 83, 83)
                    elif coins < upgrade['cost']:
                        message = 'NOT ENOUGH COINS'
                        message_color = (210, 60, 60)
                    else:
                        coins -= upgrade['cost']
                        upgrades[upgrade_key] = 1
                        message = f"BOUGHT {upgrade['name']}"
                        message_color = (46, 145, 70)
                        _save_if_needed(save_callback, coins, upgrades)
                        if sounds:
                            sounds['point'].play()

                skin = SKIN_ITEMS.get(event.key)
                if skin:
                    owned = _owns_skin(upgrades, skin)
                    if not owned:
                        if coins < skin['cost']:
                            message = 'NOT ENOUGH COINS'
                            message_color = (210, 60, 60)
                            continue
                        coins -= skin['cost']
                        upgrades[skin['owned_key']] = 1
                        message = f"BOUGHT AND EQUIPPED {skin['name']}"
                        message_color = (46, 145, 70)
                        if sounds:
                            sounds['point'].play()
                    else:
                        message = f"EQUIPPED {skin['name']}"
                        message_color = (46, 145, 70)
                        if sounds:
                            sounds['button'].play()
                    upgrades['equipped_skin'] = skin['key']
                    _save_if_needed(save_callback, coins, upgrades)

        game_surface.fill((255, 255, 255))
        _draw_centered(game_surface, font_title, 'SHOP', 55)
        _draw_centered(game_surface, font_medium, f'COINS: {min(coins, 99999):05d}', 105)

        _draw_text(game_surface, font_medium, 'UPGRADES', (90, 150))
        y = 188
        for key_label, item in (('1', UPGRADE_ITEMS[pygame.K_1]), ('2', UPGRADE_ITEMS[pygame.K_2]), ('3', UPGRADE_ITEMS[pygame.K_3])):
            owned = bool(upgrades.get(item['key'], 0))
            status = 'OWNED' if owned else 'BUY'
            color = (46, 145, 70) if owned else (83, 83, 83)
            line = f"[{key_label}] {item['name']:<11} - {item['cost']:>2} coins - {status}"
            _draw_text(game_surface, font_small, line, (110, y), color)
            _draw_text(game_surface, font_small, item['effect'], (650, y), (105, 105, 105))
            y += 32

        _draw_text(game_surface, font_medium, 'SKINS', (90, 310))
        y = 348
        skin_rows = (
            ('4', SKIN_ITEMS[pygame.K_4]),
            ('5', SKIN_ITEMS[pygame.K_5]),
            ('6', SKIN_ITEMS[pygame.K_6]),
            ('7', SKIN_ITEMS[pygame.K_7]),
        )
        for key_label, item in skin_rows:
            status = _skin_status(upgrades, item)
            color = (46, 145, 70) if status != 'BUY' else (83, 83, 83)
            line = f"[{key_label}] {item['name']:<12} - {item['cost_text']:<8} - {status}"
            _draw_text(game_surface, font_small, line, (110, y), color)
            y += 32

        if message:
            _draw_centered(game_surface, font_small, message, 505, message_color)
        _draw_centered(game_surface, font_small, 'ESC: BACK', 550)

        cfg.blit_scaled(game_surface, screen)
