import pandas as pd
import numpy as np

from datetime import datetime

today = datetime.today

def convert_date_to_age(date):
    

df = pd.read_csv("cleaned_stance_numeric.csv")