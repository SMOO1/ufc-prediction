import pandas as pd
import numpy as np

df = pd.read_csv("stats_processed.csv", sep=";")

women_fights = df[df["bout_type"].str.contains("Women", case = False, na=False)]
women = set() #set.update automatically excludes dupes
women.update(women_fights["winner_name"])
women.update(women_fights["loser_name"])


print(women_fights)

print(women)

women_fights.to_csv("women_fight_stats.csv")