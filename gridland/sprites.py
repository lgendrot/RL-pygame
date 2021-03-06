import pygame as pg
from settings import *
from controller import MonteCarloAgent
import pytweening as tween
import os


class AnimationImages:
    def __init__(self, base_dir, name="player", scale_factor=2):
        self.base_dir = base_dir
        self.scale_factor = scale_factor
        self.images = self.load_images()

    def load_images(self):
        """Rather convoluted method to build a dictionary of animation images,
            expects the structure of the base directory to be 
            action/action_direction_index.png

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
                            
                            dims = (height*self.scale_factor, 
                                    width*self.scale_factor)

                            image = pg.transform.scale(image, dims) 
                            image_dict[entry.name][direction].append(image)
        return image_dict


class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.animation_dict = AnimationImages(os.path.join(
            os.path.dirname(__file__), "img/player")).images
        self.image = self.animation_dict['idle']['forward'][0]
        self.rect = self.image.get_rect()  # Sprite class expects self.rect
        self.x = x
        self.y = y
        self.direction = "forward"
        self.carrot_count = 0
        self.score = 0
        self.total_actions = 0

    def reset(self, x, y):
        self.x = x
        self.y = y
        self.carrot_count = 0
        self.score = 0
        self.total_actions = 0
        self.direction = "forward"

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
        self.score += MOVEMENT_COST
        self.total_actions += 1

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
        if self.total_actions >= MAX_ACTIONS:
            self.score += UNFINISHED_COST
            self.game.playing = False

    def events(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.game.quit()

            if event.key == pg.K_LEFT:
                self.move(dx=-1)
            if event.key == pg.K_RIGHT:
                self.move(dx=1)
            if event.key == pg.K_UP:
                self.move(dy=-1)
            if event.key == pg.K_DOWN:
                self.move(dy=1)


class AIPlayer(Player):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        eventid = pg.USEREVENT+1
        pg.time.set_timer(eventid, AGENT_DELAY)

        self.controller = MonteCarloAgent()
        self.controller.start()

        self.immediate_reward = 0
        self.recent_carrot = False

    def update(self):
        self.queued_events()
        super().update()
        if self.total_actions >= MAX_ACTIONS:
            self.immediate_reward += UNFINISHED_COST

    def move(self, dx=0, dy=0):
        self.recent_carrot = False
        self.immediate_reward += MOVEMENT_COST
        super().move(dx, dy)

    def events(self, event):

        quitting = False
        if event.type == pg.QUIT:
            quitting = True
        elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            quitting = True
        if quitting:
            self.controller.quit()

        # Is using super() clugey?

        # periodically a USEREVENT+1 is sent to the event queue
        # That triggers the player's observe 
        if event.type == pg.USEREVENT+1:
            if self.game.go_screen:
                self.controller.inqueue.put(("NEW_GAME", self.score))
            else:
                self.controller.inqueue.put(self.observe())
        super().events(event)

    def observe(self):
        obs = {}
        carrot_pos = [False, False, False, False]
        
        # is carrot in up, down, left, right
        # player can see 1 tile around itself
        for carrot in self.game.carrots:
            if carrot.rect.collidepoint(self.rect.x, self.rect.y-TILESIZE):
                carrot_pos[0] = True
            elif carrot.rect.collidepoint(self.rect.x, self.rect.y+TILESIZE):
                carrot_pos[1] = True
            elif carrot.rect.collidepoint(self.rect.x-TILESIZE, self.rect.y):
                carrot_pos[2] = True
            elif carrot.rect.collidepoint(self.rect.x+TILESIZE, self.rect.y):
                carrot_pos[3] = True
        carrot_pos = tuple(carrot_pos)
        obs['state'] = (self.rect.x, self.rect.y, carrot_pos, self.carrot_count)
        obs['reward'] = self.immediate_reward
        self.immediate_reward = 0
        return obs

    def queued_events(self):
        while not self.controller.outqueue.empty():
            event = self.controller.outqueue.get()
            pg.event.post(pg.event.Event(event[0], key=event[1]))


class Item(pg.sprite.Sprite):
    def __init__(self, game, x, y, img_name=None, groups=[]):
        self.groups = groups 
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.load_image(img_name)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
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
    def __init__(self, game, x, y, groups):
        super().__init__(game, x, y, "carrot.png", groups) 
        self._layer = 1
        self.tween = tween.easeInOutSine
        self.tween_step = 0
        self.tween_direction = 1

    def collide(self, sprite):
        sprite.carrot_count += 1
        sprite.score += PICKUP_REWARD
        if isinstance(sprite, AIPlayer):
            sprite.immediate_reward = PICKUP_REWARD
            sprite.recent_carrot = True
        self.kill()

    def update(self):
        offset = BOB_RANGE * (self.tween(self.tween_step/BOB_RANGE) - 0.5)
        
        self.rect.y = (self.y-(self.rect.height/8)) + \
            offset * self.tween_direction

        self.tween_step += BOB_SPEED
       
        if self.tween_step > BOB_RANGE:
            self.tween_step = 0
            self.tween_direction *= -1


class Chest(Item):
    def __init__(self, game, x, y, groups):
        super().__init__(game, x, y, groups=groups)
        self.carrot_count = 0

    def reset(self):
        self.carrot_count = 0


    def collide(self, sprite):
        self.carrot_count += sprite.carrot_count
        sprite.score += (CARROT_REWARD * sprite.carrot_count)
        if isinstance(sprite, AIPlayer):
            sprite.immediate_reward = (CARROT_REWARD * sprite.carrot_count)
        sprite.carrot_count = 0
        if self.carrot_count == sprite.game.total_carrots:
            sprite.game.playing = False


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
