import pandas as pd
from pathlib import Path
from utils.utils_logs import *

class Traffic_Generator:
    def __init__(self, csv_path: str, transform=None):
        """
        PyTorch approach for modelling CSV datasets.

        Args:
            csv_path (str): Ruta al archivo CSV con los datos.
            transform (callable, optional): Transformaciones a aplicar a las entradas.
        """
        # PREPARE GLOBAL DATASET
        dataset_path = Path(csv_path) / "detector_data.csv"
        df = pd.read_csv(dataset_path)
        df.dropna(inplace=True)
        self._validate_traffic_profile(df)

        # ATTRIBUTES OF DATASET (DEFINITION)
        log_info("Example of the dataset:")
        print(df.head(2))
        self.data = df.values
        self.columns = df.columns

    def _validate_traffic_profile(self, df: pd.DataFrame) -> None:
        expected_columns = 25
        if df.shape[1] != expected_columns:
            raise ValueError(
                "Traffic_Generator expects one site_id column plus 24 hourly targets. "
                f"Found {df.shape[1]} columns instead of {expected_columns}."
            )

        expected_hour_columns = [f"h{hour:02d}" for hour in range(24)]
        if list(df.columns[1:]) != expected_hour_columns:
            raise ValueError(
                "Traffic_Generator expects hourly columns named h00..h23 in order. "
                f"Found {list(df.columns[1:])}."
            )

        numeric_targets = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
        if numeric_targets.isna().any().any():
            raise ValueError("Traffic_Generator found non-numeric hourly traffic targets in detector_data.csv.")

        if (numeric_targets < 0).any().any():
            raise ValueError("Traffic_Generator found negative hourly traffic targets in detector_data.csv.")
        
    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx].tolist()
        
    
    def __repr__(self) -> str:
        head = "Dataset " + self.__class__.__name__
        body = [f"Number of datapoints: {self.__len__()}"]
        if hasattr(self, "transforms") and self.transforms is not None:
            body += [repr(self.transforms)]
        lines = [head] + [" " + line for line in body]
        return "\n".join(lines)


def load_Traffic_Generator(file_path: str = "./data/TrafficGeneration/"):
    """
    Loads data of the detectors
    """
    dataset = Traffic_Generator( file_path, transform=None )
    return dataset


def prepare_dataset_Traffic(dataset):
    """
    """
    testset = dataset[-1][1:]
    trainset = dataset[:-1]
    print(f"Trainset: {len(trainset)} samples, Testset: {len([testset])} samples.")
    
    subsets = {}
    for set in trainset:
        id = set[0]
        data = set[1:]
        subsets[id] = data
    
    ordered_subsets = {k: subsets[k] for k in sorted(subsets.keys())}
    print()
    trainloaders = []
    valloaders = []
    for key in ordered_subsets.keys():
        trainloaders.append(subsets[key])
        valloaders.append(subsets[key])
    
    return trainloaders, valloaders, testset
