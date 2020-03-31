import pygame as pg
from settings import *


class Map:
    def __init__(self, filename):
        self.data = []
        with open(filename, 'rt') as f:
            for line in f:
                self.data.append(line.strip())
        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        self.width = self.tilewidth * TILESIZE
        self.height = self.tileheight * TILESIZE


class Camera:
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height)
        self.height = height
        self.width = width


    def apply(self, entity):
        # this moves entities based on the offset of the camera
        # the offset is calculated and applied to the camera in update()
        return entity.rect.move(self.camera.topleft)


    def update(self, target):
        # the offset -- how much we should move all other sprites in the scene
        # moves in the opposite direction as the player.
        x = -target.rect.x + int(WIDTH/2)
        y = -target.rect.y + int(HEIGHT/2)

        # clamps the maximum values such that the camera doesn't go out of bounds 
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width-WIDTH), x)
        y = max(-(self.height-HEIGHT), y)

        self.camera = pg.Rect(x, y, self.width, self.height)
