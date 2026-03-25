import pandas as pd
import numpy as np


def height_to_inches(height):
    feet, inches = height.split("'")
    
    return 12 * int(feet) + int(inches)

df = pd.read_csv("gendered_stats.csv")
df["Height"] =  df["Height"].apply(lambda x: height_to_inches(x))
df["Reach"] = df["Reach"].apply(lambda x: height_to_inches(x))

df.to_csv("converted_height.csv", index = False)

