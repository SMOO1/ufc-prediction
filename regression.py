import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

fights = pd.read_csv("stats_processed.csv", sep=";")

features = [
    "delta_height",
    "delta_reach",
    "delta_slpm_cs",
    "delta_str_acc_cs",
    "delta_sapm_cs",
    "delta_str_def_cs",
    "delta_td_avg_cs",
    "delta_td_acc_cs",
    "delta_td_def_cs",
    "delta_sub_avg_cs"
]
x = fights[features].fillna(0)
y = (fights["winner"] == "red").astype(int)

X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

model = LogisticRegression(max_iter=10000, fit_intercept=False)
model.fit(X_train, y_train)

def get_fighter_stats(name):
    fighter = fighters[fighters["fighter_name"] == name]
    if fighter.empty:
        raise ValueError("fighter not found in the dataset")
    return fighter.iloc[0].to_dict()

def predict_fight(fighter1, fighter2):
    
   # fighter1 = get_fighter_stats(fighter1)
   # fighter2 = get_fighter_stats(fighter2)
    diff = {
        "delta_height": fighter1["Height"] - fighter2["Height"],
        "delta_reach": fighter1["Reach"] - fighter2["Reach"],
        "delta_slpm_cs": fighter1["SLpM"] - fighter2["SLpM"],
        "delta_str_acc_cs": fighter1["Str_Acc"] - fighter2["Str_Acc"],
        "delta_sapm_cs": fighter1["SApM"] - fighter2["SApM"],
        "delta_str_def_cs": fighter1["Str_Def"] - fighter2["Str_Def"],
        "delta_td_avg_cs": fighter1["TD_Avg"] - fighter2["TD_Avg"],
        "delta_td_acc_cs": fighter1["TD_Acc"] - fighter2["TD_Acc"],
        "delta_td_def_cs": fighter1["TD_Def"] - fighter2["TD_Def"],
        "delta_sub_avg_cs": fighter1["Sub_Avg"] - fighter2["Sub_Avg"],
    }

    df = pd.DataFrame([diff])
    df_scaled = scaler.transform(df)

    prob = model.predict_proba(df_scaled)[0][1]
    return prob

fighters = pd.read_csv("converted_height.csv")

fighter1 = { 
    "Height": 75,
    "Reach": 78,
    "SLpM": 2.62,
    "Str_Acc": 37,
    "SApM": 3.06,
    "Str_Def": 50,
    "TD_Avg": 0.82,
    "TD_Acc": 50,
    "TD_Def": 33,
    "Sub_Avg": 1.6,
}

fighter2 = {  # 6'3", 170, 79"
    "Height": 75,
    "Reach": 79,
    "SLpM": 2.28,
    "Str_Acc": 58,
    "SApM": 1.51,
    "Str_Def": 62,
    "TD_Avg": 0.19,
    "TD_Acc": 16,
    "TD_Def": 70,
    "Sub_Avg": 0.0,
}

axel = {
    "Height": 72,
    "Reach": 74,
    "SLpM": 4.07,
    "Str_Acc": 45,
    "SApM": 5.29,
    "Str_Def": 61,
    "TD_Avg": 2.22,
    "TD_Acc": 36,
    "TD_Def": 0,
    "Sub_Avg": 0.0,
}

mason = {
    "Height": 70,
    "Reach": 74,
    "SLpM": 5.98,
    "Str_Acc": 42,
    "SApM": 4.45,
    "Str_Def": 50,
    "TD_Avg": 3.48,
    "TD_Acc": 55,
    "TD_Def": 73,
    "Sub_Avg": 0.2,
}

movsar = {
    "Height": 67,
    "Reach": 72,
    "SLpM": 3.91,
    "Str_Acc": 47,
    "SApM": 2.80,
    "Str_Def": 61,
    "TD_Avg": 4.78,
    "TD_Acc": 52,
    "TD_Def": 61,
    "Sub_Avg": 0.2,
}

lerone = {
    "Height": 69,
    "Reach": 73,
    "SLpM": 4.34,
    "Str_Acc": 51,
    "SApM": 2.65,
    "Str_Def": 60,
    "TD_Avg": 1.20,
    "TD_Acc": 54,
    "TD_Def": 44,
    "Sub_Avg": 0.5,
}

michael = {
    "Height": 68,
    "Reach": 69,
    "SLpM": 7.79,
    "Str_Acc": 42,
    "SApM": 7.43,
    "Str_Def": 51,
    "TD_Avg": 0.32,
    "TD_Acc": 100,
    "TD_Def": 57,
    "Sub_Avg": 0.0,
}

luke = {
    "Height": 69,
    "Reach": 69,
    "SLpM": 5.56,
    "Str_Acc": 57,
    "SApM": 3.32,
    "Str_Def": 64,
    "TD_Avg": 0.00,
    "TD_Acc": 0,
    "TD_Def": 37,
    "Sub_Avg": 0.0,
}

def print_win_probability(fighter1, fighter2, name1="Fighter 1", name2="Fighter 2"):
    prob_fighter1_wins = predict_fight(fighter1, fighter2)
    prob_fighter2_wins = 1.0 - prob_fighter1_wins
    
    pct_1 = prob_fighter1_wins * 100
    pct_2 = prob_fighter2_wins * 100
    
    print("-" * 30)
    print(f"Win Probability Matchup:")
    print(f"{name1}: {pct_1:.2f}%")
    print(f"{name2}: {pct_2:.2f}%")
    print("-" * 30)
    
    if prob_fighter1_wins > 0.5:
        print(f"Prediction: {name1} win")
    else:
        print(f"Prediction: {name2} win")


#print_win_probability(michael, luke, name1="mich", name2="Blue Fighter")


israel_adesanya = { 
    "Height": 76,
    "Reach": 80,
    "SLpM": 4.02,
    "Str_Acc": 48,
    "SApM": 3.20,
    "Str_Def": 55,
    "TD_Avg": 0.05,
    "TD_Acc": 11,
    "TD_Def": 76,
    "Sub_Avg": 0.1,
}

joe_pyfer = {  
    "Height": 74,
    "Reach": 75,
    "SLpM": 3.47,
    "Str_Acc": 43,
    "SApM": 3.05,
    "Str_Def": 53,
    "TD_Avg": 1.23,
    "TD_Acc": 33,
    "TD_Def": 50,
    "Sub_Avg": 1.0,
}
alexa_grasso = {
    "Height": 65,
    "Reach": 66,
    "SLpM": 4.11,
    "Str_Acc": 41,
    "SApM": 3.73,
    "Str_Def": 58,
    "TD_Avg": 0.41,
    "TD_Acc": 35,
    "TD_Def": 54,
    "Sub_Avg": 0.6,
}

maycee_barber = {
    "Height": 65,
    "Reach": 65,
    "SLpM": 4.61,
    "Str_Acc": 53,
    "SApM": 2.76,
    "Str_Def": 54,
    "TD_Avg": 1.58,
    "TD_Acc": 45,
    "TD_Def": 51,
    "Sub_Avg": 0.1,
}
niko_price = {
    "Height": 72,
    "Reach": 76,
    "SLpM": 5.13,
    "Str_Acc": 43,
    "SApM": 5.61,
    "Str_Def": 48,
    "TD_Avg": 0.98,
    "TD_Acc": 28,
    "TD_Def": 50,
    "Sub_Avg": 0.6,
}

michael_chiesa = {
    "Height": 73,
    "Reach": 75,
    "SLpM": 2.03,
    "Str_Acc": 40,
    "SApM": 1.73,
    "Str_Def": 57,
    "TD_Avg": 3.05,
    "TD_Acc": 47,
    "TD_Def": 67,
    "Sub_Avg": 1.0,
}

julian_erosa = {
    "Height": 73,
    "Reach": 74,
    "SLpM": 6.21,
    "Str_Acc": 48,
    "SApM": 6.27,
    "Str_Def": 48,
    "TD_Avg": 1.78,
    "TD_Acc": 43,
    "TD_Def": 61,
    "Sub_Avg": 0.7,
}

lerryan_douglas = {
    "Height": 69,
    "Reach": 72,
    "SLpM": 11.67,
    "Str_Acc": 87,
    "SApM": 5.00,
    "Str_Def": 66,
    "TD_Avg": 0.00,
    "TD_Acc": 0,
    "TD_Def": 0,
    "Sub_Avg": 0.0,
}

mansur_abdul_malik = {
    "Height": 74,
    "Reach": 80,
    "SLpM": 4.18,
    "Str_Acc": 48,
    "SApM": 3.46,
    "Str_Def": 51,
    "TD_Avg": 0.94,
    "TD_Acc": 50,
    "TD_Def": 83,
    "Sub_Avg": 0.5,
}

yousri_belgaroui = {
    "Height": 78,
    "Reach": 79,
    "SLpM": 5.82,
    "Str_Acc": 66,
    "SApM": 2.52,
    "Str_Def": 61,
    "TD_Avg": 0.39,
    "TD_Acc": 100,
    "TD_Def": 68,
    "Sub_Avg": 0.0,
}

kyle_nelson = {
    "Height": 71,
    "Reach": 71,
    "SLpM": 3.60,
    "Str_Acc": 45,
    "SApM": 4.48,
    "Str_Def": 53,
    "TD_Avg": 1.18,
    "TD_Acc": 23,
    "TD_Def": 66,
    "Sub_Avg": 0.5,
}

terrance_mckinney = {
    "Height": 70,
    "Reach": 73,
    "SLpM": 6.24,
    "Str_Acc": 56,
    "SApM": 3.46,
    "Str_Def": 43,
    "TD_Avg": 3.34,
    "TD_Acc": 40,
    "TD_Def": 72,
    "Sub_Avg": 2.1,
}

print_win_probability(kyle_nelson, terrance_mckinney, name1="Kyle Nelson", name2="Terrance McKinney")
print_win_probability(mansur_abdul_malik, yousri_belgaroui, name1="Mansur Abdul-Malik", name2="Yousri Belgaroui")
print_win_probability(julian_erosa, lerryan_douglas, name1="Julian Erosa", name2="Lerryan Douglas")
print_win_probability(niko_price, michael_chiesa, name1="Niko Price", name2="Michael Chiesa")
print_win_probability(alexa_grasso, maycee_barber, name1="Alexa Grasso", name2="Maycee Barber")
print_win_probability(israel_adesanya, joe_pyfer, name1="Israel Adesanya", name2="Joe Pyfer")

