"""Snakey Safari - Main Executable Game Engine."""
import os
import json
import random
import sys
import pygame
import time
from imagelist import ImageList
from enemy import Enemy

# Global System Color Palette Constants - JUNGLE/SAFARI THEME
COLOR_DARK_GREEN = (10, 30, 15)  # Darker jungle green
COLOR_LIGHT_GREEN = (35, 80, 35)  # Lush jungle green
COLOR_HUD_BG = (60, 50, 30)  # Warm wood brown
COLOR_HUD_GRADIENT_TOP = (80, 65, 40)  # Lighter wood
COLOR_HUD_GRADIENT_BOTTOM = (40, 35, 20)  # Darker wood
COLOR_TEXT_LIME = (50, 255, 50)  # Lime green for title
COLOR_TEXT_GOLD = (255, 215, 0)  # Golden text for highlights
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_CREAM = (245, 235, 200)  # Creamy white for readability
COLOR_BUTTON_GREEN = (25, 55, 30)  # Darker jungle green for buttons
COLOR_BUTTON_HOVER = (45, 90, 50)  # Slightly lighter on hover
COLOR_CARD_DARK = (20, 30, 20)  # Dark jungle shadow
COLOR_GRID_ALT = (35, 80, 35)  # Alternate grid color
COLOR_LEAF = (60, 140, 40)  # Leaf green (kept for menu background)
COLOR_UNCOMMON = (255, 200, 50)  # Gold for uncommon fruits
COLOR_RARE = (255, 80, 80)  # Red for rare fruits


class GameEngine:
    """Main Game Engine Class."""

    def __init__(self):
        """Game Engine Constructor."""
        pygame.init()
        pygame.mixer.init()
        self.load_configuration()

        # Structural state engine variables
        self.is_fullscreen = False
        self.current_w = self.cfg['screen']['width']
        self.current_h = self.cfg['screen']['height']
        self.base_grid_size = self.cfg['screen']['grid_size']
        self.current_grid_size = self.base_grid_size
        self.screen = pygame.display.set_mode(
            (self.current_w, self.current_h),
            pygame.RESIZABLE
        )
        pygame.display.set_caption(self.cfg['assets']['title'])
        self.clock = pygame.time.Clock()
        self.current_state = "MENU"  # MENU, PLAYING, GAMEOVER, SETTINGS, PROFILE, HOWTOPLAY
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
        self.bot_enabled = True
        self.speed_multiplier = 1.0  # 1.0x, 1.5x, or 2.0x speed modes
        self.speed_options = [1.0, 1.5, 2.0]
        self.speed_index = 0  # Index into speed_options

        # Profile Data Storage tracking variables
        self.stats_deaths = 0
        self.stats_longest_time = 0.0
        self.stats_total_score = 0
        self.load_profile_statistics()

        # Core Fonts Setup
        self.font_title = pygame.font.Font(None, 72)
        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Initialize assets
        self.initialize_assets()

        # Load and start home screen music
        self.music_on = True
        self.sfx_on = True
        self.current_music = None
        self.load_and_play_home_music()

        # Reset game state
        self.reset_match_state()

        # --- Confirmation dialog flags ---
        self.confirm_exit_game = False   # Home button or ESC during gameplay
        self.confirm_quit_app = False    # Quit button on main menu
        self.confirm_message = ""        # Message to display in the dialog

    def load_configuration(self):
        """Load variable boundaries from structured metadata file to avoid literals."""
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
        """Load and pre-processes asset objects into graphic memory surfaces."""
        self.img_player = ImageList("images/player", 20, 20)
        self.img_bot = ImageList("images/bot", 20, 20)
        self.img_apple = ImageList("images/apple", 20, 20)
        self.img_pear = ImageList("images/pear", 20, 20)
        self.img_orange = ImageList("images/orange", 20, 20)

        # --- LOAD HOME SCREEN LOGO IMAGE ---
        try:
            raw_logo = pygame.image.load("images/logo.png").convert_alpha()
            logo_scale = min(self.cfg['screen']['width'] * 0.25, 250)
            self.img_logo = pygame.transform.smoothscale(raw_logo, (int(logo_scale), int(logo_scale)))
            self.logo_width = int(logo_scale)
            self.logo_height = int(logo_scale)
        except Exception:
            self.img_logo = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.circle(self.img_logo, COLOR_BUTTON_GREEN, (100, 100), 80)
            pygame.draw.circle(self.img_logo, COLOR_TEXT_GOLD, (100, 100), 60, 3)
            for i in range(5):
                angle = i * 1.2
                x = 100 + int(50 * (i/4) * pygame.math.Vector2(1, 0).rotate_rad(angle).x)
                y = 100 + int(50 * (i/4) * pygame.math.Vector2(1, 0).rotate_rad(angle).y)
                pygame.draw.circle(self.img_logo, COLOR_TEXT_GOLD, (x, y), 15 - i*2)
            self.logo_width = 200
            self.logo_height = 200

        # --- LOAD HOME SCREEN MENU SNAKE IMAGE ---
        try:
            raw_menu_snake = pygame.image.load("image_5bd317.png").convert_alpha()
            self.img_menu_snake = pygame.transform.smoothscale(raw_menu_snake, (220, 220))
        except Exception:
            self.img_menu_snake = pygame.Surface((220, 220), pygame.SRCALPHA)
            pygame.draw.rect(self.img_menu_snake, COLOR_BUTTON_GREEN, (0, 0, 220, 220), border_radius=12)

        # --- SOUND LOADING ---
        try:
            self.snd_eat = pygame.mixer.Sound(os.path.join("sounds", "eat.wav"))
        except Exception as e:
            print(f"ERROR: Could not load eat sound. Reason: {e}")
            self.snd_eat = None

        try:
            self.snd_lose = pygame.mixer.Sound(os.path.join("sounds", "lose.wav"))
        except Exception as e:
            print(f"ERROR: Could not load lose sound. Reason: {e}")
            self.snd_lose = None

    def load_persist_score(self):
        """Load high score from file."""
        filename = self.cfg['assets']['high_score_file']
        if not os.path.exists(filename):
            try:
                with open(filename, "w") as f: f.write("0")
                return 0
            except IOError:
                return 0
        try:
            with open(filename, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return 0

    def save_persist_score(self):

        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(self.cfg['assets']['high_score_file'], "w") as f:
                    f.write(str(self.high_score))
            except IOError:
                pass

    def load_profile_statistics(self):
        """Load high score from file."""
        try:
            if os.path.exists("profile_stats.json"):
                with open("profile_stats.json", "r") as f:
                    data = json.load(f)
                    self.stats_deaths = data.get("deaths", 0)
                    self.stats_longest_time = data.get("longest_time", 0.0)
                    self.stats_total_score = data.get("total_score", 0)
        except Exception:
            pass

    def save_profile_statistics(self):
        """"Save high score to file."""
        try:
            data = {
                "deaths": self.stats_deaths,
                "longest_time": max(self.stats_longest_time, self.current_round_duration),
                "total_score": self.stats_total_score + self.score
            }
            with open("profile_stats.json", "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def handle_resize(self, width, height):
        """Handle window resize."""
        if width < 100:
            width = 400
        if height < 100:
            height = 400
       
        target_cells = 35
        new_grid = max(10, min(width // target_cells, 40))
       
        self.current_grid_size = new_grid
        self.current_w = width
        self.current_h = height
       
        if self.current_w < 400:
            self.current_w = 400
        if self.current_h < 400:
            self.current_h = 400

        flags = pygame.RESIZABLE
        if self.is_fullscreen:
            flags |= pygame.FULLSCREEN

        self.screen = pygame.display.set_mode((self.current_w, self.current_h), flags)
        self.align_all_objects_to_grid()
       
        try:
            raw_logo = pygame.image.load("images/logo.png").convert_alpha()
            logo_scale = min(self.current_w * 0.2, 250)
            self.img_logo = pygame.transform.smoothscale(raw_logo, (int(logo_scale), int(logo_scale)))
            self.logo_width = int(logo_scale)
            self.logo_height = int(logo_scale)
        except Exception:
            pass

    def align_all_objects_to_grid(self):
        grid = self.current_grid_size
       
        if hasattr(self, 'player_segments') and self.player_segments:
            new_segments = []
            for seg in self.player_segments:
                new_segments.append([
                    (seg[0] // grid) * grid,
                    (seg[1] // grid) * grid
                ])
            self.player_segments = new_segments
       
        if hasattr(self, 'fruits'):
            new_fruits = []
            for fruit in self.fruits:
                new_fruits.append([
                    (fruit[0] // grid) * grid,
                    (fruit[1] // grid) * grid,
                    fruit[2],
                    fruit[3]
                ])
            self.fruits = new_fruits
       
        if hasattr(self, 'enemies'):
            for bot in self.enemies:
                bot.update_screen_boundaries(self.current_w, self.current_h)
                bot.grid_size = grid
                bot.width = grid
                bot.height = grid
                if hasattr(bot, 'segments'):
                    new_segments = []
                    for seg in bot.segments:
                        new_segments.append([
                            (seg[0] // grid) * grid,
                            (seg[1] // grid) * grid
                        ])
                    bot.segments = new_segments

    def toggle_fullscreen_mode(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.handle_resize(info.current_w, info.current_h)
        else:
            self.handle_resize(self.cfg['screen']['width'], self.cfg['screen']['height'])

    def reset_match_state(self):
        grid = self.current_grid_size
        start_x = (self.current_w // (2 * grid)) * grid
        start_y = (self.current_h // (2 * grid)) * grid

        self.score = 0
        self.player_length = self.cfg['game_balance']['initial_snake_length']
        self.player_segments = [[start_x, start_y]]
        self.player_dir = (grid, 0)

        self.round_start_time = time.time()
        self.current_round_duration = 0.0

        self.spawn_fruits()

        self.enemies = []
        self.bot_targets = []   # list of (target_x, target_y) for each enemy

        if getattr(self, 'bot_enabled', True):
            for _ in range(self.cfg['game_balance']['bot_count']):
                enemy = Enemy(
                    grid * 2, grid * 4, grid, grid, self.img_bot, self.screen, grid,
                    initial_length=self.cfg['game_balance']['initial_snake_length'],
                    max_width=self.current_w, max_height=self.current_h
                )
                enemy.segments = [[(s[0] // grid) * grid, (s[1] // grid) * grid] for s in enemy.segments]
                self.enemies.append(enemy)

        # Assign a random fruit target for each bot
        for _ in self.enemies:
            if self.fruits:
                target = random.choice(self.fruits)
                self.bot_targets.append((target[0], target[1]))
            else:
                self.bot_targets.append((0, 0))  # fallback

    def spawn_fruits(self):
        grid = self.current_grid_size
        max_w = self.current_w - grid
        max_h = self.current_h - grid
        hud_h = self.cfg['screen']['hud_height']
       
        self.fruits = [
            [random.randrange(0, max_w // grid) * grid,
             random.randrange(hud_h // grid + 1, max_h // grid) * grid,
             2, self.img_apple],
            [random.randrange(0, max_w // grid) * grid,
             random.randrange(hud_h // grid + 1, max_h // grid) * grid,
             3, self.img_pear],
            [random.randrange(0, max_w // grid) * grid,
             random.randrange(hud_h // grid + 1, max_h // grid) * grid,
             5, self.img_orange]
        ]

    # ------------------- CONFIRMATION DIALOG HELPERS -------------------
    def get_confirmation_rects(self, message):
        """Computes the rectangles for the confirmation dialog and Yes/No buttons.
           Returns (dialog_rect, yes_rect, no_rect)."""
        # Dialog box
        dialog_w = int(600 * (self.current_w / 1000))
        dialog_h = int(200 * (self.current_h / 720))
        dialog_x = (self.current_w - dialog_w) // 2
        dialog_y = (self.current_h - dialog_h) // 2 - 50
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_w, dialog_h)

        # Yes / No buttons
        btn_w = int(100 * (self.current_w / 1000))
        btn_h = int(40 * (self.current_h / 720))
        spacing = 20
        total_width = 2 * btn_w + spacing
        start_x = dialog_x + (dialog_w - total_width) // 2
        btn_y = dialog_y + dialog_h - btn_h - 30
        yes_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        no_rect = pygame.Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)

        return dialog_rect, yes_rect, no_rect

    def draw_confirmation_dialog(self, message):
        """Draws the confirmation dialog overlay."""
        dialog_rect, yes_rect, no_rect = self.get_confirmation_rects(message)

        # Semi-transparent overlay
        overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Dialog background
        pygame.draw.rect(self.screen, (30, 30, 30), dialog_rect, border_radius=12)
        pygame.draw.rect(self.screen, (80, 80, 80), dialog_rect, 2, border_radius=12)

        # Message text (split by newline)
        font = pygame.font.Font(None, max(20, int(28 * (self.current_h / 720))))
        lines = message.split('\n')
        y_offset = dialog_rect.y + 30
        for line in lines:
            text_surf = font.render(line, True, COLOR_TEXT_CREAM)
            self.screen.blit(text_surf, (dialog_rect.x + 30, y_offset))
            y_offset += 35

        # Yes / No buttons
        for rect, label, color in [
            (yes_rect, "Yes", (60, 180, 60)),
            (no_rect, "No", (180, 60, 60))
        ]:
            hover = rect.collidepoint(pygame.mouse.get_pos())
            btn_color = color if not hover else (
                min(255, color[0] + 30),
                min(255, color[1] + 30),
                min(255, color[2] + 30)
            )
            pygame.draw.rect(self.screen, btn_color, rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255, 30), rect, 1, border_radius=6)
            txt = pygame.font.Font(None, max(18, int(26 * (self.current_h / 720)))).render(label, True, COLOR_TEXT_WHITE)
            self.screen.blit(txt, (rect.x + rect.w//2 - txt.get_width()//2,
                                   rect.y + rect.h//2 - txt.get_height()//2))

    # ------------------- EVENT PROCESSING -------------------
    def process_system_events(self):
        grid = self.current_grid_size
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_persist_score()
                self.save_profile_statistics()
                pygame.quit()
                sys.exit()

            elif event.type == pygame.VIDEORESIZE and not getattr(self, 'is_fullscreen', False):
                self.handle_resize(event.w, event.h)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                # --- Handle confirmation dialogs first ---
                if self.confirm_exit_game:
                    _, yes_rect, no_rect = self.get_confirmation_rects(
                        "Are you sure you want to go to home menu?\n(Note: You lose all your progress)"
                    )
                    if yes_rect.collidepoint(mouse_pos):
                        # Yes: exit to menu
                        self.save_persist_score()
                        self.stats_deaths += 1
                        self.save_profile_statistics()
                        self.current_state = "MENU"
                        self.load_and_play_home_music()
                        self.confirm_exit_game = False
                    elif no_rect.collidepoint(mouse_pos):
                        self.confirm_exit_game = False
                    continue  # ignore other clicks while dialog is active

                if self.confirm_quit_app:
                    _, yes_rect, no_rect = self.get_confirmation_rects(
                        "Are you sure you want to quit?"
                    )
                    if yes_rect.collidepoint(mouse_pos):
                        self.save_persist_score()
                        self.save_profile_statistics()
                        pygame.quit()
                        sys.exit()
                    elif no_rect.collidepoint(mouse_pos):
                        self.confirm_quit_app = False
                    continue

                # --- Regular state clicks (only if no dialog active) ---
                if self.current_state == "PLAYING":
                    btn_w = int(100 * (self.current_w / 1000))
                    btn_h = int(36 * (self.current_h / 720))
                    btn_x = 20
                    btn_y = (self.cfg['screen']['hud_height'] // 2) - (btn_h // 2)
                    if pygame.Rect(btn_x, btn_y, btn_w, btn_h).collidepoint(mouse_pos):
                        self.confirm_exit_game = True
                        return  # prevent further processing in this frame

                elif self.current_state == "MENU":
                    btn_w = int(220 * (self.current_w / 1000))
                    btn_h = int(45 * (self.current_h / 720))
                    cx = self.current_w // 2 - btn_w // 2

                    logo_height = getattr(self, 'logo_height', 200)
                    title_offset = 80 + (logo_height * 0.6)
                    start_y = int(title_offset + 180 * (self.current_h / 720))
                    spacing = int(55 * (self.current_h / 720))

                    # Main menu buttons
                    if pygame.Rect(cx, start_y, btn_w, btn_h).collidepoint(mouse_pos):
                        self.reset_match_state()
                        self.current_state = "PLAYING"
                        self.load_and_play_game_music()
                    elif pygame.Rect(cx, start_y + spacing, btn_w, btn_h).collidepoint(mouse_pos):
                        self.current_state = "SETTINGS"
                    elif pygame.Rect(cx, start_y + spacing * 2, btn_w, btn_h).collidepoint(mouse_pos):
                        self.current_state = "PROFILE"
                    elif pygame.Rect(cx, start_y + spacing * 3, btn_w, btn_h).collidepoint(mouse_pos):
                        self.current_state = "HOWTOPLAY"
                    elif pygame.Rect(cx, start_y + spacing * 4, btn_w, btn_h).collidepoint(mouse_pos):
                        self.current_state = "SOUND"

                    # Quit button (bottom-right)
                    quit_btn_w = int(80 * (self.current_w / 1000))
                    quit_btn_h = int(35 * (self.current_h / 720))
                    quit_rect = pygame.Rect(
                        self.current_w - quit_btn_w - 20,
                        self.current_h - quit_btn_h - 20,
                        quit_btn_w, quit_btn_h
                    )
                    if quit_rect.collidepoint(mouse_pos):
                        self.confirm_quit_app = True

                elif self.current_state == "SETTINGS":
                    btn_w = int(100 * (self.current_w / 1920))
                    btn_h = int(35 * (self.current_h / 1080))
                    cx = self.current_w // 2
                    spacing = int(70 * (self.current_h / 720))

                    # Bot toggle
                    if pygame.Rect(cx + 20, 200, btn_w, btn_h).collidepoint(mouse_pos):
                        self.bot_enabled = not self.bot_enabled
                    # Speed toggle
                    elif pygame.Rect(cx + 20, 200 + spacing, btn_w, btn_h).collidepoint(mouse_pos):
                        self.speed_index = (self.speed_index + 1) % len(self.speed_options)
                        self.speed_multiplier = self.speed_options[self.speed_index]
                    # Return button
                    elif pygame.Rect(self.current_w // 2 - 100, self.current_h - 100, 200, 50).collidepoint(mouse_pos):
                        self.current_state = "MENU"

                elif self.current_state == "PROFILE":
                    if pygame.Rect(self.current_w // 2 - 100, self.current_h - 100, 200, 50).collidepoint(mouse_pos):
                        self.current_state = "MENU"

                elif self.current_state == "SOUND":
                    btn_w = int(100 * (self.current_w / 1000))
                    btn_h = int(35 * (self.current_h / 720))
                    cx = self.current_w // 2
                    spacing = int(70 * (self.current_h / 720))

                    # Music toggle
                    if pygame.Rect(cx + 20, 200, btn_w, btn_h).collidepoint(mouse_pos):
                        self.toggle_music()
                    # SFX toggle
                    elif pygame.Rect(cx + 20, 200 + spacing, btn_w, btn_h).collidepoint(mouse_pos):
                        self.toggle_sfx()
                    # Return button
                    elif pygame.Rect(cx - 100, self.current_h - 100, 200, 50).collidepoint(mouse_pos):
                        self.current_state = "MENU"

                elif self.current_state == "HOWTOPLAY":
                    cx = self.current_w // 2
                    if pygame.Rect(cx - 100, self.current_h - 100, 200, 50).collidepoint(mouse_pos):
                        self.current_state = "MENU"

                elif self.current_state == "GAMEOVER":
                    if pygame.Rect(self.current_w // 2 - 150, self.current_h // 2 + 100, 300, 50).collidepoint(mouse_pos):
                        self.current_state = "MENU"
                        self.load_and_play_home_music()

            elif event.type == pygame.KEYDOWN:
                if self.current_state == "PLAYING":
                    if event.key in [pygame.K_w, pygame.K_UP] and self.player_dir[1] == 0:
                        self.player_dir = (0, -grid)
                    elif event.key in [pygame.K_s, pygame.K_DOWN] and self.player_dir[1] == 0:
                        self.player_dir = (0, grid)
                    elif event.key in [pygame.K_a, pygame.K_LEFT] and self.player_dir[0] == 0:
                        self.player_dir = (-grid, 0)
                    elif event.key in [pygame.K_d, pygame.K_RIGHT] and self.player_dir[0] == 0:
                        self.player_dir = (grid, 0)
                    elif event.key == pygame.K_ESCAPE:
                        self.confirm_exit_game = True
                elif self.current_state == "GAMEOVER":
                    if event.key == pygame.K_SPACE:
                        self.reset_match_state()
                        self.current_state = "PLAYING"
                        self.load_and_play_game_music()
                    elif event.key == pygame.K_ESCAPE:
                        self.current_state = "MENU"
                        self.load_and_play_home_music()

    # ------------------- GAME UPDATE -------------------
    def update_frame_ticks(self):
        # Do not update if a confirmation dialog is active
        if self.confirm_exit_game or self.confirm_quit_app:
            return

        if self.current_state != "PLAYING":
            return

        self.current_round_duration = round(time.time() - self.round_start_time, 1)

        grid = self.current_grid_size
        hud_h = self.cfg['screen']['hud_height']
       
        head_x = self.player_segments[0][0] + self.player_dir[0]
        head_y = self.player_segments[0][1] + self.player_dir[1]

        if (head_x < 0 or head_x >= self.current_w or
            head_y < hud_h or head_y >= self.current_h):
            self.play_lose_sfx()
            self.current_state = "GAMEOVER"
            self.stats_deaths += 1
            self.stats_total_score += self.score
            self.save_profile_statistics()
            self.save_persist_score()
            return

        if [head_x, head_y] in self.player_segments:
            self.play_lose_sfx()
            self.current_state = "GAMEOVER"
            self.stats_deaths += 1
            self.stats_total_score += self.score
            self.save_profile_statistics()
            self.save_persist_score()
            return

        self.player_segments.insert(0, [head_x, head_y])

        player_eaten = False
        for fruit in self.fruits:
            if head_x == fruit[0] and head_y == fruit[1]:
                self.score += fruit[2]
                self.player_length += fruit[2]
                self.play_eat_sfx()
                player_eaten = True
                break

        if player_eaten:
            self.spawn_fruits()
        else:
            if len(self.player_segments) > self.player_length:
                self.player_segments.pop()

        # --- BOT LOGIC with random fruit targeting ---
        if self.bot_enabled and hasattr(self, 'enemies') and self.fruits:
            fruit_regenerate_needed = False

            # Ensure bot_targets list matches enemy count
            while len(self.bot_targets) < len(self.enemies):
                if self.fruits:
                    target = random.choice(self.fruits)
                    self.bot_targets.append((target[0], target[1]))
                else:
                    self.bot_targets.append((0, 0))

            for i, bot in enumerate(self.enemies):
                try:
                    # Check if current target still exists in fruits
                    target_x, target_y = self.bot_targets[i]
                    target_exists = any(f[0] == target_x and f[1] == target_y for f in self.fruits)

                    if not target_exists and self.fruits:
                        # Target fruit is gone – pick a new random fruit
                        new_target = random.choice(self.fruits)
                        self.bot_targets[i] = (new_target[0], new_target[1])
                        target_x, target_y = self.bot_targets[i]

                    # Move bot towards its target
                    bot.update_path(target_x, target_y)
                    bot.process_movement()

                    # Check if bot ate a fruit
                    for fruit in self.fruits:
                        if bot.x == fruit[0] and bot.y == fruit[1]:
                            bot.grow(fruit[2])
                            self.play_eat_sfx()
                            fruit_regenerate_needed = True
                            break
                except (AttributeError, IndexError):
                    pass

                # Check collision with bot
                if [head_x, head_y] in bot.segments:
                    self.play_lose_sfx()
                    self.current_state = "GAMEOVER"
                    self.stats_deaths += 1
                    self.stats_total_score += self.score
                    self.save_profile_statistics()
                    self.save_persist_score()
                    return

            if fruit_regenerate_needed:
                self.spawn_fruits()
                # After regeneration, bot targets that pointed to removed fruits will be updated on next frame

    # ------------------- RENDERING -------------------
    def draw_gradient_rect(self, rect, color1, color2):
        for i in range(rect.height):
            progress = i / rect.height
            r = int(color1[0] + (color2[0] - color1[0]) * progress)
            g = int(color1[1] + (color2[1] - color1[1]) * progress)
            b = int(color1[2] + (color2[2] - color1[2]) * progress)
            pygame.draw.line(self.screen, (r, g, b),
                           (rect.x, rect.y + i),
                           (rect.x + rect.width, rect.y + i))

    def draw_leaf_decoration(self, x, y, size, color):
        points = [
            (x, y - size),
            (x + size//2, y),
            (x, y + size),
            (x - size//2, y)
        ]
        pygame.draw.polygon(self.screen, color, points)

    def render_menu_widgets(self):
        for y in range(self.current_h):
            progress = y / self.current_h
            r = int(5 + 20 * progress)
            g = int(25 + 30 * progress)
            b = int(10 + 20 * progress)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.current_w, y))
       
        for i in range(6):
            x = (i * 197 + 30) % self.current_w
            y = (i * 89 + 20) % self.current_h
            size = 15 + (i % 3) * 8
            color = (30, 80 + i*10, 30)
            self.draw_leaf_decoration(x, y, size, color)

        if hasattr(self, 'img_logo'):
            logo_x = self.current_w // 2 - self.img_logo.get_width() // 2
            logo_y = 30
            self.screen.blit(self.img_logo, (logo_x, logo_y))
            title_y = logo_y + self.img_logo.get_height() + 15
        else:
            title_y = 80
       
        title_surf = self.font_title.render("Snakey Safari", True, COLOR_TEXT_LIME)
        shadow = self.font_title.render("Snakey Safari", True, (10, 60, 10))
        self.screen.blit(shadow, (self.current_w // 2 - title_surf.get_width() // 2 + 3, title_y + 3))
        self.screen.blit(title_surf, (self.current_w // 2 - title_surf.get_width() // 2, title_y))
       
        sub_surf = self.font_small.render("Jungle Adventure", True, COLOR_TEXT_CREAM)
        self.screen.blit(sub_surf, (self.current_w // 2 - sub_surf.get_width() // 2, title_y + 55))

        mouse_pos = pygame.mouse.get_pos()

        btn_w = int(220 * (self.current_w / 1000))
        btn_h = int(45 * (self.current_h / 720))
        cx = self.current_w // 2 - btn_w // 2
       
        logo_height = getattr(self, 'logo_height', 200)
        title_offset = 80 + (logo_height * 0.6)
        start_y = int(title_offset + 180 * (self.current_h / 720))
        spacing = int(55 * (self.current_h / 720))

        buttons = [
            ("Start Game", start_y),
            ("Settings", start_y + spacing),
            ("Profile", start_y + spacing * 2),
            ("How to Play", start_y + spacing * 3),
            ("Sound", start_y + spacing * 4)
        ]

        for text, y_pos in buttons:
            rect = pygame.Rect(cx, y_pos, btn_w, btn_h)
            hover = rect.collidepoint(mouse_pos)
           
            if hover:
                for i in range(3):
                    glow_rect = rect.inflate(i * 4, i * 4)
                    pygame.draw.rect(self.screen, (COLOR_BUTTON_HOVER[0], COLOR_BUTTON_HOVER[1], COLOR_BUTTON_HOVER[2], 50 - i*15),
                                   glow_rect, border_radius=8)
           
            color = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255, 20), rect, 2, border_radius=8)
           
            font_size = max(18, int(26 * (self.current_w / 1000)))
            font = pygame.font.Font(None, font_size)
            txt_surf = font.render(text, True, COLOR_TEXT_WHITE)
            self.screen.blit(txt_surf, (cx + btn_w//2 - txt_surf.get_width()//2,
                                      y_pos + btn_h//2 - txt_surf.get_height()//2))

        # Quit button (bottom-right)
        quit_btn_w = int(80 * (self.current_w / 1000))
        quit_btn_h = int(35 * (self.current_h / 720))
        quit_rect = pygame.Rect(self.current_w - quit_btn_w - 20,
                                self.current_h - quit_btn_h - 20,
                                quit_btn_w, quit_btn_h)
        hover = quit_rect.collidepoint(mouse_pos)
        color = (200, 80, 80) if hover else (120, 50, 50)
        pygame.draw.rect(self.screen, color, quit_rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), quit_rect, 1, border_radius=6)
        quit_txt = self.font_small.render("Quit", True, COLOR_TEXT_WHITE)
        self.screen.blit(quit_txt, (quit_rect.x + quit_rect.w//2 - quit_txt.get_width()//2,
                                    quit_rect.y + quit_rect.h//2 - quit_txt.get_height()//2))

    def render_settings_view(self):
        self.screen.fill((10, 30, 15))
       
        border_rect = pygame.Rect(20, 20, self.current_w - 40, self.current_h - 40)
        pygame.draw.rect(self.screen, (40, 80, 40), border_rect, 3, border_radius=12)
       
        title_surf = self.font_large.render("Settings", True, COLOR_TEXT_LIME)
        self.screen.blit(title_surf, (self.current_w // 2 - title_surf.get_width() // 2, 60))
       
        mouse_pos = pygame.mouse.get_pos()
        cx = self.current_w // 2
       
        btn_w = int(100 * (self.current_w / 1000))
        btn_h = int(35 * (self.current_h / 720))
        spacing = int(70 * (self.current_h / 720))

        lbl_bot = self.font_medium.render("AI Competitor:", True, COLOR_TEXT_CREAM)
        self.screen.blit(lbl_bot, (cx - 220, 200))
        rect_bot = pygame.Rect(cx + 20, 200, btn_w, btn_h)
        hover = rect_bot.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_bot, border_radius=6)
        status_bot = self.font_small.render("ON" if self.bot_enabled else "OFF", True, COLOR_TEXT_WHITE)
        self.screen.blit(status_bot, (cx + 20 + btn_w//2 - status_bot.get_width()//2, 200 + btn_h//2 - status_bot.get_height()//2))

        speed_labels = {1.0: "Slow", 1.5: "Medium", 2.0: "Fast"}
        lbl_speed = self.font_medium.render("Game Speed:", True, COLOR_TEXT_CREAM)
        self.screen.blit(lbl_speed, (cx - 220, 200 + spacing))
        rect_speed = pygame.Rect(cx + 20, 200 + spacing, btn_w, btn_h)
        hover = rect_speed.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_speed, border_radius=6)
        status_spd = self.font_small.render(f"{self.speed_multiplier}x", True, COLOR_TEXT_WHITE)
        self.screen.blit(status_spd, (cx + 20 + btn_w//2 - status_spd.get_width()//2, 200 + spacing + btn_h//2 - status_spd.get_height()//2))

        rect_back = pygame.Rect(cx - 100, self.current_h - 100, 200, 50)
        hover = rect_back.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_back, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), rect_back, 2, border_radius=8)
        txt_back = self.font_medium.render("Return", True, COLOR_TEXT_WHITE)
        self.screen.blit(txt_back, (cx - txt_back.get_width()//2, self.current_h - 88))

    def render_profile_view(self):
        self.screen.fill((10, 30, 15))
       
        border_rect = pygame.Rect(20, 20, self.current_w - 40, self.current_h - 40)
        pygame.draw.rect(self.screen, (40, 80, 40), border_rect, 3, border_radius=12)
       
        cx = self.current_w // 2
        title_surf = self.font_large.render("Profile", True, COLOR_TEXT_LIME)
        self.screen.blit(title_surf, (cx - title_surf.get_width() // 2, 60))
       
        card_w = int(500 * (self.current_w / 1000))
        card_h = int(280 * (self.current_h / 720))
        card_rect = pygame.Rect(cx - card_w//2, 150, card_w, card_h)
        pygame.draw.rect(self.screen, (15, 30, 15), card_rect, border_radius=12)
        pygame.draw.rect(self.screen, (40, 80, 40), card_rect, 2, border_radius=12)

        stats = [
            f"High Score: {self.high_score} pts",
            f"Deaths: {self.stats_deaths}",
            f"Longest Survival: {max(self.stats_longest_time, self.current_round_duration)}s",
            f"Total Score: {self.stats_total_score + self.score} pts"
        ]

        y_start = 180
        spacing = 55
        for i, stat in enumerate(stats):
            txt = self.font_medium.render(stat, True, COLOR_TEXT_CREAM)
            self.screen.blit(txt, (cx - txt.get_width()//2, y_start + i * spacing))

        mouse_pos = pygame.mouse.get_pos()
        rect_back = pygame.Rect(cx - 100, self.current_h - 100, 200, 50)
        hover = rect_back.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_back, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), rect_back, 2, border_radius=8)
        txt_back = self.font_medium.render("Return", True, COLOR_TEXT_WHITE)
        self.screen.blit(txt_back, (cx - txt_back.get_width()//2, self.current_h - 88))

    def render_sound_view(self):
        self.screen.fill((10, 30, 15))
       
        border_rect = pygame.Rect(20, 20, self.current_w - 40, self.current_h - 40)
        pygame.draw.rect(self.screen, (40, 80, 40), border_rect, 3, border_radius=12)
       
        mouse_pos = pygame.mouse.get_pos()
        cx = self.current_w // 2

        title_surf = self.font_large.render("Sound", True, COLOR_TEXT_LIME)
        self.screen.blit(title_surf, (cx - title_surf.get_width() // 2, 60))

        btn_w = int(100 * (self.current_w / 1000))
        btn_h = int(35 * (self.current_h / 720))
        spacing = int(70 * (self.current_h / 720))

        lbl_music = self.font_medium.render("Music:", True, COLOR_TEXT_CREAM)
        self.screen.blit(lbl_music, (cx - 220, 200))
        rect_music = pygame.Rect(cx + 20, 200, btn_w, btn_h)
        hover = rect_music.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_music, border_radius=6)
        status_music = self.font_small.render("ON" if self.music_on else "OFF", True, COLOR_TEXT_WHITE)
        self.screen.blit(status_music, (cx + 20 + btn_w//2 - status_music.get_width()//2, 200 + btn_h//2 - status_music.get_height()//2))

        lbl_sfx = self.font_medium.render("Sound FX:", True, COLOR_TEXT_CREAM)
        self.screen.blit(lbl_sfx, (cx - 220, 200 + spacing))
        rect_sfx = pygame.Rect(cx + 20, 200 + spacing, btn_w, btn_h)
        hover = rect_sfx.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_sfx, border_radius=6)
        status_sfx = self.font_small.render("ON" if self.sfx_on else "OFF", True, COLOR_TEXT_WHITE)
        self.screen.blit(status_sfx, (cx + 20 + btn_w//2 - status_sfx.get_width()//2, 200 + spacing + btn_h//2 - status_sfx.get_height()//2))

        rect_back = pygame.Rect(cx - 100, self.current_h - 100, 200, 50)
        hover = rect_back.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_back, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), rect_back, 2, border_radius=8)
        txt_back = self.font_medium.render("Return", True, COLOR_TEXT_WHITE)
        self.screen.blit(txt_back, (cx - txt_back.get_width()//2, self.current_h - 88))

    def render_how_to_play(self):
        self.screen.fill((10, 30, 15))
       
        border_rect = pygame.Rect(20, 20, self.current_w - 40, self.current_h - 40)
        pygame.draw.rect(self.screen, (40, 80, 40), border_rect, 3, border_radius=12)
       
        title_surf = self.font_large.render("How to Play", True, COLOR_TEXT_LIME)
        self.screen.blit(title_surf, (self.current_w // 2 - title_surf.get_width() // 2, 40))
       
        # Adjusted card height for shorter content
        card_w = int(800 * (self.current_w / 1000))
        card_h = int(420 * (self.current_h / 720))  # reduced height
        card_x = self.current_w // 2 - card_w // 2
        card_y = 100
       
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill((15, 30, 15, 230))
        self.screen.blit(card_surf, (card_x, card_y))
        pygame.draw.rect(self.screen, (40, 80, 40), (card_x, card_y, card_w, card_h), 2, border_radius=8)
       
        content_y = card_y + 20
        line_spacing = max(20, int(28 * (self.current_h / 720)))
        font = pygame.font.Font(None, max(18, int(24 * (self.current_h / 720))))
       
        # Instructions truncated at GAME OVER
        instructions = [
            "OBJECTIVE",
            "Guide Snakey through the jungle to eat fruits and grow!",
            "",
            "CONTROLS",
            "WASD or Arrow Keys - Navigate Snakey",
            "SPACE - Restart after Game Over",
            "ESC - Return to Main Menu",
            "",
            "FRUIT VALUES",
            "Apple - 2 points (Common)",
            "Pear - 3 points (Uncommon)",
            "Orange - 5 points (Rare)",
            "",
            "GAME OVER",
            "* Hitting the jungle boundaries",
            "* Colliding with your own snake body",
            "* Getting caught by AI competitor snakes"
        ]
       
        for line in instructions:
            if line == "FRUIT VALUES":
                text_surf = font.render(line, True, COLOR_TEXT_GOLD)
                self.screen.blit(text_surf, (card_x + 30, content_y))
                content_y += line_spacing
                continue
            elif line == "":
                content_y += line_spacing // 2
                continue
           
            text_surf = font.render(line, True, COLOR_TEXT_CREAM if not line.startswith("*") else (200, 200, 180))
            self.screen.blit(text_surf, (card_x + 30, content_y))
            content_y += line_spacing
           
            if content_y > card_y + card_h - 40:
                break
       
        # Return button
        cx = self.current_w // 2
        rect_back = pygame.Rect(cx - 100, self.current_h - 100, 200, 50)
        mouse_pos = pygame.mouse.get_pos()
        hover = rect_back.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_GREEN, rect_back, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), rect_back, 2, border_radius=8)
        txt_back = self.font_medium.render("Return", True, COLOR_TEXT_WHITE)
        self.screen.blit(txt_back, (cx - txt_back.get_width()//2, self.current_h - 88))

    def draw_gameplay_grid(self):
        grid = self.current_grid_size
        hud_h = self.cfg['screen']['hud_height']
        for y in range(hud_h, self.current_h, grid):
            for x in range(0, self.current_w, grid):
                if ((x // grid) + (y // grid)) % 2 == 0:
                    tile_color = COLOR_LIGHT_GREEN
                else:
                    tile_color = COLOR_DARK_GREEN
                pygame.draw.rect(self.screen, tile_color, pygame.Rect(x, y, grid, grid))

    def render_graphics_pipeline(self):
        if self.current_state == "MENU":
            self.render_menu_widgets()
            # Draw confirmation if active (for Quit button)
            if self.confirm_quit_app:
                self.draw_confirmation_dialog("Are you sure you want to quit?")
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
        elif self.current_state == "SOUND":
            self.render_sound_view()
            pygame.display.flip()
            return
        elif self.current_state == "HOWTOPLAY":
            self.render_how_to_play()
            pygame.display.flip()
            return

        # --- PLAYING or GAMEOVER ---
        self.draw_gameplay_grid()

        # HUD background with gradient
        hud_height = self.cfg['screen']['hud_height']
        hud_rect = pygame.Rect(0, 0, self.current_w, hud_height)
        self.draw_gradient_rect(hud_rect, COLOR_HUD_GRADIENT_TOP, COLOR_HUD_GRADIENT_BOTTOM)
       
        # HUD decorative line (simple)
        pygame.draw.line(self.screen, (100, 80, 50), (0, hud_height), (self.current_w, hud_height), 2)

        # Scale HUD text
        font_med = pygame.font.Font(None, max(20, int(36 * (self.current_h / 720))))
        font_small = pygame.font.Font(None, max(16, int(24 * (self.current_h / 720))))
       
        # --- DYNAMIC HUD ALIGNMENT ---
        btn_w = int(100 * (self.current_w / 1000))
        btn_h = int(36 * (self.current_h / 720))
        btn_x = 20
        btn_y = (hud_height // 2) - (btn_h // 2)
        btn_end = btn_x + btn_w + 20

        text_score = font_med.render(f"Score: {self.score}", True, COLOR_TEXT_GOLD)
        text_high = font_med.render(f"High: {self.high_score}", True, COLOR_TEXT_GOLD)
        text_timer = font_med.render(f"Time: {self.current_round_duration}s", True, COLOR_TEXT_CREAM)
       
        score_x = btn_end + 20
        high_score_x = self.current_w - text_high.get_width() - 30
        timer_x = self.current_w // 2 - text_timer.get_width() // 2

        if timer_x < score_x + text_score.get_width() + 20:
            timer_x = score_x + text_score.get_width() + 20
        if timer_x + text_timer.get_width() > high_score_x - 20:
            timer_x = high_score_x - text_timer.get_width() - 20
        if timer_x < 0:
            timer_x = 10

        self.screen.blit(text_score, (score_x, 15))
        self.screen.blit(text_timer, (timer_x, 15))
        self.screen.blit(text_high, (high_score_x, 15))

        # Home button
        nav_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        mouse_pos = pygame.mouse.get_pos()
        is_nav_hovered = nav_rect.collidepoint(mouse_pos) and self.current_state == "PLAYING"
        color = COLOR_BUTTON_HOVER if is_nav_hovered else COLOR_BUTTON_GREEN
        pygame.draw.rect(self.screen, color, nav_rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), nav_rect, 1, border_radius=6)
        nav_text = font_small.render("Home", True, COLOR_TEXT_WHITE)
        self.screen.blit(nav_text, (btn_x + btn_w//2 - nav_text.get_width()//2, btn_y + btn_h//2 - nav_text.get_height()//2))

        # Fruits with glow effect
        grid = self.current_grid_size
        for fruit in self.fruits:
            fruit_x = (fruit[0] // grid) * grid
            fruit_y = (fruit[1] // grid) * grid
            rect = pygame.Rect(fruit_x, fruit_y, grid, grid)
           
            glow_size = grid + 4
            glow_rect = pygame.Rect(fruit_x - 2, fruit_y - 2, glow_size, glow_size)
            glow_color = (255, 200, 50, 30)
            pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=4)
           
            fruit_img = pygame.transform.scale(fruit[3].images[0], (grid, grid))
            self.screen.blit(fruit_img, rect)
            val_text = font_small.render(str(fruit[2]), True, COLOR_TEXT_GOLD)
            self.screen.blit(val_text, (fruit_x + grid//2 - val_text.get_width()//2, fruit_y + grid//2 - val_text.get_height()//2))
       
        # Snake segments
        for segment in self.player_segments:
            seg_x = (segment[0] // grid) * grid
            seg_y = (segment[1] // grid) * grid
            rect = pygame.Rect(seg_x, seg_y, grid, grid)
            player_img = pygame.transform.scale(self.img_player.images[0], (grid, grid))
            self.screen.blit(player_img, rect)

        # Bots
        if self.bot_enabled:
            for bot in getattr(self, 'enemies', []):
                bot.grid_size = grid
                bot.width = grid
                bot.height = grid
                bot.draw_bot()

        # Game over overlay
        if self.current_state == "GAMEOVER":
            overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
            overlay.fill((5, 15, 5, 200))
            self.screen.blit(overlay, (0, 0))
           
            go_border = pygame.Rect(self.current_w//2 - 280, self.current_h//2 - 120, 560, 240)
            pygame.draw.rect(self.screen, (20, 40, 20), go_border, border_radius=12)
            pygame.draw.rect(self.screen, (80, 60, 40), go_border, 3, border_radius=12)
           
            go_text = self.font_large.render("GAME OVER", True, (255, 80, 80))
            self.screen.blit(go_text, (self.current_w//2 - go_text.get_width()//2, self.current_h // 2 - 90))
           
            you_died_text = self.font_medium.render("You Died", True, COLOR_TEXT_CREAM)
            self.screen.blit(you_died_text, (self.current_w//2 - you_died_text.get_width()//2, self.current_h // 2 - 30))
           
            score_text = self.font_medium.render(f"Score: {self.score}", True, COLOR_TEXT_LIME)
            self.screen.blit(score_text, (self.current_w//2 - score_text.get_width()//2, self.current_h // 2 + 20))
           
            restart_text = self.font_small.render("Press SPACE to Restart", True, COLOR_TEXT_CREAM)
            self.screen.blit(restart_text, (self.current_w//2 - restart_text.get_width()//2, self.current_h // 2 + 70))
           
            menu_text = self.font_small.render("Press ESC to go to Main Menu", True, COLOR_TEXT_CREAM)
            self.screen.blit(menu_text, (self.current_w//2 - menu_text.get_width()//2, self.current_h // 2 + 100))

        # --- Draw confirmation dialog if active (Home/ESC during gameplay) ---
        if self.confirm_exit_game:
            self.draw_confirmation_dialog(
                "Are you sure you want to go to home menu?\n(Note: You lose all your progress)"
            )

        pygame.display.flip()

    # ------------------- MUSIC / SFX -------------------
    def load_and_play_home_music(self):
        self.current_music = "home"
        if not self.music_on:
            return
        try:
            pygame.mixer.music.load(os.path.join("sounds", "homescreen.wav"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading home music: {e}")

    def load_and_play_game_music(self):
        self.current_music = "game"
        if not self.music_on:
            return
        try:
            pygame.mixer.music.load(os.path.join("sounds", "maingame.wav"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading game music: {e}")

    def toggle_music(self):
        self.music_on = not self.music_on
        if self.music_on:
            if self.current_music == "game":
                self.load_and_play_game_music()
            else:
                self.load_and_play_home_music()
        else:
            pygame.mixer.music.stop()

    def toggle_sfx(self):
        self.sfx_on = not self.sfx_on

    def play_eat_sfx(self):
        if self.sfx_on and self.snd_eat:
            self.snd_eat.play()

    def play_lose_sfx(self):
        if self.sfx_on and self.snd_lose:
            self.snd_lose.play()

    # ------------------- MAIN LOOP -------------------
    def run(self):
        while True:
            self.process_system_events()
            self.update_frame_ticks()
            self.render_graphics_pipeline()
            target_fps = self.cfg['screen']['fps'] * self.speed_multiplier
            self.clock.tick(target_fps)


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()