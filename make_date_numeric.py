import pandas as pd
import numpy as np

df = pd.read_csv("cleaned_stance_numeric.csv")

df["DOB"] = pd.to_datetime(df["DOB"])

from datetime import datetime 
today = datetime.today()


df["Age"] = df["DOB"].apply(lambda x: (today - x).days // 365 if pd.notnull(x) else None)

df = df.drop(columns = "DOB")

print(df)

df.to_csv("cleaned_numeric_ages.csv")