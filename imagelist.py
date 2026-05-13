from os.path import exists
import pygame

class ImageList():
    def __init__(self, filename, width, height):
        self._images=[]
        count = 0
        while exists(filename+str(count)+ '.jpg'):
            image = pygame.image.load(filename+str(count)+ '.jpg')
            scaled = pygame.transform.smoothscale(image,[width,height])
            self._images.append(scaled)
            count +=1

    def get_images(self):
        return self._images
    images = property(get_images, None, None)

# Testing for image list
if __name__ =="__main__":
    SCR_X = 640
    SCR_Y = 480
    TEST_X = 50
    TEST_Y = 50
    TEST_W = 64
    TEST_H = 64
    TEST_FILES = "images\\test\\test"
    image_obj = ImageList(TEST_FILES,TEST_W,TEST_H)
    pygame.init()
    screen = pygame.display.set_mode((SCR_X, SCR_Y),pygame.RESIZABLE)
    quitting = False
    while not quitting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitting = True
        
        count = 0
        for image in image_obj.images:
            image_rect=pygame.Rect(TEST_X + (count * (TEST_W+10)), TEST_Y, TEST_W, TEST_H)
            screen.blit(image,image_rect)
            count += 1
        pygame.display.flip()

    pygame.quit()
