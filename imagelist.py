"""
ImageList Module - Asset management engine.
"""
from os.path import exists
import pygame

class ImageList:
    def __init__(self, filename, width, height):
        """Loads and crops a sequence of indexed image variants automatically."""
        self._images = []
        count = 0
        # Check files matching pattern
        while True:
            current_file = f"{filename}{count}.png"
            if not exists(current_file):
                current_file = f"{filename}{count}.jpg"
                if not exists(current_file):
                    break
            
            image = pygame.image.load(current_file).convert_alpha()
            scaled = pygame.transform.smoothscale(image, [width, height])
            self._images.append(scaled)
            count += 1
            
        # Fallback safeguard if no automated frames
        if not self._images:
            fallback = pygame.Surface((width, height))
            fallback.fill((255, 0, 0))
            self._images.append(fallback)

    def get_images(self):
        return self._images

    images = property(get_images, None, None)