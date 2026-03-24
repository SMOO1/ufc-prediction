import pandas as pd
import numpy as np

df = pd.read_csv("cleaned_stance_numeric.csv")

#df = pd.get_dummies(df, columns=["Stance"], dtype=int)
#df["Weight"] = df["Weight"].str.replace(' lbs', '')



#drop_cols = ["Unnamed: 0.2", "Unnamed: 0.1", "Unnamed: 0"]
#df = df.drop(drop_cols, axis = 1)

df = df.drop("NaN", index = 1)

print(df)
df.to_csv("cleaned_stance_numeric.csv")