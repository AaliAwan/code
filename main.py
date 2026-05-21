# importing files and functions
import json
import os  # Added to prevent a NameError in load_persist_score
import random
import sys
import pygame
from imagelist import ImageList
import enemy

# constants
# Global System Color Palette Constants
COLOR_DARK_GREEN = (10, 45, 16)
COLOR_LIGHT_GREEN = (24, 75, 32)
COLOR_HUD_BG = (120, 110, 45)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_BUTTON_GREEN = (15, 115, 35)
COLOR_BUTTON_HOVER = (35, 165, 60)

# class defs
class GameEngine:
    def __init__(self):
        # init
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
        self.current_state = "MENU"
        self.high_score = self.load_persist_score()
        
        # Game session parameters
        self.score = 0
        self.player_segments = []
        self.player_length = self.cfg['game_balance']['initial_snake_length']
        self.player_dir = (self.cfg['screen']['grid_size'], 0)
        
        # Core Fonts Setup
        self.font_large = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        self.initialize_assets()
        self.reset_match_state()

    # functiondefs
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
        
        self.spawn_fruits()
        
        self.enemies = []
        for _ in range(self.cfg['game_balance']['bot_count']):
            self.enemies.append(
                enemy.Enemy(  # Corrected from 'Enemy' to 'enemy.Enemy' based on your import statement
                    grid * 2, grid * 4, grid, grid, self.img_bot, self.screen, grid,
                    initial_length=self.cfg['game_balance']['initial_snake_length'],
                    max_width=self.current_w, max_height=self.current_h
                )
            )

    def spawn_fruits(self):
        """Generates random item drops within the current grid structure boundaries."""
        # TODO: Add specific fruit positioning logic here
        pass

# the main program
if __name__ == "__main__":
    # program initialization
    # Initialize engine block and entry point execution loop
    game = GameEngine()
    
    # Placeholder execution framework context
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        pygame.display.flip()
        game.clock.tick(game.cfg['screen']['fps'])
        
    pygame.quit()
    sys.exit()