import pandas as pd
import numpy as np

df = pd.read_csv("no_quotes_and_percent.csv")

df = pd.get_dummies(df, columns=["Stance"], dtype=int)
df["Weight"] = df["Weight"].str.replace(' lbs', '')

print(df)
df.to_csv("cleaned_stance_numeric.csv")