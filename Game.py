import os
import random
import sqlite3
import time

import pygame

import core
from modules.interfaces import GameEndInterface, GameStartInterface, ShopInterface
from modules.sprites import Cactus, Cloud, Coin, Dinosaur, Ground, Ptera
from rl_agent import QLearningAgent

DB_PATH = os.path.join(core.BASE_DIR, 'history.db')
Q_TABLE_PATH = os.path.join(core.BASE_DIR, 'rl_q_table.json')
SPEED_SCORE_STEP = 120
BASE_MIN_OBSTACLE_GAP = 75
BASE_MAX_OBSTACLE_GAP = 130
MIN_OBSTACLE_GAP = 45
MIN_MAX_OBSTACLE_GAP = 80
MAX_OBSTACLES_ON_SCREEN = 4



def handle_loading_events():
    """处理加载阶段事件，避免窗口被系统标记为无响应。"""
    screen = pygame.display.get_surface()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return screen, False
        if event.type == pygame.VIDEORESIZE:
            screen = core.resize_screen(event.size)
    pygame.event.pump()
    return screen, True


def draw_loading_screen(screen, message="资源加载中..."):
    """启动后立刻绘制中文加载界面，并在每个加载阶段刷新。"""
    game_surface = pygame.Surface(core.LOGICAL_SIZE)
    game_surface.fill(core.BACKGROUND_COLOR)
    try:
        title_font = core.get_font(56)
        message_font = core.get_font(30)
        hint_font = core.get_font(24)
    except Exception:
        title_font = pygame.font.Font(None, 56)
        message_font = pygame.font.Font(None, 30)
        hint_font = pygame.font.Font(None, 24)

    lines = (
        (title_font, '像素恐龙快跑', core.LOGICAL_SIZE[1] * 0.34),
        (message_font, message, core.LOGICAL_SIZE[1] * 0.50),
        (hint_font, '请稍候', core.LOGICAL_SIZE[1] * 0.60),
    )
    for font, text, y in lines:
        text_surface = font.render(text, True, core.BLACK)
        rect = text_surface.get_rect(center=(core.LOGICAL_SIZE[0] // 2, int(y)))
        game_surface.blit(text_surface, rect)

    core.blit_scaled(game_surface, screen)
    return handle_loading_events()


def loading_step(screen, message, func=None):
    """显示加载提示，执行单个加载步骤，完成后再次泵事件。"""
    screen, running = draw_loading_screen(screen, message)
    if not running:
        raise SystemExit
    if func is not None:
        func()
    screen, running = handle_loading_events()
    if not running:
        raise SystemExit
    return pygame.display.get_surface() or screen


def _default_upgrades():
    return {
        'jump_boost': 0,
        'slow_start': 0,
        'magnet': 0,
        'skin_blue': 0,
        'skin_golden': 0,
        'skin_night': 0,
        'skin_runner': 0,
        'equipped_skin': 'default',
        'cloud_text_skin': 0,
        'equipped_cloud_skin': 'default',
        'coin_icecream_skin': 0,
        'equipped_coin_skin': 'default',
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
            skin_runner INTEGER NOT NULL DEFAULT 0,
            equipped_skin TEXT NOT NULL DEFAULT 'default',
            cloud_text_skin INTEGER NOT NULL DEFAULT 0,
            equipped_cloud_skin TEXT NOT NULL DEFAULT 'default',
            coin_icecream_skin INTEGER NOT NULL DEFAULT 0,
            equipped_coin_skin TEXT NOT NULL DEFAULT 'default'
        );
        """
    )
    for column_sql in (
        "ALTER TABLE player_state ADD COLUMN magnet INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN skin_blue INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN skin_golden INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN skin_night INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN skin_runner INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN equipped_skin TEXT NOT NULL DEFAULT 'default'",
        "ALTER TABLE player_state ADD COLUMN cloud_text_skin INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN equipped_cloud_skin TEXT NOT NULL DEFAULT 'default'",
        "ALTER TABLE player_state ADD COLUMN coin_icecream_skin INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE player_state ADD COLUMN equipped_coin_skin TEXT NOT NULL DEFAULT 'default'",
    ):
        try:
            cursor.execute(column_sql)
        except sqlite3.OperationalError:
            # 字段已存在时 SQLite 会抛出 OperationalError；这是旧存档迁移的预期情况。
            pass
    cursor.execute(
        """
        INSERT OR IGNORE INTO player_state (id, coins, jump_boost, slow_start, magnet,
                                            skin_blue, skin_golden, skin_night, skin_runner,
                                            equipped_skin, cloud_text_skin, equipped_cloud_skin,
                                            coin_icecream_skin, equipped_coin_skin)
        VALUES (1, 0, 0, 0, 0, 0, 0, 0, 0, 'default', 0, 'default', 0, 'default');
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
                   skin_blue, skin_golden, skin_night, skin_runner,
                   equipped_skin, cloud_text_skin, equipped_cloud_skin,
                   coin_icecream_skin, equipped_coin_skin
            FROM player_state WHERE id = 1;
            """
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                """
                INSERT INTO player_state (id, coins, jump_boost, slow_start, magnet,
                                          skin_blue, skin_golden, skin_night, skin_runner,
                                          equipped_skin, cloud_text_skin, equipped_cloud_skin,
                                          coin_icecream_skin, equipped_coin_skin)
                VALUES (1, 0, 0, 0, 0, 0, 0, 0, 0, 'default', 0, 'default', 0, 'default');
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
            skin_runner,
            equipped_skin,
            cloud_text_skin,
            equipped_cloud_skin,
            coin_icecream_skin,
            equipped_coin_skin,
        ) = row
        upgrades['jump_boost'] = int(jump_boost)
        upgrades['slow_start'] = int(slow_start)
        upgrades['magnet'] = int(magnet)
        upgrades['skin_blue'] = int(skin_blue)
        upgrades['skin_golden'] = int(skin_golden)
        upgrades['skin_night'] = int(skin_night)
        upgrades['skin_runner'] = int(skin_runner)
        upgrades['equipped_skin'] = equipped_skin if equipped_skin in ('default', 'blue', 'golden', 'night', 'runner') else 'default'
        upgrades['cloud_text_skin'] = int(cloud_text_skin)
        upgrades['equipped_cloud_skin'] = equipped_cloud_skin if equipped_cloud_skin in ('default', 'text_cloud') else 'default'
        upgrades['coin_icecream_skin'] = int(coin_icecream_skin)
        upgrades['equipped_coin_skin'] = equipped_coin_skin if equipped_coin_skin in ('default', 'icecream') else 'default'
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
                skin_blue = ?, skin_golden = ?, skin_night = ?, skin_runner = ?,
                equipped_skin = ?, cloud_text_skin = ?, equipped_cloud_skin = ?,
                coin_icecream_skin = ?, equipped_coin_skin = ?
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
                int(upgrades.get('skin_runner', 0)),
                upgrades.get('equipped_skin', 'default'),
                int(upgrades.get('cloud_text_skin', 0)),
                upgrades.get('equipped_cloud_skin', 'default'),
                int(upgrades.get('coin_icecream_skin', 0)),
                upgrades.get('equipped_coin_skin', 'default'),
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
            (int(time.time() * 1000), score)
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
    return min(core.MAX_GAME_SPEED, base_speed + score // SPEED_SCORE_STEP)


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
    """分数越高障碍物间隔逐步缩短，但保留安全反应空间。"""
    difficulty_level = min(5, score // 500)
    min_gap = max(MIN_OBSTACLE_GAP, BASE_MIN_OBSTACLE_GAP - difficulty_level * 5)
    max_gap = max(MIN_MAX_OBSTACLE_GAP, BASE_MAX_OBSTACLE_GAP - difficulty_level * 8)
    return random.randint(min_gap, max_gap)


def ptera_spawn_probability(score):
    """翼龙在开局后才加入，并随分数小幅提高出现概率。"""
    if score < 300:
        return 0.0
    if score < 800:
        return 0.15
    return 0.25


def add_fair_obstacle(cactus_sprites_group, ptera_sprites_group, score, current_speed):
    """按当前难度生成一个公平障碍，限制同屏数量并同步当前速度。"""
    total_obstacles = len(cactus_sprites_group) + len(ptera_sprites_group)
    if total_obstacles >= MAX_OBSTACLES_ON_SCREEN:
        return

    x = core.SCREENSIZE[0] + random.randint(80, 180)
    if random.random() < ptera_spawn_probability(score):
        ptera_y = random.choice((core.GROUND_Y - 75, core.GROUND_Y - 130))
        ptera_sprites_group.add(
            Ptera(core.IMAGE_PATHS['ptera'], position=(x, ptera_y), speed=current_speed)
        )
    else:
        cactus_sprites_group.add(
            Cactus(core.IMAGE_PATHS['cacti'], position=(x, core.GROUND_Y), speed=current_speed)
        )


def apply_coin_magnet(dino, coin_sprites_group):
    """拥有金币磁铁升级后，把附近金币拉向恐龙。"""
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
    """创建默认可缩放窗口，优先用 SDL 缩放降低每帧 CPU 压力。"""
    flags = pygame.RESIZABLE
    if core.USE_SDL_SCALED:
        flags |= pygame.SCALED
    try:
        return pygame.display.set_mode(core.LOGICAL_SIZE, flags)
    except pygame.error as e:
        print(f"[PERF] pygame.SCALED 不可用，回退到手动 scale: {e}")
        core.USE_SDL_SCALED = False
        return pygame.display.set_mode(core.WINDOW_SIZE, pygame.RESIZABLE)


def draw_hud(game_surface, font, coins, highest_score, score):
    """在固定逻辑画布内绘制稳定的中文 HUD。"""
    margin = 50
    hud_y = 80
    score_y = 120

    safe_coins = max(0, min(int(coins), 99999))
    safe_highest = max(0, min(int(highest_score), 99999))
    safe_score = max(0, min(int(score), 99999))

    coin_surface = font.render(f"金币 {safe_coins:05d}", True, core.BLACK)
    coin_rect = coin_surface.get_rect(topleft=(margin, hud_y))

    hi_surface = font.render(f"最高 {safe_highest:05d}", True, core.BLACK)
    hi_rect = hi_surface.get_rect(topright=(core.LOGICAL_SIZE[0] - margin, hud_y))

    score_surface = font.render(f"分数 {safe_score:05d}", True, core.BLACK)
    score_rect = score_surface.get_rect(
        topright=(core.LOGICAL_SIZE[0] - margin, score_y)
    )

    game_surface.blit(coin_surface, coin_rect)
    game_surface.blit(hi_surface, hi_rect)
    game_surface.blit(score_surface, score_rect)



class PerfMonitor:
    """Low-frequency FPS logger; avoids spamming stdout."""

    def __init__(self, label):
        self.label = label
        self.last_log = time.monotonic()

    def tick(self, clock, state=None):
        now = time.monotonic()
        if now - self.last_log < 2.0:
            return
        self.last_log = now
        fps = clock.get_fps()
        parts = [f"[PERF] {self.label} fps={fps:.1f}"]
        if state is not None:
            counts = {
                'clouds': len(state.get('clouds', ())),
                'coins': len(state.get('coins', ())),
                'cactus': len(state.get('cacti', ())),
                'ptera': len(state.get('pteras', ())),
            }
            if fps < 30:
                parts.extend(f"{key}={value}" for key, value in counts.items())
            else:
                parts.append(f"sprites={sum(counts.values()) + 2}")
        print(' '.join(parts))


class TextLinesCache:
    """Cache groups of rendered text lines until their content changes."""

    def __init__(self, font, color=core.BLACK):
        self.font = font
        self.color = color
        self.key = None
        self.items = []

    def draw(self, surface, lines, x, y, line_gap):
        key = tuple(lines)
        if key != self.key:
            self.key = key
            self.items = [self.font.render(line, True, self.color) for line in lines]
        for idx, item in enumerate(self.items):
            surface.blit(item, (x, y + idx * line_gap))


class HUDCache:
    """Cache HUD text surfaces and only re-render when numbers change."""

    def __init__(self, font):
        self.font = font
        self.values = {}
        self.surfaces = {}

    def _surface(self, key, text, value):
        if self.values.get(key) != value:
            self.values[key] = value
            self.surfaces[key] = self.font.render(text, True, core.BLACK)
        return self.surfaces[key]

    def draw(self, game_surface, coins, highest_score, score):
        margin = 50
        hud_y = 80
        score_y = 120

        safe_coins = max(0, min(int(coins), 99999))
        safe_highest = max(0, min(int(highest_score), 99999))
        safe_score = max(0, min(int(score), 99999))

        coin_surface = self._surface('coins', f"金币 {safe_coins:05d}", safe_coins)
        hi_surface = self._surface('highest', f"最高 {safe_highest:05d}", safe_highest)
        score_surface = self._surface('score', f"分数 {safe_score:05d}", safe_score)

        game_surface.blit(coin_surface, coin_surface.get_rect(topleft=(margin, hud_y)))
        game_surface.blit(hi_surface, hi_surface.get_rect(topright=(core.LOGICAL_SIZE[0] - margin, hud_y)))
        game_surface.blit(score_surface, score_surface.get_rect(topright=(core.LOGICAL_SIZE[0] - margin, score_y)))



class SilentSound:
    def play(self):
        pass


def make_silent_sounds():
    return {key: SilentSound() for key in ('die', 'jump', 'point', 'button')}


def create_game_objects(upgrades):
    dino = Dinosaur(
        core.IMAGE_PATHS['dino'],
        position=(40, core.GROUND_Y),
        skin=upgrades.get('equipped_skin', 'default'),
    )
    if upgrades.get('jump_boost', 0):
        dino.speed = 21
    return {
        'score': 0,
        'score_timer': 0,
        'add_obstacle_timer': 0,
        'next_obstacle_gap': next_obstacle_interval(0),
        'add_coin_timer': 0,
        'next_coin_gap': random.randint(100, 180),
        'avoided_count': 0,
        'dino': dino,
        'ground': Ground(core.IMAGE_PATHS['ground'], position=(0, core.GROUND_Y)),
        'clouds': pygame.sprite.Group(),
        'cacti': pygame.sprite.Group(),
        'pteras': pygame.sprite.Group(),
        'coins': pygame.sprite.Group(),
    }


def nearest_obstacle(dino, cactus_sprites_group, ptera_sprites_group):
    obstacles = [
        obstacle for obstacle in list(cactus_sprites_group) + list(ptera_sprites_group)
        if obstacle.rect.right >= dino.rect.left
    ]
    if not obstacles:
        return None
    return min(obstacles, key=lambda obstacle: obstacle.rect.left - dino.rect.left)


def obstacle_kind_and_height(obstacle):
    if obstacle is None:
        return 0, 0
    if isinstance(obstacle, Cactus):
        return 1, 0
    if obstacle.rect.centery >= core.GROUND_Y - 85:
        return 2, 1
    return 2, 2


def get_rl_state(dino, cactus_sprites_group, ptera_sprites_group, current_speed):
    obstacle = nearest_obstacle(dino, cactus_sprites_group, ptera_sprites_group)
    if obstacle is None:
        distance_bin = 20
    else:
        distance = max(0, obstacle.rect.left - dino.rect.right)
        distance_bin = max(0, min(20, int(distance / 50)))
    obstacle_type, obstacle_height_bin = obstacle_kind_and_height(obstacle)
    speed_bin = int(current_speed)
    if dino.is_jumping:
        dino_state = 1
    elif dino.is_ducking:
        dino_state = 2
    else:
        dino_state = 0
    return (distance_bin, obstacle_type, obstacle_height_bin, speed_bin, dino_state)


def apply_ai_action(dino, action, sounds):
    if action == 1:
        dino.unduck()
        dino.jump(sounds)
    elif action == 2:
        dino.duck()
    else:
        dino.unduck()


def count_avoided_obstacles(dino, cactus_sprites_group, ptera_sprites_group):
    avoided = 0
    for obstacle in list(cactus_sprites_group) + list(ptera_sprites_group):
        if not getattr(obstacle, 'counted', False) and obstacle.rect.right < dino.rect.left and not dino.is_dead:
            obstacle.counted = True
            avoided += 1
    return avoided


def update_world(state, upgrades, sounds, current_speed, collect_coins=True):
    score = state['score']
    state['score_timer'] += 1
    if state['score_timer'] > 10:
        state['score_timer'] = 0
        state['score'] += 1
        score = state['score']
        if sounds and score % 100 == 0:
            sounds['point'].play()

    apply_speed_to_sprites(
        current_speed,
        state['ground'],
        state['cacti'],
        state['pteras'],
        state['coins'],
    )

    if len(state['clouds']) < 5 and random.randint(0, 600) == 1:
        state['clouds'].add(Cloud(core.IMAGE_PATHS['cloud'], position=(core.SCREENSIZE[0] + random.randint(80, 180), random.randint(50, 200)), skin=upgrades.get('equipped_cloud_skin', 'default')))

    state['add_obstacle_timer'] += 1
    if state['add_obstacle_timer'] > state['next_obstacle_gap']:
        state['add_obstacle_timer'] = 0
        state['next_obstacle_gap'] = next_obstacle_interval(score)
        add_fair_obstacle(state['cacti'], state['pteras'], score, current_speed)

    state['add_coin_timer'] += 1
    if len(state['coins']) < 6 and state['add_coin_timer'] > state['next_coin_gap']:
        state['add_coin_timer'] = 0
        state['next_coin_gap'] = random.randint(100, 190)
        coin_y = random.choice([core.GROUND_Y - 35, core.GROUND_Y - 75, core.GROUND_Y - 110])
        state['coins'].add(Coin(position=(core.SCREENSIZE[0] + random.randint(70, 170), coin_y), speed=current_speed, skin=upgrades.get('equipped_coin_skin', 'default')))

    dino = state['dino']
    dino.update()
    state['ground'].update()
    state['clouds'].update()
    state['cacti'].update()
    state['pteras'].update()
    state['coins'].update()
    if upgrades.get('magnet', 0):
        apply_coin_magnet(dino, state['coins'])

    hit_cactus = any(
        pygame.sprite.collide_mask(dino, cactus) for cactus in state['cacti']
    )
    hit_ptera = any(
        pygame.sprite.collide_mask(dino, ptera) for ptera in state['pteras']
    )
    if hit_cactus or hit_ptera:
        dino.die(sounds)

    avoided_now = count_avoided_obstacles(dino, state['cacti'], state['pteras'])
    state['avoided_count'] += avoided_now

    collected_now = 0
    if collect_coins:
        for coin in list(state['coins']):
            if pygame.sprite.collide_mask(dino, coin):
                coin.kill()
                collected_now += 1
        if collected_now and sounds:
            sounds['point'].play()

    return avoided_now, collected_now


def draw_world(game_surface, state, hud_cache, coins, highest_score, ai_demo=False, model_loaded=True, agent=None, ai_text_cache=None):
    game_surface.fill(core.BACKGROUND_COLOR)
    state['clouds'].draw(game_surface)
    state['ground'].draw(game_surface)
    state['cacti'].draw(game_surface)
    state['pteras'].draw(game_surface)
    state['coins'].draw(game_surface)
    state['dino'].draw(game_surface)
    hud_cache.draw(game_surface, coins, highest_score, state['score'])
    if ai_demo:
        lines = ['AI演示模式', f"本局躲避：{min(state['avoided_count'], 999):03d}"]
        if model_loaded and agent is not None:
            lines.extend([
                f"累计训练：{agent.training_episodes}轮",
                f"历史最高躲避：{agent.best_avoided}",
            ])
        else:
            lines.append('尚未训练AI，请先按 T 训练')
        if ai_text_cache is None:
            ai_text_cache = TextLinesCache(core.get_font(25))
        ai_text_cache.draw(game_surface, lines, 50, 160, 34)

def load_sounds():
    """Load each sound once at startup instead of once per game round."""
    return {key: pygame.mixer.Sound(path) for key, path in core.AUDIO_PATHS.items()}


def warm_asset_caches(screen):
    """Preload and cache image processing once so gameplay frames never do it."""
    print('正在加载资源...')

    def load_fonts():
        for size in (22, 24, 25, 26, 28, 30, 48, 52, 56, 60):
            core.get_font(size)

    def load_default_images():
        Ground._get_image(core.IMAGE_PATHS['ground'])
        Cloud._default_image(core.IMAGE_PATHS['cloud'])
        Cactus._get_images(core.IMAGE_PATHS['cacti'], (118, 82))
        Ptera._get_images(core.IMAGE_PATHS['ptera'], 70)
        Coin._get_fallback_image(14)
        for skin in ('default', 'blue', 'golden', 'night'):
            Dinosaur._get_images(core.IMAGE_PATHS['dino'], (110, 78), skin)

    def load_custom_scene_assets():
        try:
            Cloud._get_image(core.IMAGE_PATHS['cloud'], 'text_cloud')
        except Exception as e:
            print(f'文字云朵预加载失败: {e}')
        try:
            Coin._get_image(14, 'icecream')
        except Exception as e:
            print(f'雪糕金币预加载失败: {e}')

    def load_runner_skin():
        try:
            Dinosaur._get_images(core.IMAGE_PATHS['dino'], (110, 78), 'runner')
        except Exception as e:
            print(f'奔跑人物预加载失败: {e}')

    screen = loading_step(screen, '正在加载字体...', load_fonts)
    screen = loading_step(screen, '正在加载图片...', load_default_images)
    screen = loading_step(screen, '正在处理皮肤...', load_custom_scene_assets)
    screen = loading_step(screen, '正在处理奔跑人物皮肤...', load_runner_skin)
    print('资源加载完成')
    return screen


def ai_end_interface(screen, game_surface, avoided_count):
    font_title = core.get_font(52)
    font_mid = core.get_font(30)
    end_surface = pygame.Surface(core.LOGICAL_SIZE)
    end_surface.fill((255, 255, 255))
    lines = [
        (font_title, 'AI演示结束', 150),
        (font_mid, f'躲避障碍：{avoided_count}', 250),
        (font_mid, '按 A 再试一次', 335),
        (font_mid, '按 T 继续训练AI', 385),
        (font_mid, '按 ESC 返回', 435),
    ]
    for font, text, y in lines:
        surface = font.render(text, True, core.BLACK)
        end_surface.blit(surface, surface.get_rect(center=(core.LOGICAL_SIZE[0] // 2, y)))

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.VIDEORESIZE:
                screen = core.resize_screen(event.size)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    return 'retry'
                if event.key == pygame.K_t:
                    return 'train'
                if event.key == pygame.K_ESCAPE:
                    return 'back'
        game_surface.blit(end_surface, (0, 0))
        core.blit_scaled(game_surface, screen)
        clock.tick(core.FPS)


def run_ai_demo(screen, highest_score, coins, upgrades, sounds):
    game_surface = pygame.Surface(core.LOGICAL_SIZE)
    agent = QLearningAgent(epsilon=0.0)
    model_loaded = agent.load(Q_TABLE_PATH)
    agent.epsilon = 0.0
    state = create_game_objects(upgrades)
    clock = pygame.time.Clock()
    hud_cache = HUDCache(core.get_font(28))
    ai_text_cache = TextLinesCache(core.get_font(25))
    perf = PerfMonitor('ai_demo')

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit', coins
            if event.type == pygame.VIDEORESIZE:
                screen = core.resize_screen(event.size)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'back', coins
                if event.key == pygame.K_t and not model_loaded:
                    return 'train', coins

        current_speed = get_current_speed(state['score'], upgrades)
        rl_state = get_rl_state(state['dino'], state['cacti'], state['pteras'], current_speed)
        action = agent.choose_action(rl_state, training=False) if model_loaded else 0
        apply_ai_action(state['dino'], action, sounds)
        _, collected_now = update_world(state, upgrades, sounds, current_speed)
        coins += collected_now
        draw_world(game_surface, state, hud_cache, coins, highest_score, ai_demo=True, model_loaded=model_loaded, agent=agent, ai_text_cache=ai_text_cache)
        core.blit_scaled(game_surface, screen)
        clock.tick(core.FPS)
        perf.tick(clock, state)

        if state['dino'].is_dead:
            while True:
                end_action = ai_end_interface(screen, game_surface, state['avoided_count'])
                screen = pygame.display.get_surface() or screen
                if end_action == 'retry':
                    return 'retry', coins
                if end_action == 'train':
                    return 'train', coins
                return end_action, coins


def render_training_status(
    screen,
    game_surface,
    episode,
    episodes,
    cumulative_episodes,
    historical_best_avoided,
    session_best_avoided,
    average_score,
    epsilon,
    finished=False,
    session_best_score=0,
):
    game_surface.fill((255, 255, 255))
    title_font = core.get_font(48)
    font = core.get_font(26)
    title = '训练完成' if finished else 'AI训练中'
    if finished:
        lines = [
            (title_font, title, 105),
            (font, f'本次训练轮数：{episode}', 185),
            (font, f'累计训练轮数：{cumulative_episodes}', 230),
            (font, f'本次最高躲避：{session_best_avoided}', 275),
            (font, f'历史最高躲避：{historical_best_avoided}', 320),
            (font, f'本次最高分：{session_best_score}', 365),
            (font, 'Q表已保存', 420),
            (font, '按 A 演示AI    按 T 继续训练', 470),
            (font, '按 ESC 返回', 515),
        ]
    else:
        lines = [
            (title_font, title, 110),
            (font, f'本次训练：第 {episode} / {episodes} 轮', 205),
            (font, f'累计训练：{cumulative_episodes} 轮', 255),
            (font, f'历史最高躲避：{historical_best_avoided}', 305),
            (font, f'本次最高躲避：{session_best_avoided}', 355),
            (font, f'当前探索率：{epsilon:.3f}', 405),
            (font, f'平均得分：{average_score:.1f}', 455),
            (font, '按 ESC 停止训练并保存', 510),
        ]
    for font_obj, text, y in lines:
        surface = font_obj.render(text, True, core.BLACK)
        game_surface.blit(surface, surface.get_rect(center=(core.LOGICAL_SIZE[0] // 2, y)))
    core.blit_scaled(game_surface, screen)


def reset_ai_training():
    """只重置强化学习 Q 表，不触碰金币、商城、皮肤或 history.db。"""
    if os.path.exists(Q_TABLE_PATH):
        os.remove(Q_TABLE_PATH)
    print('已重置AI训练数据，仅删除 rl_q_table.json')


def clear_game_save(conn):
    """清空最高分和玩家状态，但保留数据库表结构。"""
    upgrades = _default_upgrades()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM record;")
    cursor.execute(
        """
        UPDATE player_state
        SET coins = 0, jump_boost = 0, slow_start = 0, magnet = 0,
            skin_blue = 0, skin_golden = 0, skin_night = 0, skin_runner = 0,
            equipped_skin = 'default', cloud_text_skin = 0, equipped_cloud_skin = 'default',
            coin_icecream_skin = 0, equipped_coin_skin = 'default'
        WHERE id = 1;
        """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO player_state (id, coins, jump_boost, slow_start, magnet,
                                            skin_blue, skin_golden, skin_night, skin_runner,
                                            equipped_skin, cloud_text_skin, equipped_cloud_skin,
                                            coin_icecream_skin, equipped_coin_skin)
        VALUES (1, 0, 0, 0, 0, 0, 0, 0, 0, 'default', 0, 'default', 0, 'default');
        """
    )
    conn.commit()
    print('已清除游戏存档：最高分、金币、升级和皮肤已重置')
    return 0, 0, upgrades


def _draw_clear_save_page(game_surface, title_font, font, small_font, confirm_choice=None, done_message=None):
    game_surface.fill((255, 255, 255))
    width = core.LOGICAL_SIZE[0]
    title = title_font.render('清除存档', True, core.BLACK)
    game_surface.blit(title, title.get_rect(center=(width // 2, 72)))

    if done_message:
        lines = [done_message, '按 ESC 返回开始界面']
        y = 245
        for line in lines:
            surface = font.render(line, True, core.BLACK)
            game_surface.blit(surface, surface.get_rect(center=(width // 2, y)))
            y += 58
        return

    if confirm_choice:
        lines = [f'即将{confirm_choice}', '确定要清除吗？', '按 Y 确认', '按 N 取消']
        y = 185
        for line in lines:
            surface = font.render(line, True, core.BLACK)
            game_surface.blit(surface, surface.get_rect(center=(width // 2, y)))
            y += 55
        return

    lines = [
        (font, '请选择要清除的内容：', 135),
        (font, '[1] 清除游戏存档', 205),
        (small_font, '包括金币、商城购买、皮肤、最高分', 245),
        (font, '[2] 清除 AI 训练数据', 320),
        (small_font, '包括强化学习 Q 表', 360),
        (font, '[3] 清除全部存档', 435),
        (small_font, '包括游戏存档和 AI 训练数据', 475),
        (small_font, '按 ESC 返回', 545),
    ]
    for font_obj, text, y in lines:
        surface = font_obj.render(text, True, core.BLACK)
        game_surface.blit(surface, surface.get_rect(center=(width // 2, y)))


def ClearSaveInterface(screen, game_surface, conn):
    """带二次确认的清除存档界面。"""
    title_font = core.get_font(52)
    font = core.get_font(30)
    small_font = core.get_font(24)
    clock = pygame.time.Clock()
    pending_choice = None
    done_message = None
    result_state = {'action': 'back'}
    choices = {
        pygame.K_1: ('game', '清除游戏存档'),
        pygame.K_2: ('ai', '清除 AI 训练数据'),
        pygame.K_3: ('all', '清除全部存档'),
    }

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return {'action': 'quit'}
            if event.type == pygame.VIDEORESIZE:
                screen = core.resize_screen(event.size)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return result_state if done_message else {'action': 'back'}
                if done_message:
                    continue
                if pending_choice:
                    if event.key == pygame.K_n:
                        pending_choice = None
                    elif event.key == pygame.K_y:
                        result = {'action': 'cleared'}
                        if pending_choice[0] in ('game', 'all'):
                            highest_score, coins, upgrades = clear_game_save(conn)
                            result.update({'highest_score': highest_score, 'coins': coins, 'upgrades': upgrades})
                        if pending_choice[0] in ('ai', 'all'):
                            reset_ai_training()
                            result['ai_cleared'] = True
                        done_message = '存档已清除'
                        pending_choice = None
                        result['done_message'] = done_message
                        result_state = result
                    continue
                if event.key in choices:
                    pending_choice = choices[event.key]

        _draw_clear_save_page(
            game_surface,
            title_font,
            font,
            small_font,
            confirm_choice=pending_choice[1] if pending_choice else None,
            done_message=done_message,
        )
        core.blit_scaled(game_surface, screen)
        clock.tick(core.FPS)



def train_ai(screen, upgrades, sounds, episodes=300, max_steps=5000, reset_training=False):
    game_surface = pygame.Surface(core.LOGICAL_SIZE)
    if reset_training:
        reset_ai_training()
    agent = QLearningAgent(epsilon=0.35, epsilon_decay=0.988, min_epsilon=0.05)
    loaded_history = agent.load(Q_TABLE_PATH)
    train_sounds = make_silent_sounds()
    clock = pygame.time.Clock()
    scores = []
    session_best_avoided = 0
    session_best_score = 0
    stopped = False

    if loaded_history:
        render_training_status(
            screen,
            game_surface,
            0,
            episodes,
            agent.training_episodes,
            agent.best_avoided,
            session_best_avoided,
            0,
            agent.epsilon,
        )
        pygame.time.wait(250)

    completed_episodes = 0
    for episode in range(1, episodes + 1):
        state = create_game_objects(upgrades)
        for step in range(max_steps):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    session_metadata = {
                        'session_episodes': completed_episodes,
                        'session_best_avoided': session_best_avoided,
                        'session_best_score': session_best_score,
                        'session_average_score': sum(scores) / len(scores) if scores else 0,
                    }
                    agent.save(Q_TABLE_PATH, session_metadata)
                    return {'episodes': completed_episodes, 'best_avoided': session_best_avoided, 'average_score': session_metadata['session_average_score'], 'quit': True}
                if event.type == pygame.VIDEORESIZE:
                    screen = core.resize_screen(event.size)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    stopped = True
            if stopped:
                break

            clock.tick(240)
            current_speed = get_current_speed(state['score'], upgrades)
            old_state = get_rl_state(state['dino'], state['cacti'], state['pteras'], current_speed)
            action = agent.choose_action(old_state, training=True)
            exploration_penalty = -0.2 if action == 1 and old_state[1] == 0 else 0.0
            apply_ai_action(state['dino'], action, train_sounds)
            avoided_now, collected_now = update_world(state, upgrades, train_sounds, current_speed, collect_coins=True)
            reward = 0.1 + avoided_now * 10 + collected_now * 2 + exploration_penalty
            done = state['dino'].is_dead
            if done:
                reward -= 100
            next_speed = get_current_speed(state['score'], upgrades)
            new_state = get_rl_state(state['dino'], state['cacti'], state['pteras'], next_speed)
            agent.update_q_value(old_state, action, reward, new_state, done=done)
            if avoided_now and state['avoided_count'] > agent.best_avoided:
                agent.best_avoided = state['avoided_count']
            if done:
                break

        if stopped:
            break

        completed_episodes += 1
        scores.append(state['score'])
        session_best_avoided = max(session_best_avoided, state['avoided_count'])
        session_best_score = max(session_best_score, state['score'])
        agent.best_avoided = max(agent.best_avoided, state['avoided_count'])
        agent.best_score = max(agent.best_score, state['score'])
        agent.training_episodes += 1
        agent.decay_epsilon()
        if episode % 5 == 0 or episode == 1:
            render_training_status(
                screen,
                game_surface,
                episode,
                episodes,
                agent.training_episodes,
                agent.best_avoided,
                session_best_avoided,
                sum(scores) / len(scores),
                agent.epsilon,
            )
            clock.tick(30)

    average_score = sum(scores) / completed_episodes if completed_episodes else 0
    session_metadata = {
        'session_episodes': completed_episodes,
        'session_best_avoided': session_best_avoided,
        'session_best_score': session_best_score,
        'session_average_score': average_score,
    }
    agent.save(Q_TABLE_PATH, session_metadata)
    if stopped:
        return {
            'episodes': completed_episodes,
            'best_avoided': session_best_avoided,
            'average_score': average_score,
            'quit': False,
            'action': 'back',
        }
    render_training_status(
        screen,
        game_surface,
        completed_episodes,
        episodes,
        agent.training_episodes,
        agent.best_avoided,
        session_best_avoided,
        average_score,
        agent.epsilon,
        finished=True,
        session_best_score=session_best_score,
    )
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return {'episodes': completed_episodes, 'best_avoided': session_best_avoided, 'average_score': average_score, 'quit': True}
            if event.type == pygame.VIDEORESIZE:
                screen = core.resize_screen(event.size)
                render_training_status(
                    screen,
                    game_surface,
                    completed_episodes,
                    episodes,
                    agent.training_episodes,
                    agent.best_avoided,
                    session_best_avoided,
                    average_score,
                    agent.epsilon,
                    finished=True,
                    session_best_score=session_best_score,
                )
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    return {'episodes': completed_episodes, 'best_avoided': session_best_avoided, 'average_score': average_score, 'quit': False, 'action': 'ai_demo'}
                if event.key == pygame.K_t:
                    return {'episodes': completed_episodes, 'best_avoided': session_best_avoided, 'average_score': average_score, 'quit': False, 'action': 'train'}
                if event.key == pygame.K_ESCAPE:
                    return {'episodes': completed_episodes, 'best_avoided': session_best_avoided, 'average_score': average_score, 'quit': False, 'action': 'back'}
        clock.tick(core.FPS)

def main(screen, conn, highest_score, coins, upgrades, sounds):
    """
    游戏主函数

    Args:
        screen: 程序启动时创建的 Pygame 真实窗口对象
        conn: SQLite 数据库连接
        highest_score (int): 历史最高分
        coins (int): 玩家持有金币
        upgrades (dict): 已购买升级

    Returns:
        tuple: (是否继续游戏, 当前最高分, 当前金币, 当前升级)
    """
    game_surface = pygame.Surface(core.LOGICAL_SIZE)
    pygame.display.set_caption('像素恐龙快跑')

    while True:
        start_action = GameStartInterface(screen, game_surface, sounds, core, coins, upgrades.get('equipped_skin', 'default'))
        screen = pygame.display.get_surface() or screen
        if start_action == 'start':
            break
        if start_action == 'ai_demo':
            while True:
                demo_action, coins = run_ai_demo(screen, highest_score, coins, upgrades, sounds)
                save_player_state(conn, coins, upgrades)
                screen = pygame.display.get_surface() or screen
                if demo_action == 'retry':
                    continue
                if demo_action == 'train':
                    while True:
                        result = train_ai(screen, upgrades, sounds)
                        screen = pygame.display.get_surface() or screen
                        if result.get('quit'):
                            return False, highest_score, coins, upgrades
                        if result.get('action') == 'train':
                            continue
                        break
                    if result.get('action') == 'ai_demo':
                        continue
                    break
                if demo_action == 'quit':
                    return False, highest_score, coins, upgrades
                break
            continue
        if start_action == 'ai_train':
            while True:
                result = train_ai(screen, upgrades, sounds)
                screen = pygame.display.get_surface() or screen
                if result.get('quit'):
                    return False, highest_score, coins, upgrades
                if result.get('action') == 'train':
                    continue
                if result.get('action') == 'ai_demo':
                    demo_action, coins = run_ai_demo(screen, highest_score, coins, upgrades, sounds)
                    save_player_state(conn, coins, upgrades)
                    screen = pygame.display.get_surface() or screen
                    if demo_action == 'train':
                        continue
                    if demo_action == 'quit':
                        return False, highest_score, coins, upgrades
                break
            continue
        if start_action == 'ai_reset':
            reset_ai_training()
            continue
        if start_action == 'clear_save':
            clear_result = ClearSaveInterface(screen, game_surface, conn)
            screen = pygame.display.get_surface() or screen
            if clear_result.get('action') == 'quit':
                return False, highest_score, coins, upgrades
            if clear_result.get('action') == 'cleared':
                if 'coins' in clear_result:
                    coins = clear_result['coins']
                if 'highest_score' in clear_result:
                    highest_score = clear_result['highest_score']
                if 'upgrades' in clear_result:
                    upgrades = clear_result['upgrades']
            continue
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
    hud_cache = HUDCache(core.get_font(28))
    perf = PerfMonitor('game')
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
            cloud = Cloud(core.IMAGE_PATHS['cloud'], position=(x, y), skin=upgrades.get('equipped_cloud_skin', 'default'))
            cloud_sprites_group.add(cloud)

        add_obstacle_timer += 1
        if add_obstacle_timer > next_obstacle_gap:
            add_obstacle_timer = 0
            next_obstacle_gap = next_obstacle_interval(score)
            add_fair_obstacle(
                cactus_sprites_group,
                ptera_sprites_group,
                score,
                current_speed,
            )

        add_coin_timer += 1
        if len(coin_sprites_group) < 6 and add_coin_timer > next_coin_gap:
            add_coin_timer = 0
            next_coin_gap = random.randint(100, 190)
            x = core.SCREENSIZE[0] + random.randint(70, 170)
            coin_y = random.choice([
                core.GROUND_Y - 35,
                core.GROUND_Y - 75,
                core.GROUND_Y - 110,
            ])
            coin_sprites_group.add(Coin(position=(x, coin_y), speed=current_speed, skin=upgrades.get('equipped_coin_skin', 'default')))

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

        collected_count = 0
        for coin in list(coin_sprites_group):
            if pygame.sprite.collide_mask(dino, coin):
                coin.kill()
                collected_count += 1
        if collected_count:
            coins += collected_count
            sounds['point'].play()

        cloud_sprites_group.draw(game_surface)
        ground.draw(game_surface)
        cactus_sprites_group.draw(game_surface)
        ptera_sprites_group.draw(game_surface)
        coin_sprites_group.draw(game_surface)
        dino.draw(game_surface)

        hud_cache.draw(game_surface, coins, highest_score, score)

        core.blit_scaled(game_surface, screen)
        clock.tick(core.FPS)
        perf.tick(clock, {
            'clouds': cloud_sprites_group,
            'coins': coin_sprites_group,
            'cacti': cactus_sprites_group,
            'pteras': ptera_sprites_group,
        })

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
    pygame.init()
    screen = create_screen()
    pygame.display.set_caption('像素恐龙快跑')
    conn = None
    try:
        screen, running = draw_loading_screen(screen, '资源加载中...')
        if not running:
            raise SystemExit

        screen = warm_asset_caches(screen)
        sounds_box = {}
        screen = loading_step(screen, '正在加载音效...', lambda: sounds_box.update({'sounds': load_sounds()}))
        sounds = sounds_box['sounds']

        db_box = {}
        screen = loading_step(screen, '正在读取存档...', lambda: db_box.update({'data': init_database()}))
        conn, highest_score, coins, upgrades = db_box['data']
        screen = loading_step(screen, '正在检查AI训练数据...', lambda: os.path.exists(Q_TABLE_PATH))
        draw_loading_screen(screen, '加载完成')

        while True:
            flag, highest_score, coins, upgrades = main(screen, conn, highest_score, coins, upgrades, sounds)
            screen = pygame.display.get_surface() or screen
            if not flag:
                save_player_state(conn, coins, upgrades)
                break
    except SystemExit:
        pass
    finally:
        if conn is not None:
            conn.close()
        pygame.quit()
