import threading
import multiprocessing

from entities.centralized_client import CentralizeClient
from entities.decentralized_client import DecentralizeClient
from entities.malicious_centralized_client import MaliciousCentralizeClient
from entities.malicious_decentralized_client import MaliciousDecentralizeClient
from entities.parameter_server import ParameterServer
from utils.utils_logs import *
from machine_learning.metrics.utils import R_squared_models

from typing import Dict, Any, List, Union

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
    nodes = {}
    
    barrier_sim = ProcessBarrier(len(nodes_config))             # Synchronization barrier for nodes
    # barrier_sim = threading.Barrier(len(nodes_config))      

    for index, (key, value) in enumerate(nodes_config.items()):

        if value['id'] in sim_config["malicious_nodes"]:
            # Create instances of MaliciousDecentralizeNode
            nodes[key] = MaliciousDecentralizeClient(
                node_id=value['id'], 
                ip=value['ip'], 
                port=value['port'], 
                neighbors= [nodes_config[str(i)] for i in value['neighbors']], 
                dataset=sim_config["dataset"],
                model=model_class(sim_config["conf_nodes"]),
                trainloader=trainloaders[index],
                testloader=valloaders[index],
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
                trainloader=trainloaders[index],
                testloader=valloaders[index],
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

    evaluate_metrics = shared_results[next(iter(shared_results))].keys()
    simulation_results = {metric: {} for metric in evaluate_metrics}
    simulation_results["R-Squared"] = []
    
    for key, node_statistics in shared_results.items():
        for metric in evaluate_metrics:
            simulation_results[metric][key] = node_statistics[metric] 
    
    for round in range(int(sim_config["rounds"])):
        models_round = []
        for key, node_statistics in shared_models.items():
            models_round.append(node_statistics[round])
        simulation_results["R-Squared"].append(R_squared_models(models_round))
    
    # Save models - not very efficient, but non shared memory of multiprocessing is not easy to handle
    for key, node_statistics in shared_models.items():
        last_model = node_statistics[-1]
        config_aux = sim_config["conf_nodes"].copy()
        config_aux["node_id"] = key
        model_aux = model_class(config_aux)
        model_aux.train_model(trainloaders[0], config_aux)
        model_aux.set_params(last_model)
        model_aux.model.save("./ppo_simulador_prueba_" + str(key) + ".zip")
    
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
                trainloader=trainloaders[index],
                testloader=valloaders[index],
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
                trainloader=trainloaders[index],
                testloader=valloaders[index],
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
    
    evaluate_metrics = shared_results[next(iter(shared_results))].keys()
    simulation_results = {metric: {} for metric in evaluate_metrics}
    
    for key, node_statistics in shared_results.items():
        if key == sim_config["server_id"]:
            for metric in evaluate_metrics:
                simulation_results[metric][key] = node_statistics[metric]
    
    # Save models - not very efficient, but non shared memory of multiprocessing is not easy to handle
    # for key, node_statistics in shared_models.items():
    #     last_model = node_statistics[-1]
    #     config_aux = sim_config["conf_nodes"].copy()
    #     config_aux["node_id"] = key
    #     model_aux = model_class(config_aux)
    #     model_aux.train_model(trainloaders[0], config_aux)
    #     model_aux.set_params(last_model)
    #     model_aux.model.save("./ppo_simulador_prueba_" + str(key) + ".zip")
    
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