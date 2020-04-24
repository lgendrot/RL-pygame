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
from controller import AIController

#TODO: Make WIDTH and HEIGHT automatic by loading map data first    


class Game:
    def __init__(self):
        #pg.init()
        pg.display.init()
        pg.font.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        pg.key.set_repeat(250, 50) # Allows us to hold dowW keys to move, etc.
        self.load_data()
        self.total_carrots = 0

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
        self.items = pg.sprite.Group()
        self.carrots = pg.sprite.Group()
        for tile_object in self.map.tmxdata.objects:
            if tile_object.name == "player":
                print("player location: ", tile_object.x, tile_object.y)
                self.player = Player(self, tile_object.x, tile_object.y)
            if tile_object.name == "wall":
                Obstacle(self, tile_object.x, tile_object.y, 
                               tile_object.width, tile_object.height)
            if tile_object.name == "carrot":
                Carrot(self, tile_object.x, tile_object.y) 
                self.total_carrots += 1
            if tile_object.name == "chest":
                Chest(self, tile_object.x, tile_object.y)

        self.camera = Camera(self.map.width, self.map.height)
        eventid = pg.USEREVENT+1
        pg.time.set_timer(eventid, 1000)
        self.controller = AIController()
        self.controller.start()




    def run(self):
        # game loop - set self.playing = False to end the game
        # useful for ending a training session
        self.playing = True
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.queued_events()
            self.events()
            self.update()
            self.draw()

    def quit(self):
        self.playing = False
        self.controller.inqueue.put(None)
        self.controller.join()
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

        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_LEFT:
                    self.player.move(dx=-1)
                if event.key == pg.K_RIGHT:
                    self.player.move(dx=1)
                if event.key == pg.K_UP:
                    self.player.move(dy=-1)
                if event.key == pg.K_DOWN:
                    self.player.move(dy=1)
            if event.type == pg.USEREVENT+1:
                print("Adding to queue")
                self.controller.inqueue.put((self.player.rect.x, self.player.rect.y))

    def queued_events(self):
        while not self.controller.outqueue.empty():
            event = self.controller.outqueue.get()

            pg.event.post(pg.event.Event(event[0], key=event[1]))

    def score_surface(self, player):
        template = "Score: {}, Remaining Moves: {}"
        template = template.format(player.score, MAX_ACTIONS-player.total_actions) 
        return pg.font.Font(pg.font.get_default_font(), 24).render(template, True, (0, 0, 255))

        



    def show_start_screen(self):
        pass

    def show_go_screen(self):
        self.go_screen = True
        while self.go_screen:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    self.go_screen = False


# create the game object
g = Game()
g.show_start_screen()
while True:
    g.new()
    g.run()
    g.show_go_screen()
