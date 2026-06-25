"""
Snakey Safari - Enemy Bot Class Module
NCEA Level 3 Digital Technologies AS 91906 Excellence Framework.
"""
import pygame

class Enemy:
    def __init__(self, x, y, width, height, image_list, screen, grid_size, initial_length=3, max_width=1000, max_height=720):
        """
        Initializes the competitor bot entity.
        Saves boundary restrictions locally so they can scale alongside the viewport frame.
        """
        self.width = width
        self.height = height
        self.image_list = image_list
        self.screen = screen
        self.grid_size = grid_size
        
        # Dynamic boundaries storage tracking variables
        self.max_width = max_width
        self.max_height = max_height
        
        self.segments = [[x, y]]
        self.bot_length = initial_length
        
        self.target_x = x
        self.target_y = y

    @property
    def x(self):
        return self.segments[0][0]

    @property
    def y(self):
        return self.segments[0][1]

    def update_screen_boundaries(self, new_width, new_height):
        """Updates internal barrier limits when window dimension states shift."""
        self.max_width = new_width
        self.max_height = new_height

    def update_path(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y

    def grow(self, quantity):
        """Increments the internal segment cap threshold by the fruit's weight value."""
        self.bot_length += quantity

    def process_movement(self):
        """
        Calculates a step along the grid toward the target, inserts a new head position,
        manages the trailing body trail, and enforces defensive boundary clamping.
        """
        hud_h = 60

        head_x, head_y = self.segments[0][0], self.segments[0][1]
        delta_x = self.target_x - head_x
        delta_y = self.target_y - head_y

        next_x, next_y = head_x, head_y

        if abs(delta_x) >= abs(delta_y) and delta_x != 0:
            next_x += self.grid_size if delta_x > 0 else -self.grid_size
        elif delta_y != 0:
            next_y += self.grid_size if delta_y > 0 else -self.grid_size

        # --- EXCELLENCE FRAMEWORK: DYNAMIC DATA VALIDATION LAYER ---
        # BUGFIX: Mathematical snapping boundaries back into active grid alignment
        if next_y < hud_h:
            next_y = ((hud_h // self.grid_size) + 1) * self.grid_size
        if next_y >= self.max_height:
            next_y = ((self.max_height - self.grid_size) // self.grid_size) * self.grid_size
        if next_x < 0:
            next_x = 0
        if next_x >= self.max_width:
            next_x = ((self.max_width - self.grid_size) // self.grid_size) * self.grid_size

        self.segments.insert(0, [next_x, next_y])

        if len(self.segments) > self.bot_length:
            self.segments.pop()

    def draw_bot(self):
        """Draws the bot with proper scaling to match the current grid size."""
        for segment in self.segments:
            # Align segment to grid
            seg_x = (segment[0] // self.grid_size) * self.grid_size
            seg_y = (segment[1] // self.grid_size) * self.grid_size
            rect = pygame.Rect(seg_x, seg_y, self.grid_size, self.grid_size)
            try:
                # Scale the image to match the current grid size
                img = pygame.transform.scale(self.image_list.images[0], (self.grid_size, self.grid_size))
                self.screen.blit(img, rect)
            except (AttributeError, IndexError):
                pygame.draw.rect(self.screen, (200, 40, 40), rect)
