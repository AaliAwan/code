"""
Snakey Safari - Main Executable Game Engine
"""
import os
import json
import random
import sys
import pygame
import time
from imagelist import ImageList
from enemy import Enemy

# Global System Color Palette Constants
COLOR_DARK_GREEN = (10, 45, 16)
COLOR_LIGHT_GREEN = (24, 75, 32)
COLOR_HUD_BG = (120, 110, 45)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_BUTTON_GREEN = (15, 115, 35)
COLOR_BUTTON_HOVER = (35, 165, 60)
COLOR_CARD_DARK = (18, 30, 20)

class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.load_configuration()
        
        # Structural state engine variables
        self.is_fullscreen = False
        self.current_w = self.cfg['screen']['width']
        self.current_h = self.cfg['screen']['height']
        
        self.screen = pygame.display.set_mode(
            (self.current_w, self.current_h), 
            pygame.RESIZABLE
        )
        pygame.display.set_caption(self.cfg['assets']['title'])
        self.clock = pygame.time.Clock()
        self.current_state = "MENU"  # Available: MENU, PLAYING, GAMEOVER, SETTINGS, PROFILE
        self.high_score = self.load_persist_score()
        
        # Game session parameters
        self.score = 0
        self.player_segments = []
        self.player_length = self.cfg['game_balance']['initial_snake_length']
        self.player_dir = (self.cfg['screen']['grid_size'], 0)
        
        # --- ROUND TIMER AND CONFIGURATION MODIFIERS ---
        self.round_start_time = 0.0
        self.current_round_duration = 0.0
        
        # Settings modifiers
        self.mouse_sensitivity = 1.0
        self.bot_enabled = True
        self.speed_multiplier = 1.0  # 1.0x or 2.0x speed modes
        
        # Profile Data Storage tracking variables
        self.stats_deaths = 0
        self.stats_longest_time = 0.0
        self.load_profile_statistics()
        
        # Core Fonts Setup
        self.font_large = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        self.initialize_assets()
        self.reset_match_state()

    def load_configuration(self):
        """Loads variable boundaries from structured metadata file to avoid literals."""
        try:
            with open("config.json", "r") as f:
                self.cfg = json.load(f)
        except Exception:
            self.cfg = {
                "screen": {"width": 1000, "height": 720, "hud_height": 60, "grid_size": 20, "fps": 10},
                "assets": {"title": "Snakey Safari", "high_score_file": "HI_score.txt"},
                "game_balance": {"initial_snake_length": 3, "bot_count": 1}
            }

    def initialize_assets(self):
        """Loads and pre-processes asset objects into graphic memory surfaces."""
        self.img_player = ImageList("images/player", 20, 20)
        self.img_bot = ImageList("images/bot", 20, 20)
        self.img_apple = ImageList("images/apple", 20, 20)
        self.img_pear = ImageList("images/pear", 20, 20)
        self.img_orange = ImageList("images/orange", 20, 20)
        
        try:
            self.snd_eat = pygame.mixer.Sound("sounds/eat.wav")
            self.snd_lose = pygame.mixer.Sound("sounds/lose.wav")
        except Exception:
            self.snd_eat = None
            self.snd_lose = None

    def load_persist_score(self):
        """Retrieves verified high score from structural external file logs."""
        filename = self.cfg['assets']['high_score_file']
        if not os.path.exists(filename):
            try:
                with open(filename, "w") as f: f.write("0")
                return 0
            except IOError: return 0
        try:
            with open(filename, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return 0

    def save_persist_score(self):
        """Saves current score to external logs if high score threshold is exceeded."""
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(self.cfg['assets']['high_score_file'], "w") as f:
                    f.write(str(self.high_score))
            except IOError:
                pass

    def load_profile_statistics(self):
        """Loads cumulative tracking records into memory."""
        try:
            if os.path.exists("profile_stats.json"):
                with open("profile_stats.json", "r") as f:
                    data = json.load(f)
                    self.stats_deaths = data.get("deaths", 0)
                    self.stats_longest_time = data.get("longest_time", 0.0)
        except Exception:
            pass

    def save_profile_statistics(self):
        """Persists tracking metrics dynamically to a metadata file."""
        try:
            data = {
                "deaths": self.stats_deaths,
                "longest_time": max(self.stats_longest_time, self.current_round_duration)
            }
            with open("profile_stats.json", "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def handle_resize(self, width, height):
        """Dynamically scales global dimensions and updates dependent bots."""
        grid = self.cfg['screen']['grid_size']
        self.current_w = (width // grid) * grid
        self.current_h = (height // grid) * grid
        
        if self.current_w < 400: self.current_w = 400
        if self.current_h < 400: self.current_h = 400

        flags = pygame.RESIZABLE
        if self.is_fullscreen:
            flags |= pygame.FULLSCREEN

        self.screen = pygame.display.set_mode((self.current_w, self.current_h), flags)
        
        for bot in self.enemies:
            bot.update_screen_boundaries(self.current_w, self.current_h)

    def toggle_fullscreen_mode(self):
        """Swaps display flags cleanly between targeted window environments."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.handle_resize(info.current_w, info.current_h)
        else:
            self.handle_resize(self.cfg['screen']['width'], self.cfg['screen']['height'])

    def reset_match_state(self):
        """Restores structural coordinate trackers to standard starting values."""
        grid = self.cfg['screen']['grid_size']
        start_x = (self.current_w // (2 * grid)) * grid
        start_y = (self.current_h // (2 * grid)) * grid
        
        self.score = 0
        self.player_length = self.cfg['game_balance']['initial_snake_length']
        self.player_segments = [[start_x, start_y]]
        self.player_dir = (grid, 0)
        
        # Start Round Timers
        self.round_start_time = time.time()
        self.current_round_duration = 0.0
        
        self.spawn_fruits()
        
        self.enemies = []
        if self.bot_enabled:
            for _ in range(self.cfg['game_balance']['bot_count']):
                self.enemies.append(
                    Enemy(
                        grid * 2, grid * 4, grid, grid, self.img_bot, self.screen, grid,
                        initial_length=self.cfg['game_balance']['initial_snake_length'],
                        max_width=self.current_w, max_height=self.current_h
                    )
                )

    def spawn_fruits(self):
        """Generates fruit coordinates mapped directly to your active grid spacing bounds."""
        grid = self.cfg['screen']['grid_size']
        max_w = self.current_w - grid
        max_h = self.current_h - grid
        hud_h = self.cfg['screen']['hud_height']
        
        self.fruits = [
            [random.randrange(0, max_w // grid) * grid, random.randrange(hud_h // grid + 1, max_h // grid) * grid, 2, self.img_apple],
            [random.randrange(0, max_w // grid) * grid, random.randrange(hud_h // grid + 1, max_h // grid) * grid, 3, self.img_pear],
            [random.randrange(0, max_w // grid) * grid, random.randrange(hud_h // grid + 1, max_h // grid) * grid, 5, self.img_orange]
        ]

    def process_system_events(self):
        """Handles hardware system events, resizes, and player key/mouse click inputs."""
        grid = self.cfg['screen']['grid_size']
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_persist_score()
                self.save_profile_statistics()
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                self.handle_resize(event.w, event.h)
                
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                
                # Bounding navigation tracking via nav-bar button
                if self.current_state == "PLAYING":
                    btn_w, btn_h = 100, 36
                    btn_x = 20
                    btn_y = (self.cfg['screen']['hud_height'] // 2) - (btn_h // 2)
                    if pygame.Rect(btn_x, btn_y, btn_w, btn_h).collidepoint(mouse_pos):
                        self.save_persist_score()
                        self.stats_deaths += 1
                        self.save_profile_statistics()
                        self.current_state = "MENU"
                
                # Menu Buttons handling click detection
                elif self.current_state == "MENU":
                    # Start Game Button
                    if pygame.Rect(self.current_w // 2 - 120, self.current_h // 2 - 90, 240, 50).collidepoint(mouse_pos):
                        self.reset_match_state()
                        self.current_state = "PLAYING"
                    # Settings Button
                    elif pygame.Rect(self.current_w // 2 - 120, self.current_h // 2 - 25, 240, 50).collidepoint(mouse_pos):
                        self.current_state = "SETTINGS"
                    # Profile Button
                    elif pygame.Rect(self.current_w // 2 - 120, self.current_h // 2 + 40, 240, 50).collidepoint(mouse_pos):
                        self.current_state = "PROFILE"
                        
                # Settings Menu adjustment clicks handling
                elif self.current_state == "SETTINGS":
                    # Sensitivity adjustments
                    if pygame.Rect(self.current_w // 2 + 60, 200, 40, 30).collidepoint(mouse_pos):
                        self.mouse_sensitivity = round(min(5.0, self.mouse_sensitivity + 0.2), 1)
                    elif pygame.Rect(self.current_w // 2 + 10, 200, 40, 30).collidepoint(mouse_pos):
                        self.mouse_sensitivity = round(max(0.2, self.mouse_sensitivity - 0.2), 1)
                    # Bot state handling
                    elif pygame.Rect(self.current_w // 2 + 10, 270, 100, 35).collidepoint(mouse_pos):
                        self.bot_enabled = not self.bot_enabled
                    # Game speed updates
                    elif pygame.Rect(self.current_w // 2 + 10, 340, 100, 35).collidepoint(mouse_pos):
                        self.speed_multiplier = 2.0 if self.speed_multiplier == 1.0 else 1.0
                    # Return button handling
                    elif pygame.Rect(self.current_w // 2 - 100, self.current_h - 100, 200, 50).collidepoint(mouse_pos):
                        self.current_state = "MENU"
                        
                # Profile Window click processing
                elif self.current_state == "PROFILE":
                    if pygame.Rect(self.current_w // 2 - 100, self.current_h - 100, 200, 50).collidepoint(mouse_pos):
                        self.current_state = "MENU"
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    self.toggle_fullscreen_mode()
                elif self.current_state == "PLAYING":
                    if event.key == pygame.K_UP and self.player_dir[1] == 0:
                        self.player_dir = (0, -grid)
                    elif event.key == pygame.K_DOWN and self.player_dir[1] == 0:
                        self.player_dir = (0, grid)
                    elif event.key == pygame.K_LEFT and self.player_dir[0] == 0:
                        self.player_dir = (-grid, 0)
                    elif event.key == pygame.K_RIGHT and self.player_dir[0] == 0:
                        self.player_dir = (grid, 0)
                elif self.current_state == "GAMEOVER" and event.key == pygame.K_SPACE:
                    self.reset_match_state()
                    self.current_state = "PLAYING"

    def update_frame_ticks(self):
        """Calculates state transitions, live round timers, grid shifts, and collisions."""
        if self.current_state != "PLAYING":
            return
            
        # Real-time processing duration counter
        self.current_round_duration = round(time.time() - self.round_start_time, 1)
            
        grid = self.cfg['screen']['grid_size']
        hud_h = self.cfg['screen']['hud_height']
        
        head_x = self.player_segments[0][0] + self.player_dir[0]
        head_y = self.player_segments[0][1] + self.player_dir[1]
        
        # Dynamic Boundaries Collision Validation Checks
        if (head_x < 0 or head_x >= self.current_w or 
            head_y < hud_h or head_y >= self.current_h):
            if self.snd_lose: self.snd_lose.play()
            self.current_state = "GAMEOVER"
            self.stats_deaths += 1
            self.save_profile_statistics()
            self.save_persist_score()
            return
            
        if [head_x, head_y] in self.player_segments:
            if self.snd_lose: self.snd_lose.play()
            self.current_state = "GAMEOVER"
            self.stats_deaths += 1
            self.save_profile_statistics()
            self.save_persist_score()
            return
            
        self.player_segments.insert(0, [head_x, head_y])
        
        # Process Fruit Bounding Box Collision Cycles for Player
        player_eaten = False
        for fruit in self.fruits:
            if head_x == fruit[0] and head_y == fruit[1]:
                self.score += fruit[2]
                self.player_length += fruit[2]
                if self.snd_eat: self.snd_eat.play()
                player_eaten = True
                break
                
        if player_eaten:
            self.spawn_fruits()
        else:
            if len(self.player_segments) > self.player_length:
                self.player_segments.pop()
                
        # Process AI Tracking, Movement, and Consumption Algorithms
        if self.bot_enabled and self.fruits and len(self.fruits) > 0:
            fruit_regenerate_needed = False
            
            for bot in self.enemies:
                try:
                    bot.update_path(self.fruits[0][0], self.fruits[0][1])
                    bot.process_movement()
                    
                    for fruit in self.fruits:
                        if bot.x == fruit[0] and bot.y == fruit[1]:
                            bot.grow(fruit[2])
                            if self.snd_eat: self.snd_eat.play()
                            fruit_regenerate_needed = True
                            break
                except (AttributeError, IndexError):
                    pass
                
                if [head_x, head_y] in bot.segments:
                    if self.snd_lose: self.snd_lose.play()
                    self.current_state = "GAMEOVER"
                    self.stats_deaths += 1
                    self.save_profile_statistics()
                    self.save_persist_score()
                    return
            
            if fruit_regenerate_needed:
                self.spawn_fruits()

    def render_menu_widgets(self):
        """Renders the modular main menu window displaying selection modules."""
        self.screen.fill(COLOR_DARK_GREEN)
        title_surf = self.font_large.render("Snakey Safari", True, COLOR_TEXT_WHITE)
        self.screen.blit(title_surf, (self.current_w // 2 - title_surf.get_width() // 2, 80))
        
        mouse_pos = pygame.mouse.get_pos()
        btn_w, btn_h = 240, 50
        cx = self.current_w // 2 - btn_w // 2
        
        # 3 Button coordinates setup layout mapping
        buttons = [
            ("Start Game", self.current_h // 2 - 90),
            ("Settings", self.current_h // 2 - 25),
            ("Snakey Profile", self.current_h // 2 + 40)
        ]
        
        for text, y_pos in buttons:
            rect = pygame.Rect(cx, y_pos, btn_w, btn_h)
            hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect, border_radius=6)
            txt_surf = self.font_medium.render(text, True, COLOR_TEXT_WHITE)
            self.screen.blit(txt_surf, (cx + btn_w//2 - txt_surf.get_width()//2, y_pos + btn_h//2 - txt_surf.get_height()//2))

    def render_settings_view(self):
        """Renders the settings adjustments dashboard scene layout view."""
        self.screen.fill(COLOR_DARK_GREEN)
        title_surf = self.font_large.render("Configuration Settings", True, COLOR_TEXT_WHITE)
        self.screen.blit(title_surf, (self.current_w // 2 - title_surf.get_width() // 2, 60))
        
        mouse_pos = pygame.mouse.get_pos()
        cx = self.current_w // 2
        
        # Setting Row 1: Mouse Sensitivity tracking parameters configuration
        lbl_sens = self.font_medium.render(f"Mouse Sensitivity:  {self.mouse_sensitivity}", True, COLOR_TEXT_WHITE)
        self.screen.blit(lbl_sens, (cx - 240, 200))
        
        rect_minus = pygame.Rect(cx + 10, 200, 40, 30)
        rect_plus = pygame.Rect(cx + 60, 200, 40, 30)
        pygame.draw.rect(self.screen, COLOR_BUTTON_GREEN if not rect_minus.collidepoint(mouse_pos) else COLOR_BUTTON_HOVER, rect_minus, border_radius=4)
        pygame.draw.rect(self.screen, COLOR_BUTTON_GREEN if not rect_plus.collidepoint(mouse_pos) else COLOR_BUTTON_HOVER, rect_plus, border_radius=4)
        self.screen.blit(self.font_medium.render("-", True, COLOR_TEXT_WHITE), (cx + 22, 202))
        self.screen.blit(self.font_medium.render("+", True, COLOR_TEXT_WHITE), (cx + 71, 202))
        
        # Setting Row 2: Competitor CPU Bot Enable status controller toggle configuration
        lbl_bot = self.font_medium.render("AI Competitor Bot:", True, COLOR_TEXT_WHITE)
        self.screen.blit(lbl_bot, (cx - 240, 270))
        rect_bot = pygame.Rect(cx + 10, 270, 100, 35)
        pygame.draw.rect(self.screen, COLOR_BUTTON_GREEN if not rect_bot.collidepoint(mouse_pos) else COLOR_BUTTON_HOVER, rect_bot, border_radius=4)
        status_bot = self.font_small.render("ENABLED" if self.bot_enabled else "DISABLED", True, COLOR_TEXT_WHITE)
        self.screen.blit(status_bot, (cx + 60 - status_bot.get_width()//2, 278))
        
        # Setting Row 3: Processing pacing frame tick multi speed controller toggle configuration
        lbl_speed = self.font_medium.render("Pacing Game Speed:", True, COLOR_TEXT_WHITE)
        self.screen.blit(lbl_speed, (cx - 240, 340))
        rect_speed = pygame.Rect(cx + 10, 340, 100, 35)
        pygame.draw.rect(self.screen, COLOR_BUTTON_GREEN if not rect_speed.collidepoint(mouse_pos) else COLOR_BUTTON_HOVER, rect_speed, border_radius=4)
        status_spd = self.font_small.render("2.0x Speed" if self.speed_multiplier == 2.0 else "1.0x Normal", True, COLOR_TEXT_WHITE)
        self.screen.blit(status_spd, (cx + 60 - status_spd.get_width()//2, 348))
        
        # Back Button navigation controller
        rect_back = pygame.Rect(cx - 100, self.current_h - 100, 200, 50)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if rect_back.collidepoint(mouse_pos) else COLOR_BUTTON_GREEN, rect_back, border_radius=6)
        txt_back = self.font_medium.render("Save & Return", True, COLOR_TEXT_WHITE)
        self.screen.blit(txt_back, (cx - txt_back.get_width()//2, self.current_h - 88))

    def render_profile_view(self):
        """Renders the player performance monitoring module screen data dashboards."""
        self.screen.fill(COLOR_DARK_GREEN)
        cx = self.current_w // 2
        
        title_surf = self.font_large.render("Player Profile: Snakey", True, COLOR_TEXT_WHITE)
        self.screen.blit(title_surf, (cx - title_surf.get_width() // 2, 60))
        
        # Background card frame panel
        card_rect = pygame.Rect(cx - 250, 160, 500, 240)
        pygame.draw.rect(self.screen, COLOR_CARD_DARK, card_rect, border_radius=12)
        
        # Render historical tracking metrics data
        txt_high = self.font_medium.render(f"Personal High Score: {self.high_score} pts", True, COLOR_TEXT_WHITE)
        txt_deaths = self.font_medium.render(f"Total Logged Deaths: {self.stats_deaths}", True, COLOR_TEXT_WHITE)
        txt_time = self.font_medium.render(f"Longest Survival Round: {max(self.stats_longest_time, self.current_round_duration)}s", True, COLOR_TEXT_WHITE)
        
        self.screen.blit(txt_high, (cx - 210, 200))
        self.screen.blit(txt_deaths, (cx - 210, 260))
        self.screen.blit(txt_time, (cx - 210, 320))
        
        # Back Button controller
        mouse_pos = pygame.mouse.get_pos()
        rect_back = pygame.Rect(cx - 100, self.current_h - 100, 200, 50)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if rect_back.collidepoint(mouse_pos) else COLOR_BUTTON_GREEN, rect_back, border_radius=6)
        txt_back = self.font_medium.render("Return Menu", True, COLOR_TEXT_WHITE)
        self.screen.blit(txt_back, (cx - txt_back.get_width()//2, self.current_h - 88))

    def draw_gameplay_grid(self):
        """Draws the checkerboard grid map using 20px squares."""
        grid = self.cfg['screen']['grid_size']
        hud_h = self.cfg['screen']['hud_height']
        
        for y in range(hud_h, self.current_h, grid):
            for x in range(0, self.current_w, grid):
                tile_color = COLOR_LIGHT_GREEN if ((x // grid) + (y // grid)) % 2 == 0 else COLOR_DARK_GREEN
                pygame.draw.rect(self.screen, tile_color, pygame.Rect(x, y, grid, grid))

    def render_graphics_pipeline(self):
        """Renders individual component layers directly onto your active screen frame."""
        if self.current_state == "MENU":
            self.render_menu_widgets()
            pygame.display.flip()
            return
        elif self.current_state == "SETTINGS":
            self.render_settings_view()
            pygame.display.flip()
            return
        elif self.current_state == "PROFILE":
            self.render_profile_view()
            pygame.display.flip()
            return
            
        self.draw_gameplay_grid()
        
        # Draw HUD space panel bar boundaries
        hud_rect = pygame.Rect(0, 0, self.current_w, self.cfg['screen']['hud_height'])
        pygame.draw.rect(self.screen, COLOR_HUD_BG, hud_rect)
        
        # HUD Data Output strings tracking metrics values
        text_score = self.font_medium.render(f"Score: {self.score}", True, COLOR_TEXT_WHITE)
        text_high = self.font_medium.render(f"High: {self.high_score}", True, COLOR_TEXT_WHITE)
        
        # Live display tracking string for the round sequence counter
        text_timer = self.font_medium.render(f"Time: {self.current_round_duration}s", True, COLOR_TEXT_WHITE)
        
        self.screen.blit(text_score, (140, 15))
        self.screen.blit(text_timer, (self.current_w // 2 - text_timer.get_width() // 2, 15))
        self.screen.blit(text_high, (self.current_w - text_high.get_width() - 30, 15))
        
        # Home menu back button placement component rendering pipeline
        btn_w, btn_h = 100, 36
        btn_x = 20
        btn_y = (self.cfg['screen']['hud_height'] // 2) - (btn_h // 2)
        nav_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        is_nav_hovered = nav_rect.collidepoint(mouse_pos) and self.current_state == "PLAYING"
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if is_nav_hovered else COLOR_BUTTON_GREEN, nav_rect, border_radius=6)
        
        nav_text = self.font_small.render("Home", True, COLOR_TEXT_WHITE)
        self.screen.blit(nav_text, (btn_x + btn_w // 2 - nav_text.get_width() // 2, btn_y + btn_h // 2 - nav_text.get_height() // 2))
        
        grid = self.cfg['screen']['grid_size']
        for fruit in self.fruits:
            rect = pygame.Rect(fruit[0], fruit[1], grid, grid)
            self.screen.blit(fruit[3].images[0], rect)
            val_text = self.font_small.render(str(fruit[2]), True, COLOR_TEXT_WHITE)
            self.screen.blit(val_text, (fruit[0] + grid//2 - val_text.get_width()//2, fruit[1] + grid//2 - val_text.get_height()//2))
            
        for segment in self.player_segments:
            rect = pygame.Rect(segment[0], segment[1], grid, grid)
            self.screen.blit(self.img_player.images[0], rect)
            
        if self.bot_enabled:
            for bot in self.enemies:
                bot.draw_bot()
            
        if self.current_state == "GAMEOVER":
            overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            go_text = self.font_large.render("GAME OVER", True, (255, 50, 50))
            sub_text = self.font_medium.render("Press SPACE to Restart", True, COLOR_TEXT_WHITE)
            self.screen.blit(go_text, (self.current_w//2 - go_text.get_width()//2, self.current_h // 2 - 40))
            self.screen.blit(sub_text, (self.current_w//2 - sub_text.get_width()//2, self.current_h // 2 + 40))
            
        pygame.display.flip()

    def run(self):
        """Primary executable application processing thread loop."""
        while True:
            self.process_system_events()
            self.update_frame_ticks()
            self.render_graphics_pipeline()
            
            # Pacing adjustment calculation logic modifier scales metrics properly
            target_fps = self.cfg['screen']['fps'] * self.speed_multiplier
            self.clock.tick(target_fps)

if __name__ == "__main__":
    engine = GameEngine()
    engine.run()