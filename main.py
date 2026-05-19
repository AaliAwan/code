import os
import json
import random
import sys
import pygame
from imagelist import ImageList

# Global System Color Palette Constants
COLOR_DARK_GREEN = (10, 45, 16)
COLOR_LIGHT_GREEN = (24, 75, 32)
COLOR_HUD_BG = (120, 110, 45)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_BUTTON_GREEN = (15, 115, 35)
COLOR_BUTTON_HOVER = (35, 165, 60)

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