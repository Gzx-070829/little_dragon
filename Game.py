import core
import sys
import time
import random
import pygame
import sqlite3
from modules import *

def main(highest_score):
    """
    游戏主函数

    Args:
        highest_score (int): 历史最高分

    Returns:
        tuple: (是否继续游戏, 当前最高分)
    """
    # 1. 初始化Pygame和游戏窗口
    pygame.init()
    screen = pygame.display.set_mode(core.SCREENSIZE)
    pygame.display.set_caption('Dino Rush')

    # 2. 加载所有音效文件
    sounds = {}
    for key, path in core.AUDIO_PATHS.items():
        sounds[key] = pygame.mixer.Sound(path)

    # 3. 显示游戏开始界面
    GameStartInterface(screen, sounds, core)

    # 4. 初始化游戏对象
    score = 0
    dino = Dinosaur(core.IMAGE_PATHS['dino'])
    # ground = Ground(core.IMAGE_PATHS['ground'], position=(0, core.SCREENSIZE[1]-400))
    # 获取屏幕尺寸
    screen_width, screen_height = core.SCREENSIZE

    # 直接用路径创建，让 Ground 内部自己缩放
    ground = Ground(
        core.IMAGE_PATHS['ground'],  # 传路径，不要传图片！
        position=(0, screen_height - 50)
    )


    # 5. 创建精灵组
    cloud_sprites_group = pygame.sprite.Group()
    cactus_sprites_group = pygame.sprite.Group()
    ptera_sprites_group = pygame.sprite.Group()

    # 游戏计时器
    add_obstacle_timer = 0
    score_timer = 0
    clock = pygame.time.Clock()

    # 游戏速度
    game_speed = 10

    # 6. 游戏主循环
    while True:
        # ============== 1. 事件处理 ==============
        for event in pygame.event.get():
            # 退出游戏
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 按键按下
            if event.type == pygame.KEYDOWN:
                # 跳跃
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump(sounds)
                # 下蹲
                if event.key == pygame.K_DOWN or event.key == pygame.K_LSHIFT:
                    dino.duck()

            # 松开按键取消下蹲
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN or event.key == pygame.K_LSHIFT:
                    dino.unduck()

        # ============== 2. 清空屏幕 ==============
        screen.fill(core.BACKGROUND_COLOR)

        # ============== 3. 随机生成云朵 ==============
        if len(cloud_sprites_group) < 5 and random.randint(0, 600) == 1:
            x = core.SCREENSIZE[0] + 100
            y = random.randint(50, 200)
            cloud = Cloud(core.IMAGE_PATHS['cloud'], position=(x, y))
            cloud_sprites_group.add(cloud)

        # ============== 4. 随机生成障碍物 ==============
        add_obstacle_timer += 1
        if add_obstacle_timer > random.randint(70, 150):
            add_obstacle_timer = 0
            x = core.SCREENSIZE[0] + 100
            y = ground.rect.top

            # 80% 仙人掌, 20% 翼龙
            if random.randint(0, 100) < 80:
                cactus = Cactus(core.IMAGE_PATHS['cacti'])
                cactus_sprites_group.add(cactus)
            else:
                ptera_y = random.choice([y - 60, y - 120])
                ptera = Ptera(core.IMAGE_PATHS['ptera'], position=(x, ptera_y))
                ptera_sprites_group.add(ptera)

        # ============== 5. 更新所有对象 ==============
        dino.update()
        ground.update()
        cloud_sprites_group.update()
        cactus_sprites_group.update()
        ptera_sprites_group.update()

        # ============== 6. 计分逻辑 ==============
        score_timer += 1
        if score_timer > 10:
            score_timer = 0
            score += 1
            # 每100分加分音效
            # if score % 100 == 0:
            #     sounds['score'].play()
            # 每1000分加速
            if score % 1000 == 0:
                game_speed += 1
                ground.speed = -game_speed
                for c in cactus_sprites_group: c.speed = -game_speed
                for p in ptera_sprites_group: p.speed = -game_speed

        # ============== 7. 碰撞检测 ==============
        if pygame.sprite.spritecollide(dino, cactus_sprites_group, True, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(dino, ptera_sprites_group, True, pygame.sprite.collide_mask):
            dino.die(sounds)

        # ============== 8. 绘制所有元素 ==============
        cloud_sprites_group.draw(screen)
        ground.draw(screen)
        cactus_sprites_group.draw(screen)
        ptera_sprites_group.draw(screen)
        dino.draw(screen)

        # 绘制计分板
        score_board = Scoreboard(score, core.FONT_PATHS['joystix'], (core.SCREENSIZE[0] - 150, 30))
        highest_board = Scoreboard(highest_score, core.FONT_PATHS['joystix'], (core.SCREENSIZE[0] - 350, 30), is_highest=True)
        score_board.draw(screen)
        highest_board.draw(screen)

        # ============== 9. 刷新屏幕 ==============
        pygame.display.update()
        clock.tick(core.FPS)

        # ============== 10. 游戏结束 ==============
        if dino.is_dead:
            # 保存分数到数据库
            try:
                c.execute("INSERT INTO record (unix_timestamp, score) VALUES (?, ?)", (int(time.time()), score))
                conn.commit()
            except:
                pass
            is_new_record = False
            if score > highest_score:
                highest_score = score
                is_new_record = True
            else:
                # 没破纪录 → 保持原来的最高分
                pass

            break

    # 显示游戏结束界面
    return GameEndInterface(screen, core, score, highest_score, is_new_record, sounds), highest_score


if __name__ == '__main__':
    # 数据库初始化
    # conn = sqlite3.connect('history.db')
    # c = conn.cursor()
    # c.execute("CREATE TABLE IF NOT EXISTS record (unix_timestamp INT PRIMARY KEY, score SMALLINT NOT NULL);")
    # c.execute("SELECT MAX(score) FROM record;")
    # rows = c.fetchall()
    # highest_score = 0
    # for row in rows:
    #     if row[0] is not None:
    #         highest_score = row[0]
    highest_score = 0
    try:
        conn = sqlite3.connect('history.db')
        c = conn.cursor()
        c.execute("SELECT MAX(score) FROM record;")
        max_score = c.fetchone()[0]

        if max_score is not None:
            highest_score = max_score
        conn.close()
    except:
        conn = sqlite3.connect('history.db')
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS record (unix_timestamp INT PRIMARY KEY, score SMALLINT NOT NULL);")
        c.execute("SELECT MAX(score) FROM record;")
        rows = c.fetchall()

    # 主循环
    while True:
        flag, highest_score = main(highest_score)
        if not flag:
            break

    conn.commit()
    conn.close()