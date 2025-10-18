from collections import OrderedDict
from sklearn.metrics import *

from stable_baselines3 import PPO
from itertools import zip_longest


import time

import gym
from gym import spaces

import random
import numpy as np
import torch

from .SIMULA import simulacion

#Normalizacion global
Norma = 10000

# #############################################################################
# General ML Pipeline: Model Training, and Testing
# #############################################################################
class Traffic_Generation_Algorithms:
    """
    Generalized class for Machine Learning models.
    """
    def __init__(self, conf):
        self.model = None
        self.trained_rounds = 0
        print("T0:", time.time())
    
    def get_params(self):
        model_params = [val.cpu().numpy() for _, val in self.model.policy.state_dict().items()]
        return np.concatenate(model_params, axis=None).ravel()

    def set_params(self, updated_model):
        parameters = []
        init = 0
        for _, tensor_parameter in self.model.policy.state_dict().items():
            end = init + tensor_parameter.numel()  # number of elements in tensor
            recovered_tensor = torch.tensor(updated_model[init:end], dtype=tensor_parameter.dtype)
            recovered_tensor = recovered_tensor.view(tensor_parameter.shape)
            parameters.append(recovered_tensor)
            init = end

        params_dict = zip(self.model.policy.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.Tensor(v) for k, v in params_dict})
        self.model.policy.load_state_dict(state_dict, strict=True)
        return

    def train_model(self, trainloader, conf):
        """Train the ML algorithm on the training set."""
        if self.model == None:

            target = np.mean(trainloader) / Norma

            env = CustomEnv(target, Norma, conf["node_id"])
        
            self.model = PPO('MlpPolicy', env,
                    learning_rate=0.0003,
                    n_steps=64,
                    batch_size=64,
                    n_epochs=4,
                    gamma=0.95,
                    gae_lambda=0.95,
                    clip_range=0.2,
                    ent_coef=0.01,
                    vf_coef=0.5,
                    max_grad_norm=0.5,
                    verbose=1)
        
        steps = 100
        self.model.learn(total_timesteps=steps)
        return
        
    def test_model(self, testloader, conf):
        """Validate the ML algorithm on the entire test set."""
        rewards = []
        out = []
        num_episodes = 10

        target = np.linspace(min(testloader), max(testloader), num_episodes ) / Norma

        error = 0
        e = 0
        dones = 0

        for i in range(num_episodes):

            env = CustomEnv(target[i], Norma, conf["node_id"])

            obs = env.reset()
            done = False
            
            while not done:
                # El modelo predice la acción a tomar
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, done, _ = env.step(action)
            
                # Agregar la recompensa total de este episodio a la lista
                if isinstance(reward, float):
                    rewards.append(reward)
                    aux = env.out * Norma
                else:
                    rewards.append(reward[0])
                    aux = env.out[0] * Norma
                
                out.append(aux)
                e = (target[i] * Norma) - aux

            
            if ( done == True ):
                dones = dones + 1
            
            error = error + e

            env.close()
        
        aciertos = dones / num_episodes
        MAE = error / num_episodes

        print("T:", time.time())

        return {
            "rewards": aciertos,
            "output": MAE,
            "target": target[-1] * Norma
        }
    
    def init_model(self, trainloader, conf):
        """Init the ML algorithm on the training set."""
        if self.model == None:
            target = np.mean(trainloader) / Norma
            env = CustomEnv(target, Norma, conf["node_id"])
            self.model = PPO('MlpPolicy', env,
                    learning_rate=0.0003,
                    n_steps=64,
                    batch_size=64,
                    n_epochs=4,
                    gamma=0.95,
                    gae_lambda=0.95,
                    clip_range=0.2,
                    ent_coef=0.01,
                    vf_coef=0.5,
                    max_grad_norm=0.5,
                    verbose=1)
        return


class CustomEnv(gym.Env):
    def __init__(self, target, Norma, node_id):
        super(CustomEnv, self).__init__()
        self.target = target
        self.observation_space = spaces.Box(low=0, high=3, shape=(1,), dtype=np.float32)
        self.action_space = spaces.Box(low=-0.5, high=0.5, shape=(1,), dtype=np.float32)
        
        self.state = None
        self.out = None
        self.num_steps = None
        self.max_steps = None
        self.remanente = None

        self.Norma = Norma
        self.node_id = node_id

    def step(self, action):
        multiplicador = action[0]
        self.remanente = [0] * 24

        self.state = np.clip(self.state + self.state * multiplicador, 0.001, 3)
        coches = self.state * self.target
        
        # output, self.remanente = self.generate_output_SUMO(coches)
        output, self.remanente = self.generate_output_Test(coches)
        
        reward = -np.abs(self.target - output)
        self.num_steps += 1

        done = False

        umbral = 0.001

        if abs(self.target - output) < umbral:
            reward += 10
            done = True
        
        if self.num_steps >= self.max_steps:
            reward -= 0.5
            done = True

        return self.state, reward, done, {}

    def reset(self):
        self.state = np.array([1.0])
        self.num_steps = 0
        self.max_steps = 10

        print("Reset:", self.state)
        return self.state

    def generate_output_SUMO(self, state):
        intensidad_promedio = 0
        remanente = [0] * 24

        fix_state = state * self.Norma
        out = simulacion(int(fix_state), str(self.node_id))

        for o in out:
            lista = o
            intensidad = lista[0]
            remanente = [x + y for x, y in zip_longest(remanente, lista[1:-1], fillvalue=0)]
            intensidad_promedio += intensidad

        output = intensidad_promedio / self.Norma

        self.out = output

        return output, remanente
    
    def generate_output_Test(self, state):
        
        remanente = [0] * 24

        a = int(state)
        a = a * self.Norma
        
        output = -6.47e-05 * a + 0.7171 * a + 0.3595

        output = output / self.Norma

        self.out = output

        return output, remanente
