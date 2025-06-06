import pandas as pd
import torch
import numpy as np
import random
from torch.utils.data import DataLoader, Dataset, Subset, random_split
from utils.utils_logs import *
from collections import Counter

class Traffic_Generator(Dataset):
    def __init__(self, csv_path: str, transform=None):
        """
        PyTorch approach for modelling CSV datasets.

        Args:
            csv_path (str): Ruta al archivo CSV con los datos.
            transform (callable, optional): Transformaciones a aplicar a las entradas.
        """
        # PREPARE GLOBAL DATASET
        df = pd.read_csv(csv_path + "detector_data.csv")
        df.dropna(inplace=True)

        # ATTRIBUTES OF DATASET (DEFINITION)
        log_info("Example of the dataset:")
        print(df.head(2))
        self.data = df.values
        self.columns = df.columns
        
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