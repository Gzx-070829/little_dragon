import os
import random
import sqlite3
import time

import pygame

import core
from modules import *

DB_PATH = os.path.join(core.BASE_DIR, 'history.db')


def _default_upgrades():
    return {
        'jump_boost': 0,
        'slow_start': 0,
        'magnet': 0,
        'skin_blue': 0,
        'skin_golden': 0,
        'skin_night': 0,
        'equipped_skin': 'default',
    }


def init_database():
    """初始化数据库并返回连接、历史最高分、金币和升级状态。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS record (
            unix_timestamp INTEGER PRIMARY KEY,
            score INTEGER NOT NULL
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS player_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            coins INTEGER NOT NULL DEFAULT 0,
            jump_boost INTEGER NOT NULL DEFAULT 0,
            slow_start INTEGER NOT NULL DEFAULT 0,
            magnet INTEGER NOT NULL DEFAULT 0,
            skin_blue INTEGER NOT NULL DEFAULT 0,
            skin_golden INTEGER NOT NULL DEFAULT 0,
            skin_night INTEGER NOT NULL DEFAULT 0,
            equipped_skin TEXT NOT NULL DEFAULT 'default'
        );
        """
    )
    for column_sql in (
        "ALTER TABLE player_state ADD COLUMN magnet INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN skin_blue INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN skin_golden INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN skin_night INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN equipped_skin TEXT NOT NULL DEFAULT 'default'",
    ):
        try:
            cursor.execute(column_sql)
        except sqlite3.OperationalError:
            pass
    cursor.execute(
        """
        INSERT OR IGNORE INTO player_state (id, coins, jump_boost, slow_start, magnet,
                                            skin_blue, skin_golden, skin_night, equipped_skin)
        VALUES (1, 0, 0, 0, 0, 0, 0, 0, 'default');
        """
    )
    conn.commit()

    highest_score = 0
    try:
        cursor.execute("SELECT MAX(score) FROM record;")
        max_score = cursor.fetchone()[0]
        if max_score is not None:
            highest_score = max_score
    except Exception as e:
        print(f"读取最高分失败: {e}")

    coins, upgrades = load_player_state(conn)
    return conn, highest_score, coins, upgrades


def load_player_state(conn):
    """读取金币和已购买升级。"""
    upgrades = _default_upgrades()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT coins, jump_boost, slow_start, magnet,
                   skin_blue, skin_golden, skin_night, equipped_skin
            FROM player_state WHERE id = 1;
            """
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                """
                INSERT INTO player_state (id, coins, jump_boost, slow_start, magnet,
                                          skin_blue, skin_golden, skin_night, equipped_skin)
                VALUES (1, 0, 0, 0, 0, 0, 0, 0, 'default');
                """
            )
            conn.commit()
            return 0, upgrades

        (
            coins,
            jump_boost,
            slow_start,
            magnet,
            skin_blue,
            skin_golden,
            skin_night,
            equipped_skin,
        ) = row
        upgrades['jump_boost'] = int(jump_boost)
        upgrades['slow_start'] = int(slow_start)
        upgrades['magnet'] = int(magnet)
        upgrades['skin_blue'] = int(skin_blue)
        upgrades['skin_golden'] = int(skin_golden)
        upgrades['skin_night'] = int(skin_night)
        upgrades['equipped_skin'] = equipped_skin if equipped_skin in ('default', 'blue', 'golden', 'night') else 'default'
        return int(coins), upgrades
    except Exception as e:
        print(f"读取玩家状态失败: {e}")
        return 0, upgrades


def save_player_state(conn, coins, upgrades):
    """保存金币和升级状态。"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE player_state
            SET coins = ?, jump_boost = ?, slow_start = ?, magnet = ?,
                skin_blue = ?, skin_golden = ?, skin_night = ?, equipped_skin = ?
            WHERE id = 1;
            """,
            (
                int(coins),
                int(upgrades.get('jump_boost', 0)),
                int(upgrades.get('slow_start', 0)),
                int(upgrades.get('magnet', 0)),
                int(upgrades.get('skin_blue', 0)),
                int(upgrades.get('skin_golden', 0)),
                int(upgrades.get('skin_night', 0)),
                upgrades.get('equipped_skin', 'default'),
            )
        )
        conn.commit()
    except Exception as e:
        print(f"保存玩家状态失败: {e}")


def save_score(conn, score):
    """保存本局分数。"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO record (unix_timestamp, score) VALUES (?, ?)",
            (int(time.time()), score)
        )
        conn.commit()
    except Exception as e:
        print(f"保存分数失败: {e}")


def open_shop(screen, game_surface, sounds, coins, upgrades, conn):
    """打开商城并立即保存购买和装备结果。"""
    def save_shop_state(shop_coins, shop_upgrades):
        save_player_state(conn, shop_coins, shop_upgrades)

    coins, upgrades = ShopInterface(
        screen,
        game_surface,
        core,
        coins,
        upgrades,
        sounds,
        save_callback=save_shop_state,
    )
    save_player_state(conn, coins, upgrades)
    return coins, upgrades


def get_current_speed(score, upgrades):
    """根据当前分数连续计算速度，避免整千分突变或漏触发。"""
    base_speed = (
        core.SLOW_START_GAME_SPEED
        if upgrades.get('slow_start', 0)
        else core.BASE_GAME_SPEED
    )
    return min(core.MAX_GAME_SPEED, base_speed + score // 500)


def apply_speed_to_sprites(
    current_speed,
    ground,
    cactus_sprites_group,
    ptera_sprites_group,
    coin_sprites_group,
):
    """把当前游戏速度同步给所有横向移动对象。"""
    ground.speed = -current_speed
    for cactus in cactus_sprites_group:
        cactus.speed = -current_speed
    for ptera in ptera_sprites_group:
        ptera.speed = -current_speed
    for coin in coin_sprites_group:
        coin.set_speed(current_speed)


def next_obstacle_interval(score):
    """分数越高障碍物间隔略微缩短，但保留可反应空间。"""
    difficulty_steps = min(score // 1000, 8)
    return random.randint(75 - difficulty_steps * 2, 140 - difficulty_steps * 4)


def apply_coin_magnet(dino, coin_sprites_group):
    """Pull nearby coins toward the dinosaur when the Magnet upgrade is owned."""
    magnet_radius = 175
    pull_strength = 0.18
    for coin in coin_sprites_group:
        dx = dino.rect.centerx - coin.rect.centerx
        dy = dino.rect.centery - coin.rect.centery
        distance_squared = dx * dx + dy * dy
        if 0 < distance_squared <= magnet_radius * magnet_radius:
            coin.rect.x += int(dx * pull_strength)
            coin.rect.y += int(dy * pull_strength)


def create_screen():
    """Create the default resizable window without changing logical layout."""
    return pygame.display.set_mode(core.WINDOW_SIZE, pygame.RESIZABLE)


def draw_hud(game_surface, font, coins, highest_score, score):
    """Draw stable HUD text inside the fixed logical canvas."""
    margin = 50
    hud_y = 80
    score_y = 120

    safe_coins = max(0, min(int(coins), 99999))
    safe_highest = max(0, min(int(highest_score), 99999))
    safe_score = max(0, min(int(score), 99999))

    coin_surface = font.render(f"COIN {safe_coins:05d}", True, core.BLACK)
    coin_rect = coin_surface.get_rect(topleft=(margin, hud_y))

    hi_surface = font.render(f"HI {safe_highest:05d}", True, core.BLACK)
    hi_rect = hi_surface.get_rect(topright=(core.LOGICAL_SIZE[0] - margin, hud_y))

    score_surface = font.render(f"SCORE {safe_score:05d}", True, core.BLACK)
    score_rect = score_surface.get_rect(
        topright=(core.LOGICAL_SIZE[0] - margin, score_y)
    )

    game_surface.blit(coin_surface, coin_rect)
    game_surface.blit(hi_surface, hi_rect)
    game_surface.blit(score_surface, score_rect)


def main(conn, highest_score, coins, upgrades):
    """
    游戏主函数

    Args:
        conn: SQLite 数据库连接
        highest_score (int): 历史最高分
        coins (int): 玩家持有金币
        upgrades (dict): 已购买升级

    Returns:
        tuple: (是否继续游戏, 当前最高分, 当前金币, 当前升级)
    """
    pygame.init()
    screen = create_screen()
    game_surface = pygame.Surface(core.LOGICAL_SIZE)
    pygame.display.set_caption('Dino Rush')

    sounds = {}
    for key, path in core.AUDIO_PATHS.items():
        sounds[key] = pygame.mixer.Sound(path)

    while True:
        start_action = GameStartInterface(screen, game_surface, sounds, core, coins, upgrades.get('equipped_skin', 'default'))
        screen = pygame.display.get_surface() or screen
        if start_action == 'start':
            break
        if start_action == 'shop':
            coins, upgrades = open_shop(screen, game_surface, sounds, coins, upgrades, conn)
            screen = pygame.display.get_surface() or screen
            continue
        return False, highest_score, coins, upgrades

    score = 0
    dino = Dinosaur(
        core.IMAGE_PATHS['dino'],
        position=(40, core.GROUND_Y),
        skin=upgrades.get('equipped_skin', 'default'),
    )
    if upgrades.get('jump_boost', 0):
        dino.speed = 21

    ground = Ground(core.IMAGE_PATHS['ground'], position=(0, core.GROUND_Y))

    cloud_sprites_group = pygame.sprite.Group()
    cactus_sprites_group = pygame.sprite.Group()
    ptera_sprites_group = pygame.sprite.Group()
    coin_sprites_group = pygame.sprite.Group()

    add_obstacle_timer = 0
    next_obstacle_gap = next_obstacle_interval(score)
    add_coin_timer = 0
    next_coin_gap = random.randint(100, 180)
    score_timer = 0
    clock = pygame.time.Clock()
    hud_font = pygame.font.Font(core.FONT_PATHS['joystix'], 24)
    current_speed = get_current_speed(score, upgrades)
    apply_speed_to_sprites(
        current_speed,
        ground,
        cactus_sprites_group,
        ptera_sprites_group,
        coin_sprites_group,
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_player_state(conn, coins, upgrades)
                return False, highest_score, coins, upgrades

            if event.type == pygame.VIDEORESIZE:
                screen = core.resize_screen(event.size)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save_player_state(conn, coins, upgrades)
                    return False, highest_score, coins, upgrades
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump(sounds)
                if event.key == pygame.K_DOWN or event.key == pygame.K_LSHIFT:
                    dino.duck()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN or event.key == pygame.K_LSHIFT:
                    dino.unduck()

        score_timer += 1
        if score_timer > 10:
            score_timer = 0
            score += 1
            if score % 100 == 0:
                sounds['point'].play()

        current_speed = get_current_speed(score, upgrades)
        apply_speed_to_sprites(
            current_speed,
            ground,
            cactus_sprites_group,
            ptera_sprites_group,
            coin_sprites_group,
        )

        game_surface.fill(core.BACKGROUND_COLOR)

        if len(cloud_sprites_group) < 5 and random.randint(0, 600) == 1:
            x = core.SCREENSIZE[0] + random.randint(80, 180)
            y = random.randint(50, 200)
            cloud = Cloud(core.IMAGE_PATHS['cloud'], position=(x, y))
            cloud_sprites_group.add(cloud)

        add_obstacle_timer += 1
        if add_obstacle_timer > next_obstacle_gap:
            add_obstacle_timer = 0
            next_obstacle_gap = next_obstacle_interval(score)
            x = core.SCREENSIZE[0] + random.randint(80, 180)

            if random.randint(0, 100) < 80:
                cactus = Cactus(
                    core.IMAGE_PATHS['cacti'],
                    position=(x, core.GROUND_Y),
                    speed=current_speed,
                )
                cactus_sprites_group.add(cactus)
            else:
                ptera_y = random.choice([core.GROUND_Y - 70, core.GROUND_Y - 130])
                ptera = Ptera(
                    core.IMAGE_PATHS['ptera'],
                    position=(x, ptera_y),
                    speed=current_speed,
                )
                ptera_sprites_group.add(ptera)

        add_coin_timer += 1
        if add_coin_timer > next_coin_gap:
            add_coin_timer = 0
            next_coin_gap = random.randint(100, 190)
            x = core.SCREENSIZE[0] + random.randint(70, 170)
            coin_y = random.choice([
                core.GROUND_Y - 35,
                core.GROUND_Y - 35,
                core.GROUND_Y - 110,
            ])
            coin_sprites_group.add(Coin(position=(x, coin_y), speed=current_speed))

        dino.update()
        ground.update()
        cloud_sprites_group.update()
        cactus_sprites_group.update()
        ptera_sprites_group.update()
        coin_sprites_group.update()
        if upgrades.get('magnet', 0):
            apply_coin_magnet(dino, coin_sprites_group)

        hit_cactus = any(
            pygame.sprite.collide_mask(dino, cactus) for cactus in cactus_sprites_group
        )
        hit_ptera = any(
            pygame.sprite.collide_mask(dino, ptera) for ptera in ptera_sprites_group
        )
        if hit_cactus or hit_ptera:
            dino.die(sounds)

        collected_coins = pygame.sprite.spritecollide(
            dino,
            coin_sprites_group,
            True,
            pygame.sprite.collide_mask,
        )
        if collected_coins:
            coins += len(collected_coins)
            sounds['point'].play()

        cloud_sprites_group.draw(game_surface)
        ground.draw(game_surface)
        cactus_sprites_group.draw(game_surface)
        ptera_sprites_group.draw(game_surface)
        coin_sprites_group.draw(game_surface)
        dino.draw(game_surface)

        draw_hud(game_surface, hud_font, coins, highest_score, score)

        core.blit_scaled(game_surface, screen)
        clock.tick(core.FPS)

        if dino.is_dead:
            save_score(conn, score)
            save_player_state(conn, coins, upgrades)
            is_new_record = False
            if score > highest_score:
                highest_score = score
                is_new_record = True
            break

    while True:
        end_action = GameEndInterface(
            screen,
            game_surface,
            core,
            score,
            highest_score,
            is_new_record,
            sounds,
            coins,
        )
        screen = pygame.display.get_surface() or screen
        if end_action == 'restart':
            return True, highest_score, coins, upgrades
        if end_action == 'shop':
            coins, upgrades = open_shop(screen, game_surface, sounds, coins, upgrades, conn)
            screen = pygame.display.get_surface() or screen
            continue
        return False, highest_score, coins, upgrades


if __name__ == '__main__':
    conn, highest_score, coins, upgrades = init_database()
    try:
        while True:
            flag, highest_score, coins, upgrades = main(conn, highest_score, coins, upgrades)
            if not flag:
                save_player_state(conn, coins, upgrades)
                break
    finally:
        conn.close()
        pygame.quit()
