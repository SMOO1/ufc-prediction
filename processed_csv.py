import pandas as pd
import numpy as np

df = pd.read_csv("stats_processed.csv", sep=";")

women_fights = df[df["bout_type"].str.contains("Women", case = False, na=False)]
women = set() #set.update automatically excludes dupes
women.update(women_fights["winner_name"])
women.update(women_fights["loser_name"])

women_list = list(women)
print(women)


#print(women_fights)

#print(women)

#women_fights.to_csv("women_fight_stats.csv")


final_df = pd.read_csv("cleaned_numeric_ages.csv")

final_df["Female"] = final_df["fighter_name"].apply(lambda x: 1 if x.upper() in women else 0)

print(final_df)
final_df.to_csv("gendered_stats.csv", index=False)