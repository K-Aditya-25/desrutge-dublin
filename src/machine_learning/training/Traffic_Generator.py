from collections import OrderedDict
from sklearn.metrics import *

from stable_baselines3 import PPO

import time

import gymnasium as gym
from gymnasium import spaces

import random
import numpy as np
import torch

from .SIMULA import simulacion
from .sumo_site_metrics import combine_hourly_profiles, profile_mean

#Normalizacion global
Norma = 10000
DEFAULT_TRAFFIC_SIMULATION_MODE = "sumo"
SUPPORTED_TRAFFIC_SIMULATION_MODES = {"sumo", "test"}
DEFAULT_TRAFFIC_TOTAL_TIMESTEPS = 100
DEFAULT_TRAFFIC_EPISODE_MAX_STEPS = 10
DEFAULT_TRAFFIC_TEST_EPISODES = 10


def resolve_traffic_simulation_mode(conf):
    mode = str(conf.get("traffic_simulation_mode", DEFAULT_TRAFFIC_SIMULATION_MODE)).lower()
    if mode not in SUPPORTED_TRAFFIC_SIMULATION_MODES:
        raise ValueError(
            "Unsupported traffic_simulation_mode "
            f"{mode!r}. Expected one of {sorted(SUPPORTED_TRAFFIC_SIMULATION_MODES)}."
        )
    return mode


def resolve_test_targets(testloader, num_episodes):
    if num_episodes <= 1:
        return np.array([float(np.mean(testloader))], dtype=np.float32) / Norma

    return np.linspace(min(testloader), max(testloader), num_episodes, dtype=np.float32) / Norma

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

    def _build_env(self, target, conf):
        return CustomEnv(
            target,
            Norma,
            conf["node_id"],
            resolve_traffic_simulation_mode(conf),
            int(conf.get("traffic_episode_max_steps", DEFAULT_TRAFFIC_EPISODE_MAX_STEPS)),
        )

    def _resolve_ppo_rollout_config(self, conf):
        total_timesteps = max(1, int(conf.get("traffic_total_timesteps", DEFAULT_TRAFFIC_TOTAL_TIMESTEPS)))
        rollout_steps = min(64, max(2, total_timesteps))
        batch_size = rollout_steps
        return total_timesteps, rollout_steps, batch_size
    
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
        steps, rollout_steps, batch_size = self._resolve_ppo_rollout_config(conf)
        if self.model == None:

            target = np.mean(trainloader) / Norma

            env = self._build_env(target, conf)
        
            self.model = PPO('MlpPolicy', env,
                    learning_rate=0.0003,
                    n_steps=rollout_steps,
                    batch_size=batch_size,
                    n_epochs=4,
                    gamma=0.95,
                    gae_lambda=0.95,
                    clip_range=0.2,
                    ent_coef=0.01,
                    vf_coef=0.5,
                    max_grad_norm=0.5,
                    verbose=1)

        self.model.learn(total_timesteps=steps)
        return
        
    def test_model(self, testloader, conf):
        """Validate the ML algorithm on the entire test set."""
        rewards = []
        out = []
        num_episodes = max(1, int(conf.get("traffic_test_episodes", DEFAULT_TRAFFIC_TEST_EPISODES)))

        target = resolve_test_targets(testloader, num_episodes)

        error = 0
        e = 0
        dones = 0

        for i in range(num_episodes):

            env = self._build_env(target[i], conf)

            obs, _ = env.reset()
            done = False
            
            while not done:
                # El modelo predice la acción a tomar
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
            
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
            _, rollout_steps, batch_size = self._resolve_ppo_rollout_config(conf)
            target = np.mean(trainloader) / Norma
            env = self._build_env(target, conf)
            self.model = PPO('MlpPolicy', env,
                    learning_rate=0.0003,
                    n_steps=rollout_steps,
                    batch_size=batch_size,
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
    def __init__(
        self,
        target,
        Norma,
        node_id,
        traffic_simulation_mode=DEFAULT_TRAFFIC_SIMULATION_MODE,
        max_steps=DEFAULT_TRAFFIC_EPISODE_MAX_STEPS,
    ):
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
        self.traffic_simulation_mode = traffic_simulation_mode
        self.max_steps_limit = int(max_steps)

    def step(self, action):
        multiplicador = action[0]
        self.remanente = [0] * 24

        self.state = np.clip(self.state + self.state * multiplicador, 0.001, 3)
        coches = self.state * self.target

        if self.traffic_simulation_mode == "sumo":
            output, self.remanente = self.generate_output_SUMO(coches)
        else:
            output, self.remanente = self.generate_output_Test(coches)
        
        reward = -np.abs(self.target - output)
        self.num_steps += 1

        terminated = False
        truncated = False

        umbral = 0.001

        if abs(self.target - output) < umbral:
            reward += 10
            terminated = True
        
        if self.num_steps >= self.max_steps:
            reward -= 0.5
            truncated = True

        return self.state, reward, terminated, truncated, {}

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.array([1.0])
        self.num_steps = 0
        self.max_steps = self.max_steps_limit

        print("Reset:", self.state)
        return self.state, {}

    def generate_output_SUMO(self, state):
        remanente = [0] * 24

        fix_state = state * self.Norma
        if int(fix_state) <= 0:
            self.out = 0.0
            return 0.0, remanente
        out = simulacion(int(fix_state), str(self.node_id))
        remanente = combine_hourly_profiles(out)

        # Keep the PPO interface scalar while aligning it with the 24-hour site profile:
        # the scalar output is now the daily mean of the simulated detector profile.
        output = profile_mean(remanente) / self.Norma

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
