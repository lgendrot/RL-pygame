import pygame as pg
from settings import *
import os


class AnimationImages:
    def __init__(self, base_dir, name="player", scale_factor=2):
        self.base_dir = base_dir
        self.scale_factor = scale_factor
        self.images = self.load_images()

    def load_images(self):
        """Rather convoluted method to build a dictionary of animation images,
        expects the structure of the base directory to be action/action_direction_index.png

        output: self.images[action][direction] = [file1, file2, file3]
        """
        with os.scandir(self.base_dir) as entries:
            image_dict = {}
            for entry in entries:
                if entry.is_dir():
                    image_dict[entry.name] = {}
                    for file in os.scandir(entry.path):
                        if file.is_file() and file.name.endswith(".png"):
                            name = file.name.split(".")[0]
                            action, direction, index = name.split("_")
                            if not image_dict[entry.name].get(direction, False):
                                image_dict[entry.name][direction] = []
                            image = pg.image.load(file.path).convert()
                            height, width = image.get_size()
                            image = pg.transform.scale(image, (height*self.scale_factor, width*self.scale_factor))
                            image_dict[entry.name][direction].append(image)
        return image_dict


class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.animation_dict = AnimationImages(os.path.join(os.path.dirname(__file__), "img/player")).images
        self.image = self.animation_dict['idle']['forward'][0] 
        self.rect = self.image.get_rect() # Sprite class expects self.rect
        self.x = x
        self.y = y
        self.direction = "forward"
        self.carrot_count = 0

    def move(self, dx=0, dy=0):
        dx *= TILESIZE
        dy *= TILESIZE
        if not self.collide_with_walls(dx, dy):
            if dx == 0 and dy > 0:
                self.direction = "forward"
            elif dx > 0 and dy == 0:
                self.direction = "right"
            elif dx < 0 and dy == 0:
                self.direction = "left"
            elif dx == 0 and dy < 0:
                self.direction = "back"
            
            self.x += dx
            self.y += dy
            
                
    
            
    def collide_with_walls(self, dx, dy):
        for wall in self.game.walls:
            if wall.rect.collidepoint(self.x + dx, self.y + dy):
                return True
        return False

    def collide_with_items(self):
        for item in self.game.items:
            if item.rect.collidepoint(self.x, self.y):
                item.collide(self)
                return True
        return False

    def update(self):
        self.image = self.animation_dict['idle'][self.direction][0]
        self.rect.x = self.x 
        self.rect.y = self.y
        self.collide_with_items()

class Item(pg.sprite.Sprite):
    def __init__(self, game, x, y, img_name=None):
        self.groups = game.all_sprites, game.items
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.load_image(img_name)
        self.rect = self.image.get_rect()
        self.x = int(x/TILESIZE)
        self.y = int(y/TILESIZE)
        self.rect.x = x 
        self.rect.y = y
        self.active = True
    
    def collide(self, sprite):
        pass

    def load_image(self, img_name):
        if img_name:
            return pg.image.load(os.path.join(IMAGE_FOLDER, img_name))
        return pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA)

class Carrot(Item):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, "carrot.png")
        self._layer = 1
    
    def collide(self, sprite):
        sprite.carrot_count += 1
        self.kill()
               

class Chest(Item):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.carrot_count = 0

    def collide(self, sprite):
        self.carrot_count += sprite.carrot_count
        sprite.carrot_count = 0
        print("Carrots in chest: ", self.carrot_count)
        

class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Obstacle(pg.sprite.Sprite):
    def __init__(self, game, x, y, w, h):
        self.groups = game.walls,
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = pg.Rect(x, y, w, h) 
        self.x = int(x/TILESIZE)
        self.y = int(y/TILESIZE)
        self.rect.x = x
        self.rect.y = y
