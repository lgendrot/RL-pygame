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
        self.Q_s = dict()
        self.N_s = dict()


    def run(self):
        episode_list = []
        episode_number = 1
        epsilon = EXPLORATION_RATE
        actions = {"up": (0, -TILESIZE), "down": (0, TILESIZE), "left": (-TILESIZE, 0), "right": (TILESIZE, 0)}

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
                    action = observation['action']
                    reward = observation['reward']


                    G = 0
                    for idx, step in enumerate(episode_list[idx:]):
                        G += (REWARD_DISCOUNT**(idx+1))*step['reward']

                    
                    state_action = (state, action) 
                    self.Q_s[state_action] += ((1/self.N_s[state_action])*(G - self.Q_s[state_action]))
                
                episode_list = []

                if episode_number % EPSILON_UPDATE_RATE == 0:
                    epsilon *= epsilon

                self.outqueue.put((pg.KEYDOWN, pg.K_SPACE))
                self.debug_queue.put((episode_number, self.Q_s))
            else:
                   
            # Get surrounding squares:

                best_action = None
                best_v = -1000000
                for action in actions:
                    s_a = (observation['state'], action) 
                    state_action_value = self.Q_s.get(s_a, 0)
                    if state_action_value >= best_v:
                        best_v = state_action_value
                        best_action = action

                print("Best action: ", best_action)


                if np.random.uniform() > 1-epsilon:
                    print("Random Action!")
                    print("EPSILON: ", epsilon)
                    print("EPISODE: ", episode_number)
                    random_idx = np.random.randint(0, 4)
                    keys = [pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT]
                    self.outqueue.put((pg.KEYDOWN, keys[random_idx]))
                    observation['action'] = ["up", "down", "left", "right"][random_idx]
                elif best_action == 'up':
                    self.outqueue.put((pg.KEYDOWN, pg.K_UP))
                    observation['action'] = best_action
                elif best_action == 'down':
                    self.outqueue.put((pg.KEYDOWN, pg.K_DOWN))
                    observation['action'] = best_action
                elif best_action == 'left':
                    self.outqueue.put((pg.KEYDOWN, pg.K_LEFT))
                    observation['action'] = best_action
                elif best_action == 'right':
                    self.outqueue.put((pg.KEYDOWN, pg.K_RIGHT))
                    observation['action'] = best_action


                state_action = (observation['state'], observation['action'])
                if self.N_s.get(state_action, 0): 
                    self.N_s[state_action] += 1  
                else:
                    self.N_s[state_action] = 1


                if not self.Q_s.get(state_action, False):
                    self.Q_s[state_action] = 0
                episode_list.append(observation) 

            # For deep learning: Load up the model in __init__ and call it here
            # For table-based Q-learning:
            #   Load up the table in __init__ and call/update it here
        
        # Take from inqueue -> observation
        # Use observation to select next action
        # Post action to outqueue
                
