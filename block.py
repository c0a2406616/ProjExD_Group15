import os
import random
import math
import sys
import time
import pygame as pg
import pygame 

# --- 定数定義 ---
WIDTH = 1100   # 画面の幅
HEIGHT = 650   # 画面の高さ
FPS = 60       # フレームレート
PADDLE_Y_OFFSET = 50  # 下からバーを上げる量
BLOCK_ROWS = 6        # ブロックの行数
BLOCK_COLS = 10       # ブロックの列数
BLOCK_WIDTH = 100     # ブロックの幅
BLOCK_HEIGHT = 30     # ブロックの高さ
BLOCK_PADDING = 5     # ブロック間の余白
BLOCK_TOP_MARGIN = 30  # ブロック表示の上マージンを調整

# 作業ディレクトリをスクリプトのある場所に変更
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Background:
    def __init__(self, path="fig/0.png"):
        raw = pg.image.load(path).convert()
        self.img = pg.transform.scale(raw, (WIDTH, HEIGHT))

    def draw(self, screen):
        screen.blit(self.img, (0, 0))
        

class Paddle:
    def __init__(self, pos):
        # バー画像の読み込み
        self.width = 130
        self.height = 15
        self.rect = pg.Rect(0, 0, self.width, self.height)
        self.rect.midbottom = pos

        self.base_speed = 12
        self.boosted_speed = 20
        self.speed = self.base_speed

        # こうかとん画像の準備
        raw = pg.image.load("fig/fly.png").convert_alpha()
        char_w = self.rect.width // 2
        char_h = int(char_w * raw.get_height() / raw.get_width())
        self.char_img = pg.transform.scale(raw, (char_w, char_h))
        self.dir = 1

        #加速モード
        self.speedup_sound = pg.mixer.Sound("fig/スピードアップ.mp3")
        self.boosting = False
        self.boost_start_time = 0
        self.boost_duration = 10000 #10秒


    def update(self, keys,hud:"HUD"):
        current_time=pg.time.get_ticks()
        if keys[pg.K_SPACE]and not self.boosting and hud.mp > 0:
            self.boosting = True
            self.boost_start_time = current_time
            hud.mp -= 1 #MP消費
            self.speedup_sound.play()  # 加速音
        if self.boosting:
            if current_time-self.boost_start_time<=self.boost_duration:
                self.speed = self.boosted_speed
            else:
                self.boosting = False
                self.speed = self.base_speed
        else:
            self.speed = self.base_speed
        
        if keys[pg.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
            self.dir = 1  # 向きを左と記録
        if keys[pg.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
            self.dir = -1  #向きを右と記録

    def draw(self, screen):
        pg.draw.rect(screen, (0, 100, 255), self.rect, border_radius=self.rect.height // 2)


        char = self.char_img
        if self.dir < 0:
            char = pg.transform.flip(self.char_img, True, False)
        mx, my = self.rect.midbottom
        char_rect = char.get_rect(midtop=(mx, my - 5))  # 5px 上にオフセット
        screen.blit(char, char_rect)


        

class Ball:
    def __init__(self, pos, radius=10):
        self.pos = pg.math.Vector2(pos)
        angle = random.uniform(-math.pi/4, -3*math.pi/4)
        speed = 10
        self.vel = pg.math.Vector2(
            speed * math.cos(angle),
            speed * math.sin(angle)
        )
        self.radius = radius
        self.color = (255, 100, 100)

    def update(self):
        self.pos += self.vel
        if self.pos.x - self.radius <= 0 or self.pos.x + self.radius >= WIDTH:
            self.vel.x *= -1
        if self.pos.y - self.radius <= 0:
            self.vel.y *= -1
        

    def draw(self, screen):
        pg.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def get_rect(self) -> pg.Rect:
        return pg.Rect(
            int(self.pos.x - self.radius),
            int(self.pos.y - self.radius),
            self.radius * 2, self.radius * 2
        )


class Ringo:  #りんごのクラス
    def __init__(self,ap_x,ap_y,ap_rad):
        self.ap_x = ap_x
        self.ap_y = ap_y
        self.color = (255,0,0)
        self.ap_rad = ap_rad
        #座標と半径、色
        
    def update(self):
        self.ap_y += 2
            
    def draw(self,screen):
        app_img = pg.image.load("fig/apple.png")
        app_img = pg.transform.scale(app_img,(60,60))
        screen.blit(app_img,(self.ap_x, int(self.ap_y)))
        
            
    def get_rect(self) -> pg.Rect:
        return pg.Rect(
            int(self.ap_x - self.ap_rad),
            int(self.ap_y - self.ap_rad),
            self.ap_rad * 2, self.ap_rad * 2
        )


class Block:
    """
    ゲーム内のブロックを表すクラス。

    Attributes:
        rect (pg.Rect): ブロックの位置とサイズを示す矩形。
        color (tuple[int, int, int]): ブロックのRGB色。
        alive (bool): ブロックが生存中かどうかのフラグ。
    """
      
    def __init__(self, x, y, color):
        self.rect = pg.Rect(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)
        self.color = color
        self.alive = True

    def draw(self, screen):
        if self.alive:
            pg.draw.rect(screen, self.color, self.rect)

class HUD:
    def __init__(self, font):
        self.font = font
        self.hp = 3
        self.mp = 5
        self.last_regen_time = pg.time.get_ticks()  # MP 再生用タイマー

    def draw(self, screen):
        hp_s = self.font.render(f"HP: {self.hp}/3", True, (255,255,255))
        mp_s = self.font.render(f"MP: {self.mp}/5", True, (255,255,255))
        screen.blit(hp_s, (10, 10))
        screen.blit(mp_s, (10, 40))


class Penetration:
    """
    貫通機能を管理するクラス。

    Attributes:
        active (bool): 貫通中かどうかのフラグ。
        cost (int): 発動に必要なMP。
    """

    def __init__(self, cost=5):
        self.active = False
        self.cost = cost
        # 音声は初期化時に読み込んでおく
        self.sound = pg.mixer.Sound("fig/貫通.mp3")

    def try_activate(self, hud: HUD, ball: Ball):
        """Enter キーが押されたときに，MPが足りていて貫通未発動なら発動する"""
        if not self.active and hud.mp >= self.cost:
            hud.mp -= self.cost
            self.active = True
            ball.color = (255, 255, 100)  # 貫通中の色に変更
            self.sound.play()

    def deactivate(self, ball: Ball):
        """貫通を終了し，ボールの色を元に戻す"""
        if self.active:
            self.active = False
            ball.color = (255, 100, 100)


class Game:
    def __init__(self):
        pg.display.set_caption("こうかとんのブロック崩し")
        self.break_sound = pg.mixer.Sound("fig/割れる.mp3")

        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.bg = Background()
        self.paddle = Paddle((WIDTH//2, HEIGHT - PADDLE_Y_OFFSET))
        self.ball = Ball((self.paddle.rect.centerx, self.paddle.rect.top - 10))
        self.app = Ringo(100,-100,30)
        self.font = pg.font.Font(None, 36)
        self.hud = HUD(self.font)
        self.running = True
        self.game_over_font = pg.font.Font(None, 100)
        self.game_clear_font = pg.font.Font(None, 100) # 追加

        self.penetration = Penetration(cost=5)  # 貫通クラスをインスタンス化

        # こうかとんに当たったときの爆発用のアニメーション
        self.explosion_img = pg.image.load("fig/explosion.gif").convert_alpha()

        # ブロックの全体幅を計算
        total_block_width = BLOCK_COLS * BLOCK_WIDTH + (BLOCK_COLS - 1) * BLOCK_PADDING
        x_middle = (WIDTH - total_block_width) // 2  # 中央に寄せる
        # ブロック生成（中央揃え & 赤ブロックのみ）
        self.blocks: list[Block] = []
        for row in range(BLOCK_ROWS):
            for col in range(BLOCK_COLS):
                x = x_middle + col * (BLOCK_WIDTH + BLOCK_PADDING)
                y = row * (BLOCK_HEIGHT + BLOCK_PADDING) + BLOCK_PADDING + BLOCK_TOP_MARGIN
                color = (255, 0, 0)  # 常に赤
                self.blocks.append(Block(x, y, color))

        # 隣接する赤いブロックを検出して出力
        self.output_adjacent_red_blocks()

    def output_adjacent_red_blocks(self):
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        for b in self.blocks:
            if not b.alive or b.color != (255, 0, 0):
                continue
            neighbors = []
            for dx, dy in directions:
                nx = b.rect.x + dx*(BLOCK_WIDTH+BLOCK_PADDING)
                ny = b.rect.y + dy*(BLOCK_HEIGHT+BLOCK_PADDING)
                for other in self.blocks:
                    if other.alive and other.color == (255, 0, 0) and other.rect.x == nx and other.rect.y == ny:
                        neighbors.append((nx, ny))
            if neighbors:
                print(f"Adjacent red blocks at: {b.rect.x},{b.rect.y} -> {neighbors}")

    def run(self):
        while self.running:

            self.clock.tick(FPS)
            self._events()
            self._update()
            self._draw()

            
            # 全てのブロックが消えたらクリア画面へ
            if all(not block.alive for block in self.blocks):
                self._draw_game_clear()      # クリア画面の描画
                pg.display.flip()            # 表示を更新
                pg.time.delay(3000)          # 3秒待機
                self.running = False         # ループ終了
                break


            if self.hud.hp <= 0:
                self._draw_game_over()
                pg.display.flip()
                pg.time.delay(3000)
                self.running = False
            

                pg.time.delay(4000)
                self.running = False    
        pg.quit()
        sys.exit()

    def _events(self):
        for e in pg.event.get():
            if e.type == pg.QUIT:
                self.running = False
        keys = pg.key.get_pressed()  # Enterキーで貫通開始
        if keys[pg.K_RETURN]:
            self.penetration.try_activate(self.hud, self.ball)

    def _update(self):
        keys = pg.key.get_pressed()
        self.paddle.update(keys, self.hud)
        self.ball.update()
        self.app.update()

        #MP自動回復処理
        current_time = pg.time.get_ticks()
        if current_time - self.hud.last_regen_time >= 5000:  #5秒おきに
            self.hud.last_regen_time = current_time
            if self.hud.mp < 5:
                self.hud.mp += 1  # 1回復する 

        #こうかとんにボールが当たったら爆発&ゲームオーバー
        mx, my = self.paddle.rect.midbottom
        char_img = (self.paddle.char_img 
                    if self.paddle.dir > 0
                    else pg.transform.flip(self.paddle.char_img, True, False))
        char_rect = char_img.get_rect(midtop=(mx, my - 5))
        # 当たり判定を縮小（上下左右 10px 縮める例）
        reduced_rect = char_rect.inflate(-20, -20)  # 幅・高さを小さくする

        if self.ball.get_rect().colliderect(reduced_rect):
            #  爆発音
            pg.mixer.Sound("fig/爆発1.mp3").play()

            # 爆発エフェクト
            self.screen.blit(self.explosion_img, char_rect)
            pg.display.flip()
            pg.time.delay(1000)

            # ゲームオーバー画面へ移行
            self._draw_game_over()
            pg.display.flip()
            pg.time.delay(3000)
            self.running = False
            return

        if self.ball.get_rect().colliderect(self.paddle.rect):  # バー衝突　
            self.ball.vel.y *= -1
            self.penetration.deactivate(self.ball)  # 貫通解除
        
        if self.app.get_rect().colliderect(self.paddle.rect):  # パドル（バー）とりんごの衝突判定
            if self.hud.hp < 3 :
                self.hud.hp += 1  #HPを回復
                pg.mixer.Sound("fig/回復.mp3").play()  # 回復音
            else :
                None
            self.app.ap_x = random.randint(100,2300)
            self.app.ap_y = -100
        

        # ブロック衝突
        ball_rct = self.ball.get_rect()
        for block in self.blocks:
            if not block.alive:
                continue
            if ball_rct.colliderect(block.rect):  #ボールとブロックの衝突判定
                block.alive = False  # ボールが消える
                self.break_sound.play()  # 割れる音
                # 貫通中でなければ反転、貫通中なら反射せずそのまま貫通
                if not self.penetration.active:
                    self.ball.vel.y *= -1
                break

        # 画面下へ落ちたらHP減
        if self.ball.pos.y - self.ball.radius > HEIGHT:
            self.hud.hp -= 1
            # 貫通解除
            self.penetration.deactivate(self.ball)
            self.ball = Ball((self.paddle.rect.centerx, self.paddle.rect.top - 10))
            pg.time.delay(500)
            self.app.ap_y = -100
            self.app.ap_x = random.randint(100,2300)
            #リンゴが落ちたときに再度落ちてくる
        if self.app.ap_y >= 700:
            self.app.ap_y = -100
            self.app.ap_x = random.randint(100,2300)
            

    def _draw(self):
        self.screen.fill((0, 0, 0))
        self.bg.draw(self.screen)
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        for block in self.blocks:
            block.draw(self.screen)
        for block in self.blocks:
            block.draw(self.screen)
        self.hud.draw(self.screen)
        self.app.draw(self.screen)
        pg.display.flip()

    #gameover画面
    def _draw_game_over(self):
        pygame.mixer.init()
        pygame.mixer.music.load("fig/hatapon-crying-344088.mp3")
        pygame.mixer.music.play(-1)
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0,0,0))
        self.screen.blit(overlay, (0, 0))
        #こうかとん画像読み込み
        cry_k =pg.image.load("fig/cry.png")
        cry_k =pg.transform.rotozoom(cry_k,WIDTH,10)
        cry_k2 =pg.transform.flip(cry_k,True,False)
        game_over_surf = self.game_over_font.render("Game Over", True, (255, 0, 0))
        rect = game_over_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(cry_k,[WIDTH//2,HEIGHT//2-120])
        self.screen.blit(cry_k2,[WIDTH//2-650,HEIGHT//2-120])
        self.screen.blit(game_over_surf, rect)


    #クリア画面
    def _draw_game_clear(self):
        pygame.mixer.init()
        pygame.mixer.music.load("fig/crowd-cheering-310544.mp3")
        pygame.mixer.music.play(-1)
        overlay = pg.Surface((WIDTH,HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((255,255,255))
        self.screen.blit(overlay, (0,0))
        happy_k =pg.image.load("fig/happy.png")
        happy_k =pg.transform.rotozoom(happy_k,0,3)
        happy_k =pg.transform.flip(happy_k,True,False)
        game_clear_surf = self.game_clear_font.render("Clear!!!!!!!!!",True, (0,255, 0))
        rect = game_clear_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(happy_k,[WIDTH//2-100,HEIGHT//2])
        self.screen.blit(game_clear_surf, rect)
        

    #クリア画面
    def _draw_game_clear(self):
        pygame.mixer.init()
        pygame.mixer.music.load("fig/crowd-cheering-310544.mp3")
        pygame.mixer.music.play(-1)
        overlay = pg.Surface((WIDTH,HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((255,255,255))
        self.screen.blit(overlay, (0,0))
        happy_k =pg.image.load("fig/happy.png")
        happy_k =pg.transform.rotozoom(happy_k,0,3)
        happy_k =pg.transform.flip(happy_k,True,False)
        game_clear_surf = self.game_clear_font.render("Clear!!!!!!!!!",True, (0,255, 0))
        rect = game_clear_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(happy_k,[WIDTH//2-100,HEIGHT//2])
        self.screen.blit(game_clear_surf, rect)
        

def main():
    pg.init()
    pygame.init()
    pygame.mixer.init()

    # BGMの読み込みと再生（ループ）
    pygame.mixer.music.load("fig/Space.mp3")
    pygame.mixer.music.play(-1)  # -1で無限ループ
    Game().run()

if __name__ == "__main__":
    main()