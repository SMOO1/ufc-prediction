import pandas as pd
import numpy as np

df = pd.read_csv("cleaned_numeric_ages.csv")




df.drop(columns=["Unnamed: 0"])
print(df)

df.to_csv("cleaned_numeric_age.csv", index = False)