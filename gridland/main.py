# KidsCanCode - Game Development with Pygame video series
# Tile-based game - Part 1
# Project setup
# Video link: https://youtu.be/3UxnelT9aCo

import pygame as pg
import sys
import queue
from os import path
from settings import *
from sprites import *
from tilemap import TiledMap, Camera

# TODO: Make WIDTH and HEIGHT automatic by loading map data first


class Game:
    def __init__(self):
        # pg.init()
        pg.display.init()
        pg.font.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        pg.key.set_repeat(250, 50)  # Allows us to hold dowW keys to move, etc.
        self.load_data()
        self.total_carrots = 0
        self.go_screen = False

    def load_data(self):
        game_folder = path.dirname(__file__)
        map_folder = path.join(game_folder, "maps")
        self.map = TiledMap(path.join(map_folder, "AI-map.tmx"))
        self.map_img = self.map.make_map()
        self.map_rect = self.map_img.get_rect()
        #self.map = Map(path.join(game_folder, "map.txt"))

    def new(self):
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.chest = pg.sprite.Group()
        self.items = pg.sprite.Group()
        self.carrots = pg.sprite.Group()
        for tile_object in self.map.tmxdata.objects:
            if tile_object.name == "player":
                print("player location: ", tile_object.x, tile_object.y)
                self.player = AIPlayer(self, tile_object.x, tile_object.y)             
                #self.player = Player(self, tile_object.x, tile_object.y)

            if tile_object.name == "wall":
                Obstacle(self, tile_object.x, tile_object.y,
                         tile_object.width, tile_object.height)
            if tile_object.name == "carrot":
                Carrot(self, tile_object.x, tile_object.y, groups=[self.all_sprites, self.carrots])
                self.total_carrots += 1
            if tile_object.name == "chest":
                Chest(self, tile_object.x, tile_object.y, groups=[self.all_sprites, self.chest])

        self.camera = Camera(self.map.width, self.map.height)

    def reset(self):
        # initialize all variables anddo all the setup for a new game
        
        self.chest = pg.sprite.Group()
        for chest in self.chest:
            self.all_sprites.remove(chest)
            chest.kill()
        
        for carrot in self.carrots:
            self.all_sprites.remove(carrot)
            carrot.kill()
        self.carrots.empty()
        self.carrots = pg.sprite.Group()

        for item in self.items:
            self.all_sprites.remove(item)
            item.kill()
        self.items = pg.sprite.Group()
        self.total_carrots = 0
        
        for tile_object in self.map.tmxdata.objects:
            if tile_object.name == "player":
                print("player location: ", tile_object.x, tile_object.y)
                #self.player = AIPlayer(self, tile_object.x, tile_object.y)
                self.player.reset(tile_object.x, tile_object.y)
            if tile_object.name == "carrot":
                Carrot(self, tile_object.x, tile_object.y, groups=[self.all_sprites, self.carrots, self.items])
                self.total_carrots += 1
            if tile_object.name == "chest":
                Chest(self, tile_object.x, tile_object.y, groups=[self.all_sprites, self.chest, self.items])


    def run(self):
        # game loop - set self.playing = False to end the game
        # useful for ending a training session
        self.playing = True
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.update()
            self.events()
            self.draw()

    def quit(self):
        self.playing = False
        pg.quit()
        pg.display.quit()
        sys.exit()

    def update(self):
        # update portion of the game loop
        self.all_sprites.update()
        self.camera.update(self.player)

    def draw_grid(self):
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y), (WIDTH, y))

    def draw(self):
        self.screen.fill(BGCOLOR)
        self.draw_grid()
        self.screen.blit(self.map_img, self.camera.apply_rect(self.map_rect))
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        self.screen.blit(self.score_surface(self.player), (0, 0))
       
        # Yuck 
        try:
            for state in self.state_values:
                val = self.state_values.get(state, 0)
                val = round(val, 2)
                x, y = (state[0]+TILESIZE/2, state[1]+TILESIZE/2)
                if len(state) == 3 and state[2] == True:
                    y = state[1] + TILESIZE/4
                self.screen.blit(self.state_value_surface(str(val)), (x,y))
        except NameError:
            print("Oops, no state values to blit")

        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if isinstance(self.player, AIController):
                    self.player.controller.quit()
                self.quit()
            self.player.events(event)

    def score_surface(self, player):
        template = "Score: {}, Remaining Moves: {}"
        template = template.format(
            player.score, MAX_ACTIONS-player.total_actions)
       
        default_font = pg.font.get_default_font()
        return pg.font.Font(default_font, 18).render(template, True, (0,0,255))

    def show_start_screen(self):
        pass

    def game_over_surface(self):
        text = "Game Over! Press Any Key To Play Again"
        default_font = pg.font.get_default_font()
        return pg.font.Font(default_font, 24).render(text, True, (0, 0, 255))

    def state_value_surface(self, V):
        default_font = pg.font.get_default_font()
        return pg.font.Font(default_font, 8).render(V, True, (0,0,240))

    def show_go_screen(self):
        self.go_screen = True
        while self.go_screen:
            go_surf = self.game_over_surface()
            self.screen.blit(
                go_surf, (WIDTH/2-(go_surf.get_width()/2), HEIGHT/2))

            pg.display.flip()
            
            self.events()
            self.update()
            
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    self.go_screen = False

# create the game object
g = Game()
g.show_start_screen()
g.new()
while True:
    g.run()
    g.show_go_screen()
    g.reset()
