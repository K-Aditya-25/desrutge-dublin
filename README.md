# DesRUTGe: a DFL Simulation Project for traffic generation

The project **DesRUTGe** has been adapted to simulate environments for Decentralized Federated Learning (DFL), specifically focused on federating a traffic generator called DesRUTGe. This adaptation enables multiple nodes to collaboratively train and optimize traffic generation models without sharing their local data, allowing exploration of network topologies and model aggregation strategies in a decentralized context.

## Project Structure

- **/config**: Configuration files for the simulation (communication network).
- **/src**: Contains the simulation source code.
    -  **../entities**: Provides the main classes that define the role of the device in the learning network (server, client...)
    -  **../machine_learning**: Various tools for handling ML models, Byzantine attacks, aggregation algorithms...
    -  **../utils**: Multipurpose tools: logger...
    -  **../main_sim_(de)centralized.py**: Provides a specific example of how to launch a (D)FL simulation.

## Requirements

- **Python 3.10.12**
- Libraries:
  - torch==2.0.1
  - torchvision==0.15.2
  - numpy==1.24.1
  - pandas==1.5.3
  - urllib3==1.26.7
  - scipy==1.11.3
  - tqdm==4.65.0
  - seaborn==0.13.0
  - argparse==1.1
  - matplotlib==3.7.1
  - mpltex==0.7
  - colorama

## Installation

Clone the repository:

```bash
git clone https://gitlab.com/compromise3/desrutge.git
```

Navigate to the project directory:

```bash
cd desrutge
```

Install the necessary packages:

```bash
pip3 install -r requirements.txt
```

## Usage
To run the simulation, use the following command (it is one example):

```bash
python3 ./src/main_sim_decentralized.py -r 1 -t './config/voronoi_traffic_detectors.json' -a "Mean" -db "Traffic_Generator" -o "./output/decentralized_sim/decentralized_mean.json"

python3 ./src/main_sim_centralized.py -r 1 -s 0 -t './config/centralized_traffic_detectors.json' -a "Mean" -db "Traffic_Generator" -o "./output/centralized_sim/centralized_mean.json"
```

Configuration parameters (more details in the source code):

- Communication rounds (`-r`): Number of rounds to train and share the ML model.
- Network topology (`-t`): Path to the file containing the network topology.
- Malicious nodes (`-m`): Byzantine Nodes Array.
- Byzantine attack (`-at`): Type of Byzantine attack
- Attack parameters (`-p1`): Parameters for attack config
- Aggregation algorithm (`-a`): Selected Byzantine-robust algorithm
- Algorithm parameters (`-p2`): Parameters for aggregation scheme config.
- Database (`-db`): Selected dataset for this simulation.
- Output file (`-o`): name of the output file.
- Server (`-s`): ID of the server in the network topology (only in centralized simulations)

## License

This project is licensed under the GNU GPLv3 License. See the LICENSE file for more details.

## Contact

For questions or suggestions, contact the author at dcajaraville@det.uvigo.es.