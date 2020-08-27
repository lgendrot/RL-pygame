import multiprocessing
import queue
import time
import pygame as pg
import numpy as np
from settings import *

# TODO: Monte Carlo: Make equal-value state_action choices a random choice
# TODO: Monte Carlo: Functions functions functions

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
        actions = {
            "up": (0, -TILESIZE),
            "down": (0, TILESIZE),
            "left": (-TILESIZE, 0),
            "right": (TILESIZE, 0)
	}

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
                    epsilon *= EPSILON_DECAY

                self.outqueue.put((pg.KEYDOWN, pg.K_SPACE))
                self.debug_queue.put((episode_number, self.Q_s))

                print("Episode: {} Epsilon: {}".format(episode_number, epsilon))
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



                if np.random.uniform() > 1-epsilon:
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


class SARSA(AIController):
    def __init__(self):
        super().__init__()
        self.previous_sa = (None, None)
        self.Q = dict()
        self.actions = {
            "up": (pg.KEYDOWN, pg.K_UP),
            "down": (pg.KEYDOWN, pg.K_DOWN),
            "left": (pg.KEYDOWN, pg.K_LEFT),
            "right": (pg.KEYDOWN, pg.K_RIGHT)
        }
        self.episode_number = 1
        self.epsilon = EXPLORATION_RATE
        self.first_state = None


    def run(self):
        while True:
            observation = self.inqueue.get()

            if observation is None:
                print("Quitting...")
                break
            elif isinstance(observation, tuple) and observation[0] == "NEW_GAME":
                self.new_game()
            else:
                self.act(observation)



    def act(self, observation):

        state = observation['state']
        action = self.policy(state)

        reward = observation['reward']
        delta = reward + (REWARD_DISCOUNT*self.Q.get((state, action), 0))

        # Update Q Value
        old_qa = self.Q.get(self.previous_sa, 0)
        self.Q[self.previous_sa] = old_qa + (ALPHA*(delta - old_qa))
        self.previous_sa = (state, action)


        if self.first_state is None:
            self.first_state = state


        if np.random.uniform() >= 1-self.epsilon:
            random_action = np.random.randint(0, 4)
            random_action = [a for a in self.actions][random_action]
            self.outqueue.put(self.actions[random_action])
        else:
            self.outqueue.put(self.actions[action])

        # Record old state_action
        # Take New state_action
        # Update Q_a


    def policy(self, state):
        best_value = -1000000000
        best_action = None
        for action in self.actions:
            state_action = (state, action)
            sa = self.Q.get(state_action, 0)
            if sa > best_value:
                best_action = action
                best_value = sa
        return best_action



    def new_game(self):
        # Reset episode state
        self.episode_number += 1
        self.previous_sa = (None, None)
        self.epsilon = self.epsilon * EPSILON_DECAY

        # Janktastic way to get the best first_state, action pair from the Q table
        start_states = [(self.Q.get((self.first_state, action), 0), action) for action in self.actions]
        start_states.sort(key=lambda x: x[0])

        print("Episode: ", self.episode_number, "Epsilon: ", self.epsilon, "V(start): ", start_states[-1])
        self.outqueue.put((pg.KEYDOWN, pg.K_SPACE))

        self.first_state = None



class SARSAL(AIController):
    def __init__(self, lamb=.8):
        super().__init__()
        self.previous_sa = (None, None)
        self.Q = dict()
        self.actions = {
            "up": (pg.KEYDOWN, pg.K_UP),
            "down": (pg.KEYDOWN, pg.K_DOWN),
            "left": (pg.KEYDOWN, pg.K_LEFT),
            "right": (pg.KEYDOWN, pg.K_RIGHT)
        }
        self.episode_number = 1
        self.epsilon = EXPLORATION_RATE
        self.first_state = None

        # dict -> {(state, action): eligibility}
        self.traces = {}
        self.lamb = lamb




    def run(self):
        while True:
            observation = self.inqueue.get()

            if observation is None:
                print("Quitting...")
                break
            elif isinstance(observation, tuple) and observation[0] == "NEW_GAME":
                self.new_game()
            else:
                self.act(observation)




    def act(self, observation):

        state = observation['state']
        action = self.policy(state)

        reward = observation['reward']
        delta = reward + (REWARD_DISCOUNT*self.Q.get((state, action), 0))
        old_qa = self.Q.get(self.previous_sa, 0)
        delta = delta - old_qa
        self.traces[self.previous_sa] = self.traces.get(self.previous_sa, 0) + 1
        # Update Q Value for ALL STATES in self.traces

        for s_a in self.traces:
            self.Q[s_a] = self.Q.get(s_a, 0) + (ALPHA*delta*self.traces[s_a])
            self.traces[s_a] *= REWARD_DISCOUNT*self.lamb

        self.previous_sa = (state, action)

        if self.first_state is None:
            self.first_state = state


        if np.random.uniform() >= 1-self.epsilon:
            random_action = np.random.randint(0, 4)
            random_action = [a for a in self.actions][random_action]
            self.outqueue.put(self.actions[random_action])
        else:
            self.outqueue.put(self.actions[action])



    def policy(self, state):
        best_value = -1000000000
        best_action = None
        for action in self.actions:
            state_action = (state, action)
            sa = self.Q.get(state_action, 0)
            if sa > best_value:
                best_action = action
                best_value = sa
        return best_action



    def new_game(self):
        # Reset episode state
        self.episode_number += 1
        self.previous_sa = (None, None)
        self.epsilon = self.epsilon * EPSILON_DECAY

        # Janktastic way to get the best first_state, action pair from the Q table
        start_states = [(self.Q.get((self.first_state, action), 0), action) for action in self.actions]
        start_states.sort(key=lambda x: x[0])

        print("Episode: ", self.episode_number, "Epsilon: ", self.epsilon, "V(start): ", start_states[-1])
        self.outqueue.put((pg.KEYDOWN, pg.K_SPACE))

        self.first_state = None
        self.traces = {}




