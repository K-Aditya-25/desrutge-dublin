# DesRUTGe: Realistic Urban Traffic Generator using Decentralized Federated Learning for the SUMO simulator

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
  - scikit-learn==1.4.1
  - stable_baselines3==2.2.1
  - gym==0.26.2
  - numpy==1.24.1
  - pandas==1.5.3
  - urllib3==1.26.7
  - scipy==1.11.3
  - tqdm==4.65.0
  - seaborn==0.13.0
  - argparse==1.1
  - matplotlib==3.7.1
  - mpltex==0.7
  - colorama==0.4.6
  - lxml

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

python3 ./src/main_sim_centralized.py -r 1 -s 0 -t './config/centralized.json' -a "Mean" -db "Traffic_Generator" -o "./output/centralized_sim/centralized_mean.json"
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
- Traffic data path (`--trafficDataPath`): Directory containing `detector_data.csv` for the `Traffic_Generator` dataset.
- Output file (`-o`): name of the output file.
- Server (`-s`): ID of the server in the network topology (only in centralized simulations)

## Dublin SCATS preprocessing

The public repository does not include the original Barcelona traffic counts. To prepare Dublin SCATS data for the
`Traffic_Generator` pipeline, convert the hourly detector data into one 24-hour target profile per site:

```bash
python3 ./scripts/preprocess_dublin_scats.py \
  --hourly-data /path/to/dublin_hourly_counts.csv \
  --site-metadata /path/to/dublin_site_locations.csv \
  --dayfirst \
  --mode paper-faithful \
  --output-dir ./data/TrafficGeneration/dublin \
  --topology-output ./config/dublin_geographic_topology.json
```

This generates:

- `detector_data.csv`: repo-compatible site-level targets in the format `site_id,h00,...,h23`
- `site_metadata.csv`: merged metadata, coverage metrics, and quality flags for node selection
- `site_hourly_targets_long.csv` and `site_date_hour_totals.csv` in `paper-faithful` mode
- `preprocessing_summary.json`: a machine-readable summary of retained/rejected sites

You can then point the simulation at the generated Dublin dataset without overwriting the placeholder file:

```bash
python3 ./src/main_sim_decentralized.py \
  -r 1 \
  -t ./config/dublin_geographic_topology.json \
  -a Mean \
  -db Traffic_Generator \
  --trafficDataPath ./data/TrafficGeneration/dublin/ \
  -o ./output/decentralized_sim/dublin_mean.json
```

## Reference to the Paper

This code was originally presented in the following publication:
> **Alberto Bazán-Guillén, Carlos Beis-Penedo, Diego Cajaraville-Aboy, Pablo Barbecho-Bautista, Rebeca P. Díaz-Redondo, Luis J. de la Cruz Llopis, Ana Fernández-Vilas, Mónica Aguilar Igartua, Manuel Fernández-Veiga**, *"Realistic Urban Traffic Generator using Decentralized Federated Learning for the SUMO simulator"*, IEEE Open Journal of the Communications Society, ISSN: 2644-125X, 8th August 2025, **DOI:** [10.1109/OJCOMS.2025.3597019](https://ieeexplore.ieee.org/document/11121363).

If you use or modify this code in your research, please cite the paper to acknowledge the original work.

## ACKNOWLEDGMENT

This work was supported by the Spanish Government under research project ``Enhancing Communication Protocols with Machine Learning while Protecting Sensitive Data ([COMPROMISE](http://www.compromise.upc.edu/))" PID2020-113795RB-C32/C33, funded by MICIU/AEI/10.13039/501100011033.
![alt text](http://www.compromise.upc.edu/images/MICIU+AEI-COMPROMISE.jpg)

## License

This project is licensed under the GNU GPLv3 License. See the LICENSE file for more details.

## Contact

For questions or suggestions, contact the author at alberto.bazan@upc.edu.
