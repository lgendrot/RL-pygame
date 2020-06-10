import multiprocessing
import queue
import time
import pygame as pg
import numpy as np
from settings import TILESIZE, EXPLORATION_RATE, EPSILON_UPDATE_RATE, REWARD_DISCOUNT

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
        episode_number = 1
        epsilon = EXPLORATION_RATE
        while True:
            observation = self.inqueue.get()
            if observation is None:
                print("Quitting...")
                break
            elif isinstance(observation, tuple) and observation[0] == "NEW_GAME":
                episode_number += 1
                #print(self.N_s)
                G = 0
                state_rewards = {}
                for idx, observation in enumerate(episode_list):
                    
                    state = observation['state']
                    reward = observation['reward']

                    G = 0
                    for idx, step in enumerate(episode_list[idx:]):
                        G += (REWARD_DISCOUNT**(idx+1))*step['reward']

                    
                    
                    self.V_s[state] += ((1/self.N_s[state])*(G - self.V_s[state]))
                
                self.outqueue.put((pg.KEYDOWN, pg.K_DOWN))
                self.debug_queue.put(self.V_s)
                episode_list = []

                if episode_number % EPSILON_UPDATE_RATE == 0:
                    epsilon *= epsilon
            else:
                episode_list.append(observation)
                if self.N_s.get(observation['state'], None):
                    self.N_s[observation['state']] += 1
                else:
                    self.N_s[observation['state']] = 1
                    self.V_s[observation['state']] = 0


            # Get surrounding squares:

                up = list(np.array((0, -1))*TILESIZE)
                down = list(np.array((0, 1))*TILESIZE)
                left = list(np.array((-1, 0))*TILESIZE)
                right = list(np.array((1, 0))*TILESIZE)

                actions = [right, up, down, left]
                best_action = None
                best_v = -1000000
                for action in actions:
                    next_state = np.array(observation['state']) + np.array(action)
                    next_state = tuple(next_state)
                    action_value = self.V_s.get(next_state, 0)
                    if action_value > best_v:
                        best_v = action_value
                        best_action = action

                print("Best action: ", best_action)



                if np.random.uniform() > 1-epsilon:
                    print("Random Action!")
                    print("EPSILON: ", epsilon)
                    print("EPISODE: ", episode_number)
                    self.outqueue.put((pg.KEYDOWN, [pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT][np.random.randint(0, 4)]))
                elif best_action == up:
                    self.outqueue.put((pg.KEYDOWN, pg.K_UP))
                elif best_action == down:
                    self.outqueue.put((pg.KEYDOWN, pg.K_DOWN))
                elif best_action == left:
                    self.outqueue.put((pg.KEYDOWN, pg.K_LEFT))
                elif best_action == right:
                    self.outqueue.put((pg.KEYDOWN, pg.K_RIGHT))


            # For deep learning: Load up the model in __init__ and call it here
            # For table-based Q-learning:
            #   Load up the table in __init__ and call/update it here
        
        # Take from inqueue -> observation
        # Use observation to select next action
        # Post action to outqueue
                
