import pandas as pd
import numpy as np

cols = ["Height", "Weight", "Reach", "SLpM", "Str_Acc", "SApM", "Str_Def",
    "TD_Avg", "TD_Acc", "TD_Def", "Sub_Avg"]

df = pd.read_csv("zero_removed.csv")

df["Height"] = df["Height"].str.replace('"', '')
df["Reach"] = df["Height"].str.replace('"', '')

percent_cols = ["Str_Acc", "Str_Def", "TD_Acc", "TD_Def"]

for col in percent_cols:
    df[col] = df[col].str.replace('%', '').astype(float) / 100 #convert percentages to decimal

df.to_csv("no_quotes_and_percent.csv")
print(df)

