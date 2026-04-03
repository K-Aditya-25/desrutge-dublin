from collections import OrderedDict

from stable_baselines3 import PPO

import time

import gymnasium as gym
from gymnasium import spaces

import numpy as np
import torch

from .SIMULA import simulacion
from .sumo_site_metrics import combine_hourly_profiles, compute_profile_metrics


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
    profile = normalize_profile(testloader) * Norma
    return [profile.tolist()[:] for _ in range(num_episodes)]


def normalize_profile(values):
    profile = np.asarray(values, dtype=np.float32).reshape(-1)
    if profile.shape[0] != 24:
        raise ValueError(f"Traffic_Generator expects exactly 24 hourly targets, found {profile.shape[0]}.")
    return profile / Norma


def denormalize_profile(values):
    return (np.asarray(values, dtype=np.float32) * Norma).tolist()


def normalize_scalar(value):
    return float(max(0.0, float(value))) / Norma


def denormalize_scalar(value):
    return float(value) * Norma


class Traffic_Generation_Algorithms:
    """
    PPO-based hourly traffic generator.

    One environment step corresponds to one hourly calibration attempt.
    Full-day profiles are produced by sequentially chaining 24 hourly
    calibrations while carrying forward detector spillover into later hours.
    """

    def __init__(self, conf):
        self.model = None
        self.trained_rounds = 0
        print("T0:", time.time())

    def _build_hour_env(self, target_schedule, conf):
        return HourlyTrafficEnv(
            target_schedule,
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
            end = init + tensor_parameter.numel()
            recovered_tensor = torch.tensor(updated_model[init:end], dtype=tensor_parameter.dtype)
            recovered_tensor = recovered_tensor.view(tensor_parameter.shape)
            parameters.append(recovered_tensor)
            init = end

        params_dict = zip(self.model.policy.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.Tensor(v) for k, v in params_dict})
        self.model.policy.load_state_dict(state_dict, strict=True)
        return

    def train_model(self, trainloader, conf):
        steps, rollout_steps, batch_size = self._resolve_ppo_rollout_config(conf)
        if self.model is None:
            env = self._build_hour_env(trainloader, conf)
            self.model = PPO(
                "MlpPolicy",
                env,
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
                verbose=1,
            )

        self.model.learn(total_timesteps=steps)
        return

    def test_model(self, testloader, conf):
        num_episodes = max(1, int(conf.get("traffic_test_episodes", DEFAULT_TRAFFIC_TEST_EPISODES)))
        target_profiles = resolve_test_targets(testloader, num_episodes)

        completion_scores = []
        metrics_history = []
        last_target_profile = [0.0] * 24
        last_output_profile = [0.0] * 24
        last_remaining_profile = [0.0] * 24

        for target_profile in target_profiles:
            simulated_profile, remaining_profile, completion_score = self._run_daily_profile(target_profile, conf)
            metrics = compute_profile_metrics(target_profile, simulated_profile)
            metrics_history.append(metrics)
            completion_scores.append(completion_score)
            last_target_profile = target_profile
            last_output_profile = simulated_profile
            last_remaining_profile = remaining_profile

        average_hourly_error = [
            float(np.mean([metrics["hourly_error"][hour] for metrics in metrics_history]))
            for hour in range(24)
        ]
        average_hourly_absolute_error = [
            float(np.mean([metrics["hourly_absolute_error"][hour] for metrics in metrics_history]))
            for hour in range(24)
        ]

        print("T:", time.time())

        return {
            "rewards": float(np.mean(completion_scores)),
            "output": last_output_profile,
            "target": last_target_profile,
            "simulated_profile": last_output_profile,
            "target_profile": last_target_profile,
            "remaining_target_profile": last_remaining_profile,
            "hourly_error": average_hourly_error,
            "hourly_absolute_error": average_hourly_absolute_error,
            "profile_mae": float(np.mean([metrics["mae"] for metrics in metrics_history])),
            "profile_rmse": float(np.mean([metrics["rmse"] for metrics in metrics_history])),
            "total_target": float(np.mean([metrics["total_target"] for metrics in metrics_history])),
            "total_simulated": float(np.mean([metrics["total_simulated"] for metrics in metrics_history])),
            "daily_mean_target": float(np.mean([metrics["daily_mean_target"] for metrics in metrics_history])),
            "daily_mean_simulated": float(np.mean([metrics["daily_mean_simulated"] for metrics in metrics_history])),
        }

    def _run_daily_profile(self, target_profile, conf):
        carryover_profile = [0.0] * 24
        simulated_profile = [0.0] * 24
        remaining_profile = [0.0] * 24
        completed_hours = 0

        for hour, target_value in enumerate(target_profile):
            carry_in = carryover_profile[hour]
            remaining_target = max(0.0, float(target_value) - carry_in)
            remaining_profile[hour] = remaining_target

            if remaining_target <= 0:
                simulated_profile[hour] = carry_in
                continue

            current_output, residual_profile, completed = self._run_single_hour_generator(remaining_target, conf)
            simulated_profile[hour] = carry_in + current_output
            completed_hours += int(completed)

            for offset, residual_value in enumerate(residual_profile, start=1):
                future_hour = hour + offset
                if future_hour >= 24:
                    break
                carryover_profile[future_hour] += residual_value

        return simulated_profile, remaining_profile, completed_hours / 24.0

    def _run_single_hour_generator(self, target_value, conf):
        env = self._build_hour_env([target_value], conf)
        obs, _ = env.reset()
        done = False

        while not done:
            action, _ = self.model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

        current_output = denormalize_scalar(env.out)
        residual_profile = [float(value) for value in env.remanente]
        completed = env.last_terminated
        env.close()
        return current_output, residual_profile, completed

    def init_model(self, trainloader, conf):
        if self.model is None:
            _, rollout_steps, batch_size = self._resolve_ppo_rollout_config(conf)
            env = self._build_hour_env(trainloader, conf)
            self.model = PPO(
                "MlpPolicy",
                env,
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
                verbose=1,
            )
        return


class HourlyTrafficEnv(gym.Env):
    def __init__(
        self,
        target_schedule,
        Norma,
        node_id,
        traffic_simulation_mode=DEFAULT_TRAFFIC_SIMULATION_MODE,
        max_steps=DEFAULT_TRAFFIC_EPISODE_MAX_STEPS,
    ):
        super().__init__()
        raw_targets = np.asarray(target_schedule, dtype=np.float32).reshape(-1)
        if raw_targets.size == 0:
            raise ValueError("HourlyTrafficEnv requires at least one hourly target.")

        self.target_schedule = [normalize_scalar(value) for value in raw_targets]
        self.observation_space = spaces.Box(low=0, high=3, shape=(2,), dtype=np.float32)
        self.action_space = spaces.Box(low=-0.5, high=0.5, shape=(1,), dtype=np.float32)

        self.state = None
        self.out = None
        self.remanente = None
        self.num_steps = 0
        self.max_steps = int(max_steps)
        self.max_steps_limit = int(max_steps)
        self.current_target = 0.0
        self.current_target_index = 0
        self.last_terminated = False

        self.Norma = Norma
        self.node_id = node_id
        self.traffic_simulation_mode = traffic_simulation_mode

    def step(self, action):
        multiplier = float(np.asarray(action, dtype=np.float32).reshape(-1)[0])
        demand_multiplier = float(np.clip(self.state[0] + (self.state[0] * multiplier), 0.0, 3.0))
        if self.current_target > 0:
            demand_multiplier = max(demand_multiplier, 0.001)

        self.state = np.array([demand_multiplier, self.current_target], dtype=np.float32)
        self.remanente = [0.0] * 23

        injected_demand = self.state[0] * self.current_target
        if self.traffic_simulation_mode == "sumo":
            output, self.remanente = self.generate_output_SUMO(injected_demand)
        else:
            output, self.remanente = self.generate_output_Test(injected_demand)

        reward = -abs(self.current_target - output)
        self.num_steps += 1

        terminated = False
        truncated = False
        if abs(self.current_target - output) < 0.001:
            reward += 10
            terminated = True

        if self.num_steps >= self.max_steps:
            reward -= 0.5
            truncated = True

        self.out = output
        self.last_terminated = terminated
        return self.state.astype(np.float32), float(reward), terminated, truncated, {}

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.num_steps = 0
        self.max_steps = self.max_steps_limit
        self.current_target = self.target_schedule[self.current_target_index % len(self.target_schedule)]
        self.current_target_index += 1
        self.state = np.array([1.0, self.current_target], dtype=np.float32)
        self.out = 0.0
        self.remanente = [0.0] * 23
        self.last_terminated = False
        print("Reset:", self.state)
        return self.state, {}

    def generate_output_SUMO(self, normalized_injected_demand):
        fix_state = int(float(normalized_injected_demand) * self.Norma)
        if fix_state <= 0:
            return 0.0, [0.0] * 23

        per_detector_profiles = simulacion(fix_state, str(self.node_id))
        combined_profile = combine_hourly_profiles(per_detector_profiles)
        if not combined_profile:
            return 0.0, [0.0] * 23

        current_output = float(combined_profile[0]) / self.Norma
        residual_profile = [float(value) for value in combined_profile[1:24]]
        if len(residual_profile) < 23:
            residual_profile.extend([0.0] * (23 - len(residual_profile)))

        return current_output, residual_profile[:23]

    def generate_output_Test(self, normalized_injected_demand):
        demand = float(normalized_injected_demand) * self.Norma
        output = (-6.47e-05 * demand) + (0.7171 * demand) + 0.3595
        return output / self.Norma, [0.0] * 23
