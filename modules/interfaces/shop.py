import pygame


UPGRADE_ITEMS = {
    pygame.K_1: {
        'key': 'jump_boost',
        'name': '跳跃强化',
        'cost': 5,
        'effect': '提高跳跃高度',
    },
    pygame.K_2: {
        'key': 'slow_start',
        'name': '慢速开局',
        'cost': 8,
        'effect': '降低初始速度',
    },
    pygame.K_3: {
        'key': 'magnet',
        'name': '金币磁铁',
        'cost': 10,
        'effect': '靠近金币时自动吸附',
    },
}

SKIN_ITEMS = {
    pygame.K_4: {
        'key': 'default',
        'owned_key': None,
        'name': '默认皮肤',
        'cost': 0,
        'cost_text': '免费',
    },
    pygame.K_5: {
        'key': 'blue',
        'owned_key': 'skin_blue',
        'name': '蓝色恐龙',
        'cost': 6,
        'cost_text': '6 金币',
    },
    pygame.K_6: {
        'key': 'golden',
        'owned_key': 'skin_golden',
        'name': '黄金恐龙',
        'cost': 12,
        'cost_text': '12 金币',
    },
    pygame.K_7: {
        'key': 'night',
        'owned_key': 'skin_night',
        'name': '暗夜恐龙',
        'cost': 15,
        'cost_text': '15 金币',
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
        return '已装备'
    if _owns_skin(upgrades, skin_item):
        return '已拥有 / 装备'
    return '购买'


def _save_if_needed(save_callback, coins, upgrades):
    if save_callback:
        save_callback(coins, upgrades)


def _render_centered_item(font, text, y, surface_width, color=(83, 83, 83)):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(surface_width // 2, int(y)))
    return text_surface, rect


def _render_text_item(font, text, pos, color=(83, 83, 83)):
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect(topleft=pos)


def _render_shop_surface(surface, font_title, font_medium, font_small, coins, upgrades, message, message_color):
    """Render shop text only after coins/owned/equipped/message changes."""
    surface.fill((255, 255, 255))
    width = surface.get_width()
    render_items = [
        _render_centered_item(font_title, '商城', 55, width),
        _render_centered_item(font_medium, f'金币：{min(coins, 99999):05d}', 105, width),
        _render_text_item(font_medium, '属性升级', (90, 150)),
        _render_text_item(font_medium, '恐龙皮肤', (90, 310)),
        _render_centered_item(font_small, '按 ESC 返回', 550, width),
    ]

    y = 188
    for key_label, item in (('1', UPGRADE_ITEMS[pygame.K_1]), ('2', UPGRADE_ITEMS[pygame.K_2]), ('3', UPGRADE_ITEMS[pygame.K_3])):
        owned = bool(upgrades.get(item['key'], 0))
        status = '已拥有' if owned else '购买'
        color = (46, 145, 70) if owned else (83, 83, 83)
        line = f"[{key_label}] {item['name']} - {item['cost']} 金币 - {status}"
        render_items.append(_render_text_item(font_small, line, (110, y), color))
        render_items.append(_render_text_item(font_small, item['effect'], (650, y), (105, 105, 105)))
        y += 32

    y = 348
    skin_rows = (
        ('4', SKIN_ITEMS[pygame.K_4]),
        ('5', SKIN_ITEMS[pygame.K_5]),
        ('6', SKIN_ITEMS[pygame.K_6]),
        ('7', SKIN_ITEMS[pygame.K_7]),
    )
    for key_label, item in skin_rows:
        status = _skin_status(upgrades, item)
        color = (46, 145, 70) if status != '购买' else (83, 83, 83)
        line = f"[{key_label}] {item['name']} - {item['cost_text']} - {status}"
        render_items.append(_render_text_item(font_small, line, (110, y), color))
        y += 32

    if message:
        render_items.append(_render_centered_item(font_small, message, 505, width, message_color))

    for text_surface, rect in render_items:
        surface.blit(text_surface, rect)


def ShopInterface(screen, game_surface, cfg, coins, upgrades, sounds=None, save_callback=None):
    """简单商城界面。文字仅在状态变化时重新渲染。"""
    upgrades = upgrades.copy()
    font_title = cfg.get_font(46)
    font_medium = cfg.get_font(26)
    font_small = cfg.get_font(21)
    clock = pygame.time.Clock()
    message = ''
    message_color = (83, 83, 83)
    dirty = True

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

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
                        message = f"{upgrade['name']} 已经拥有"
                        message_color = (83, 83, 83)
                    elif coins < upgrade['cost']:
                        message = '金币不足'
                        message_color = (210, 60, 60)
                    else:
                        coins -= upgrade['cost']
                        upgrades[upgrade_key] = 1
                        message = f"购买成功：{upgrade['name']}"
                        message_color = (46, 145, 70)
                        _save_if_needed(save_callback, coins, upgrades)
                        if sounds:
                            sounds['point'].play()
                    dirty = True

                skin = SKIN_ITEMS.get(event.key)
                if skin:
                    owned = _owns_skin(upgrades, skin)
                    if not owned:
                        if coins < skin['cost']:
                            message = '金币不足'
                            message_color = (210, 60, 60)
                            dirty = True
                            continue
                        coins -= skin['cost']
                        upgrades[skin['owned_key']] = 1
                        message = f"购买成功，已装备：{skin['name']}"
                        message_color = (46, 145, 70)
                        if sounds:
                            sounds['point'].play()
                    else:
                        message = f"已装备：{skin['name']}"
                        message_color = (46, 145, 70)
                        if sounds:
                            sounds['button'].play()
                    upgrades['equipped_skin'] = skin['key']
                    _save_if_needed(save_callback, coins, upgrades)
                    dirty = True

        if dirty:
            _render_shop_surface(game_surface, font_title, font_medium, font_small, coins, upgrades, message, message_color)
            dirty = False

        cfg.blit_scaled(game_surface, screen)
        clock.tick(cfg.FPS)
