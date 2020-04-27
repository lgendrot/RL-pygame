import multiprocessing
import queue
import time
import pygame as pg



class AIController(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.inqueue = multiprocessing.Queue()
        self.outqueue = multiprocessing.Queue()



    def run(self):
        while True:
            observation = self.inqueue.get()
            if observation is None:
                print("Quitting...")
                break

            if observation[0] < 150:
                self.outqueue.put((pg.KEYDOWN, pg.K_RIGHT))
            elif observation[1] < 300:
                self.outqueue.put((pg.KEYDOWN, pg.K_DOWN))

    def quit(self):
        self.inqueue.put(None)
        self.join()
        
        
        # Take from inqueue -> observation
        # Use observation to select next action
        # Post action to outqueue
                
