import multiprocessing
import queue
import time
import pygame as pg
import numpy as np
from settings import TILESIZE, EXPLORATION_RATE

class AIController(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.inqueue = multiprocessing.Queue()
        self.outqueue = multiprocessing.Queue()
        self.debug_queue = multiprocessing.Queue()


    def run(self):
        raise NotImplementedError("AIController Class must implement Run Method")
    
    
    def quit(self):
        self.inqueue.put(None)
        self.join()




class MonteCarloAgent(AIController): 
    def __init__(self):
        super().__init__()
        self.V_s = dict()
        self.N_s = dict()


    def run(self):
        episode_list = []
        while True:
            observation = self.inqueue.get()
            if observation is None:
                print("Quitting...")
                break
            elif observation[0] == "NEW_GAME":
                print(self.N_s)
                self.G = observation[1]
                for state in episode_list:
                    self.V_s[state] += ((1/self.N_s[state])*(self.G - self.V_s[state]))
                self.G = 0
                self.outqueue.put((pg.KEYDOWN, pg.K_DOWN))
                self.debug_queue.put(self.V_s)
                episode_list = []
            else:
                episode_list.append(observation)
                if self.N_s.get(observation, None):
                    self.N_s[observation] += 1
                else:
                    self.N_s[observation] = 1
                    self.V_s[observation] = 0


            # Get surrounding squares:

                up = list(np.array((0, 1))*TILESIZE)
                down = list(np.array((0, -1))*TILESIZE)
                left = list(np.array((-1, 0))*TILESIZE)
                right = list(np.array((1, 0))*TILESIZE)

                actions = [(action, self.V_s.get(tuple(np.array(observation)+np.array(action)), 0)) for action in [up, down, left, right]]
                actions.sort(key=lambda x: x[1])


                if np.random.uniform() > 1-EXPLORATION_RATE:
                    self.outqueue.put((pg.KEYDOWN, [pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT][np.random.randint(0, 4)]))
                elif actions[-1][0] == up:
                    self.outqueue.put((pg.KEYDOWN, pg.K_UP))
                elif actions[-1][0] == down:
                    self.outqueue.put((pg.KEYDOWN, pg.K_DOWN))
                elif actions[-1][0] == left:
                    self.outqueue.put((pg.KEYDOWN, pg.K_LEFT))
                elif actions[-1][0] == right:
                    self.outqueue.put((pg.KEYDOWN, pg.K_RIGHT))


            # For deep learning: Load up the model in __init__ and call it here
            # For table-based Q-learning:
            #   Load up the table in __init__ and call/update it here
        
        # Take from inqueue -> observation
        # Use observation to select next action
        # Post action to outqueue
                
