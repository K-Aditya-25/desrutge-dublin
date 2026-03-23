import threading
import multiprocessing
import time
from pathlib import Path

import torch

from entities.centralized_client import CentralizeClient
from entities.decentralized_client import DecentralizeClient
from entities.malicious_centralized_client import MaliciousCentralizeClient
from entities.malicious_decentralized_client import MaliciousDecentralizeClient
from entities.parameter_server import ParameterServer
from utils.utils_logs import *
from machine_learning.metrics.utils import R_squared_models

from typing import Dict, Any, List, Union


def resolve_node_loader(loaders, node_key, index):
    if isinstance(loaders, dict):
        return loaders[str(node_key)]
    return loaders[index]


def snapshot_shared_mapping(shared_mapping):
    return {str(key): value for key, value in shared_mapping.items()}


def build_export_ready_model(model_class, sim_config, node_key, trainloader):
    config_aux = sim_config["conf_nodes"].copy()
    config_aux["node_id"] = str(node_key)
    model_aux = model_class(config_aux)
    if hasattr(model_aux, "init_model"):
        model_aux.init_model(trainloader, config_aux)
    return model_aux


def save_model_artifact(model_aux, node_key):
    if hasattr(model_aux, "model") and model_aux.model is not None and hasattr(model_aux.model, "save"):
        output_path = Path(f"./ppo_simulador_prueba_{node_key}.zip")
        model_aux.model.save(str(output_path))
        return str(output_path)

    if hasattr(model_aux, "state_dict"):
        output_path = Path(f"./model_simulador_prueba_{node_key}.pt")
        torch.save(model_aux.state_dict(), output_path)
        return str(output_path)

    raise RuntimeError(f"Unable to save model artifact for node {node_key}.")


def export_node_models(shared_models, ordered_node_keys, model_class, trainloaders, sim_config):
    if not shared_models:
        log_warning("Node-model export was requested, but no shared model history was collected.")
        return

    export_started = time.perf_counter()
    log_info("Exporting node models from the final in-memory parameters...")

    for index, node_key in enumerate(ordered_node_keys):
        node_statistics = shared_models.get(str(node_key))
        if not node_statistics:
            log_warning(f"Skipping node-model export for node {node_key}: no model history found.")
            continue

        last_model = node_statistics[-1]
        trainloader = resolve_node_loader(trainloaders, node_key, index)
        model_aux = build_export_ready_model(model_class, sim_config, node_key, trainloader)
        model_aux.set_params(last_model)
        output_path = save_model_artifact(model_aux, node_key)
        log_info(f"Saved node model for {node_key} to {output_path}")

    export_elapsed = time.perf_counter() - export_started
    log_info(f"Node-model export completed in {export_elapsed:.2f}s")

def decentralized_simulation(
    sim_config: Dict[str, Any], 
    nodes_config: Dict[str, Any], 
    model_class,
    trainloaders, 
    valloaders,
    **kwargs
    ) -> Dict[str, Any]:
    """
    Simulates a decentralized federated learning process across multiple nodes.

    Args:
        sim_config: General simulation configuration (e.g., global hyperparameters).
        nodes_config: Specific configuration for each node.
        model_class: Python class of the training algorithm
        trainloaders: List of data loaders for training on each node.
        valloaders: List of data loaders for validation on each node.

    Returns:
        simulation_results: Results of the simulation, which may include performance metrics, statistics, etc.
    """
    simulation_started = time.perf_counter()
    nodes = {}
    
    barrier_sim = ProcessBarrier(len(nodes_config))             # Synchronization barrier for nodes
    # barrier_sim = threading.Barrier(len(nodes_config))      

    for index, (key, value) in enumerate(nodes_config.items()):
        trainloader = resolve_node_loader(trainloaders, key, index)
        valloader = resolve_node_loader(valloaders, key, index)

        if value['id'] in sim_config["malicious_nodes"]:
            # Create instances of MaliciousDecentralizeNode
            nodes[key] = MaliciousDecentralizeClient(
                node_id=value['id'], 
                ip=value['ip'], 
                port=value['port'], 
                neighbors= [nodes_config[str(i)] for i in value['neighbors']], 
                dataset=sim_config["dataset"],
                model=model_class(sim_config["conf_nodes"]),
                trainloader=trainloader,
                testloader=valloader,
                rounds=sim_config["rounds"],
                aggregation_alg=sim_config["algorithm"],
                aggregation_config=sim_config.get("algorithm_config", None),
                conf_nodes=sim_config["conf_nodes"],
                barrier_sim=barrier_sim,
                gossip_share=sim_config["gossip_share"],
                byz_attack=sim_config["byz_attack"],
                attack_config=sim_config.get("attack_config", None)
            )
        else:
            # Create instances of DecentralizeNode
            nodes[key] = DecentralizeClient(
                node_id=value['id'], 
                ip=value['ip'], 
                port=value['port'], 
                neighbors= [nodes_config[str(i)] for i in value['neighbors']], 
                dataset=sim_config["dataset"],
                model=model_class(sim_config["conf_nodes"]),
                trainloader=trainloader,
                testloader=valloader,
                rounds=sim_config["rounds"],
                aggregation_alg=sim_config["algorithm"],
                aggregation_config=sim_config.get("algorithm_config", None),
                conf_nodes=sim_config["conf_nodes"],
                barrier_sim=barrier_sim,
                gossip_share=sim_config["gossip_share"]
            )
    
    TaskExecutor = multiprocessing.Process 
    manager = multiprocessing.Manager()
    shared_results = manager.dict()
    shared_models = manager.dict()
    # TaskExecutor = threading.Thread
    # shared_results = {}
    
    # Run the training process in separate threads/process for each node
    # tasks: List[Union[threading.Thread, multiprocessing.Process]] = []
    tasks = []
    for key, decentralized_node in nodes.items():
        print("Node ID init:", decentralized_node.node_id)
        task = TaskExecutor(target=run_node, args=(decentralized_node, shared_results, shared_models))
        task.start()
        tasks.append(task)

    # Wait for all threads to finish
    for task in tasks:
        task.join()
        print("Task joined")

    shared_results_local = snapshot_shared_mapping(shared_results)
    shared_models_local = snapshot_shared_mapping(shared_models)
    ordered_node_keys = list(nodes.keys())

    if not shared_results_local:
        raise RuntimeError("Decentralized simulation finished without collecting any node statistics.")

    evaluate_metrics = shared_results_local[next(iter(shared_results_local))].keys()
    simulation_results = {metric: {} for metric in evaluate_metrics}
    simulation_results["R-Squared"] = []
    
    for key in ordered_node_keys:
        node_statistics = shared_results_local[str(key)]
        for metric in evaluate_metrics:
            simulation_results[metric][key] = node_statistics[metric] 
    
    for round in range(int(sim_config["rounds"])):
        models_round = []
        for key in ordered_node_keys:
            node_statistics = shared_models_local[str(key)]
            models_round.append(node_statistics[round])
        simulation_results["R-Squared"].append(R_squared_models(models_round))

    simulation_elapsed = time.perf_counter() - simulation_started
    log_info(f"Decentralized worker processes completed in {simulation_elapsed:.2f}s")

    if sim_config.get("save_node_models", False):
        export_node_models(shared_models_local, ordered_node_keys, model_class, trainloaders, sim_config)
    
    return simulation_results


def centralized_simulation(
    sim_config: Dict[str, Any], 
    nodes_config: Dict[str, Any], 
    model_class,
    trainloaders, 
    valloaders,
    testloader,
    **kwargs
    ) -> Dict[str, Any]:
    """
    Simulates a centralized federated learning process across multiple nodes and a server.

    Args:
        sim_config: General simulation configuration (e.g., global hyperparameters).
        nodes_config: Specific configuration for each node.
        model_class: Python class of the training algorithm
        trainloaders: List of data loaders for training on each node.
        valloaders: List of data loaders for validation on each node.
        testloader: Data loader for validation on server.
    Returns:
        simulation_results: Results of the simulation, which may include performance metrics, statistics, etc.
    """
    simulation_started = time.perf_counter()

    nodes = {}
    server_conf = nodes_config[sim_config["server_id"]]
    nodes[sim_config["server_id"]] = ParameterServer(
        node_id=server_conf['id'], 
        ip=server_conf['ip'], 
        port=server_conf['port'], 
        neighbors= [nodes_config[str(i)] for i in server_conf['neighbors']], 
        dataset=sim_config["dataset"],
        model=model_class(sim_config["conf_nodes"]),
        testloader=testloader,
        rounds=sim_config["rounds"],
        aggregation_alg=sim_config["algorithm"],
        aggregation_config=sim_config.get("algorithm_config", None),
        conf_nodes=sim_config["conf_nodes"]
    )

    clients_config = nodes_config.copy()
    del clients_config[sim_config["server_id"]]
    barrier_sim = ProcessBarrier(len(clients_config))      # Synchronization barrier for nodes
    
    for index, (key, value) in enumerate(clients_config.items()):
        trainloader = resolve_node_loader(trainloaders, key, index)
        valloader = resolve_node_loader(valloaders, key, index)
        if value['id'] in sim_config["malicious_nodes"]:
            # Create instances of MaliciousCentralizedNode
            nodes[key] = MaliciousCentralizeClient(
                node_id=value['id'], 
                ip=value['ip'], 
                port=value['port'], 
                neighbors= [nodes_config[str(i)] for i in value['neighbors']], 
                server_id=sim_config["server_id"],
                dataset=sim_config["dataset"],
                model=model_class(sim_config["conf_nodes"]),
                trainloader=trainloader,
                testloader=valloader,
                rounds=sim_config["rounds"],
                conf_nodes=sim_config["conf_nodes"],
                barrier_sim=barrier_sim,
                byz_attack=sim_config["byz_attack"],
                attack_config=sim_config.get("attack_config", None)
            )
        else:
            # Create instances of CentralizedNode
            nodes[key] = CentralizeClient(
                node_id=value['id'], 
                ip=value['ip'], 
                port=value['port'], 
                neighbors= [nodes_config[str(i)] for i in value['neighbors']],
                server_id=sim_config["server_id"], 
                dataset=sim_config["dataset"],
                model=model_class(sim_config["conf_nodes"]),
                trainloader=trainloader,
                testloader=valloader,
                rounds=sim_config["rounds"],
                conf_nodes=sim_config["conf_nodes"],
                barrier_sim=barrier_sim
            )
    
    TaskExecutor = multiprocessing.Process 
    manager = multiprocessing.Manager()
    shared_results = manager.dict()
    shared_models = manager.dict()
    
    # Run the training process in separate threads/process for each node
    # tasks: List[Union[threading.Thread, multiprocessing.Process]] = []
    tasks = []
    for key, centralized_node in nodes.items():
        print("Node ID init:", centralized_node.node_id)
        task = TaskExecutor(target=run_node, args=(centralized_node, shared_results, shared_models))
        task.start()
        tasks.append(task)
    
    # Wait for all threads to finish
    for task in tasks:
        task.join()
        print("Task joined")

    shared_results_local = snapshot_shared_mapping(shared_results)
    shared_models_local = snapshot_shared_mapping(shared_models)
    ordered_node_keys = list(nodes.keys())

    if not shared_results_local:
        raise RuntimeError("Centralized simulation finished without collecting any node statistics.")

    evaluate_metrics = shared_results_local[next(iter(shared_results_local))].keys()
    simulation_results = {metric: {} for metric in evaluate_metrics}
    
    for key, node_statistics in shared_results_local.items():
        if str(key) == sim_config["server_id"]:
            for metric in evaluate_metrics:
                simulation_results[metric][key] = node_statistics[metric]

    simulation_elapsed = time.perf_counter() - simulation_started
    log_info(f"Centralized worker processes completed in {simulation_elapsed:.2f}s")

    if sim_config.get("save_node_models", False):
        export_node_models(shared_models_local, ordered_node_keys, model_class, trainloaders, sim_config)
    
    return simulation_results
    
def run_node(node, shared_results, shared_models):
    node.run()
    shared_results[node.node_id] = node.statistics
    shared_models[node.node_id] = node.local_model_history
    return

class ProcessBarrier:
    def __init__(self, n):
        self.n = n
        self.count = multiprocessing.Value('i', 0)
        self.condition = multiprocessing.Condition()

    def wait(self):
        with self.condition:
            self.count.value += 1
            if self.count.value == self.n:
                self.count.value = 0  # Reset para reusar la barrera
                self.condition.notify_all()
            else:
                self.condition.wait()
