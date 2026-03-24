import pandas as pd
import numpy as np

cols = ["Height", "Weight", "Reach", "SLpM", "Str_Acc", "SApM", "Str_Def",
    "TD_Avg", "TD_Acc", "TD_Def", "Sub_Avg"]

df = pd.read_csv("raw_fighter_details.csv")

df[cols] = df[cols].replace(0, np.nan)
df.to_csv("zero_to_nan.csv")
print(df)

