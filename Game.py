import os
import random
import sqlite3
import time

import pygame

import core
from modules import *

DB_PATH = os.path.join(core.BASE_DIR, 'history.db')


def init_database():
    """初始化分数数据库并返回连接和历史最高分。"""
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
    conn.commit()

    highest_score = 0
    try:
        cursor.execute("SELECT MAX(score) FROM record;")
        max_score = cursor.fetchone()[0]
        if max_score is not None:
            highest_score = max_score
    except Exception as e:
        print(f"读取最高分失败: {e}")

    return conn, highest_score


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


def main(conn, highest_score):
    """
    游戏主函数

    Args:
        conn: SQLite 数据库连接
        highest_score (int): 历史最高分

    Returns:
        tuple: (是否继续游戏, 当前最高分)
    """
    pygame.init()
    screen = pygame.display.set_mode(core.SCREENSIZE)
    pygame.display.set_caption('Dino Rush')

    sounds = {}
    for key, path in core.AUDIO_PATHS.items():
        sounds[key] = pygame.mixer.Sound(path)

    if not GameStartInterface(screen, sounds, core):
        return False, highest_score

    score = 0
    dino = Dinosaur(core.IMAGE_PATHS['dino'])
    _, screen_height = core.SCREENSIZE
    ground = Ground(
        core.IMAGE_PATHS['ground'],
        position=(0, screen_height - 50)
    )

    cloud_sprites_group = pygame.sprite.Group()
    cactus_sprites_group = pygame.sprite.Group()
    ptera_sprites_group = pygame.sprite.Group()

    add_obstacle_timer = 0
    score_timer = 0
    clock = pygame.time.Clock()
    game_speed = 10

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, highest_score

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump(sounds)
                if event.key == pygame.K_DOWN or event.key == pygame.K_LSHIFT:
                    dino.duck()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN or event.key == pygame.K_LSHIFT:
                    dino.unduck()

        screen.fill(core.BACKGROUND_COLOR)

        if len(cloud_sprites_group) < 5 and random.randint(0, 600) == 1:
            x = core.SCREENSIZE[0] + 100
            y = random.randint(50, 200)
            cloud = Cloud(core.IMAGE_PATHS['cloud'], position=(x, y))
            cloud_sprites_group.add(cloud)

        add_obstacle_timer += 1
        if add_obstacle_timer > random.randint(70, 150):
            add_obstacle_timer = 0
            x = core.SCREENSIZE[0] + 100
            y = ground.rect.top

            if random.randint(0, 100) < 80:
                cactus = Cactus(core.IMAGE_PATHS['cacti'], position=(x, y))
                cactus.speed = -game_speed
                cactus_sprites_group.add(cactus)
            else:
                ptera_y = random.choice([y - 60, y - 120])
                ptera = Ptera(core.IMAGE_PATHS['ptera'], position=(x, ptera_y))
                ptera.speed = -game_speed
                ptera_sprites_group.add(ptera)

        dino.update()
        ground.update()
        cloud_sprites_group.update()
        cactus_sprites_group.update()
        ptera_sprites_group.update()

        score_timer += 1
        if score_timer > 10:
            score_timer = 0
            score += 1
            if score % 100 == 0:
                sounds['point'].play()
            if score % 1000 == 0:
                game_speed += 1
                ground.speed = -game_speed
                for cactus in cactus_sprites_group:
                    cactus.speed = -game_speed
                for ptera in ptera_sprites_group:
                    ptera.speed = -game_speed

        if pygame.sprite.spritecollide(dino, cactus_sprites_group, True, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(dino, ptera_sprites_group, True, pygame.sprite.collide_mask):
            dino.die(sounds)

        cloud_sprites_group.draw(screen)
        ground.draw(screen)
        cactus_sprites_group.draw(screen)
        ptera_sprites_group.draw(screen)
        dino.draw(screen)

        score_board = Scoreboard(score, core.FONT_PATHS['joystix'], (core.SCREENSIZE[0] - 150, 30))
        highest_board = Scoreboard(
            highest_score,
            core.FONT_PATHS['joystix'],
            (core.SCREENSIZE[0] - 350, 30),
            is_highest=True
        )
        score_board.draw(screen)
        highest_board.draw(screen)

        pygame.display.update()
        clock.tick(core.FPS)

        if dino.is_dead:
            save_score(conn, score)
            is_new_record = False
            if score > highest_score:
                highest_score = score
                is_new_record = True
            break

    return GameEndInterface(screen, core, score, highest_score, is_new_record, sounds), highest_score


if __name__ == '__main__':
    conn, highest_score = init_database()
    try:
        while True:
            flag, highest_score = main(conn, highest_score)
            if not flag:
                break
    finally:
        conn.close()
        pygame.quit()
