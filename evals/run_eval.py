from pathlib import Path 
from datetime import datetime 
import pandas as pd 

from tests.test_ai import run_single 

BASE_PATH = Path.cwd() 
DF_PATH = BASE_PATH / "data" / "ground_truth_evals" / "product_info.csv"

def run_evaluations(): 
    df = pd.read_csv(DF_PATH)
    print(df.head())

    for _ in range(df["ID_producto"]): 
        continue

async def run_single_evaluation(): 
    ... 


if __name__ == "__main__": 
    run_evaluations() 