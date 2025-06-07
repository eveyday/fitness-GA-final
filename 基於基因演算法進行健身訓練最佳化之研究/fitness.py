import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

#評分函數
def evaluate_fitness(chromosome_df, user, verbose=True):
    weights = {
        "coverage": 0.3,
        "target": 0.15,
        "safety": 0.25,
        "rest": 0.15,
        "cardio": 0.15,
        "volume": 0.1,
        "overuse":0.1
    }

    scores = {
        "coverage": evaluate_coverage(chromosome_df),
        "volume": evaluate_volume(chromosome_df, user),
        "safety": evaluate_safety(chromosome_df, user),
        "target": evaluate_target(chromosome_df, user),
        "rest": evaluate_muscle_rest(chromosome_df, user),
        "cardio": evaluate_cardio(chromosome_df),
        "overuse": evaluate_overuse(chromosome_df,user)
    }

    total_score = sum(scores[k] * weights[k] for k in weights)

    if verbose:
        print("\n=== Fitness 各項目得分 ===")
        for k in scores:
            print(f"{k.capitalize()}: {scores[k]}")

    return round(total_score, 2), scores

# 所有主要肌群（排除有氧）
ALL_MAJOR_MUSCLES = ["胸", "背", "腿", "手臂", "肩", "臀","核心"]

#是否所有肌群都有練到
def evaluate_coverage(chromosome_df):
    trained = set(chromosome_df["大肌群"].unique()) 
    covered = sum(1 for m in ALL_MAJOR_MUSCLES if m in trained)
    return covered / len(ALL_MAJOR_MUSCLES)

#評估是否有加強使用者想加強的部位(每周多練一次)
def evaluate_target(chromosome_df, user):
    if not user.target_muscles:
        return 1.0

    target = user.target_muscles[0]

    # 找出每一天是否有訓練到目標肌群
    days_with_target = set()
    for _, row in chromosome_df.iterrows():
        if row["大肌群"] == target:
            days_with_target.add(row["訓練日"])

    # 至少兩天有訓練目標肌群就給滿分
    return min(len(days_with_target) / 2, 1.0)

# 評估整體的安全性
# 安全分數公式（針對一般成人）
#score = 1.0 - min(max((avg_risk - 13.8) / (18 - 13.8), 0), 1)
def evaluate_safety(df, user):
    avg_risk = df["危險度"].mean()

    # 老人條件：高於 60 歲
    if user.age >= 60:
        threshold = 16
        if avg_risk <= threshold:
            return 1.0
        else:
            score = 1.0 - (avg_risk - threshold) * 0.1
            return round(max(score, 0), 2)

    # 新手條件：初級訓練者
    elif user.level == "beginner":
        threshold = 13.8
        if avg_risk <= threshold:
            return 1.0
        else:
            score = 1.0 - (avg_risk - threshold) * 0.1
            return round(max(score, 0), 2)

    # 一般成人使用線性轉換：13.8~18 映射為 1.0~0.0
    else:
        score = 1.0 - min(max((avg_risk - 13.8) / (18 - 13.8), 0), 1)
        return round(score, 2)

#根據實際訓練的星期去判斷是否連續訓練
def evaluate_muscle_rest(df, user):
    from collections import defaultdict

    # 建立 day → 肌群 對應表（轉成 int）
    day_muscles = defaultdict(set)
    for _, row in df.iterrows():
        day = int(str(row["訓練日"]).replace("Day", ""))  # 保險起見轉字串後去 Day
        day_muscles[day].add(row["大肌群"])

    training_days = sorted(user.training_days_list)  # 預期為 int list，如 [1, 3, 5]
    penalty = 0

    for i in range(len(training_days) - 1):
        day1 = training_days[i]
        day2 = training_days[i + 1]

        if abs(day2 - day1) == 1:  # 相鄰才檢查
            repeated = day_muscles[day1] & day_muscles[day2]
            filtered = {m for m in repeated if m not in user.target_muscles and m != "有氧"}
            penalty += len(filtered)

    max_penalty = len(training_days) - 1
    score = 1 - (penalty / max_penalty if max_penalty else 0)
    return max(0, round(score, 2))

# 評估是否安排了有氧（有給分）
def evaluate_cardio(chromosome_df):
    has_cardio = "有氧" in chromosome_df["大肌群"].values
    return 1.0 if has_cardio else 0.0

# 控制同部位出現太多次
def evaluate_overuse(df, user):
    # 記錄每一天訓練到哪些大肌群
    day_muscles = defaultdict(set)
    for _, row in df.iterrows():
        day = row["訓練日"]
        day_muscles[day].add(row["大肌群"])

    # 統計整週每個大肌群出現了幾天
    muscle_day_count = Counter()
    for muscles in day_muscles.values():
        for m in muscles:
            muscle_day_count[m] += 1

    penalty = 0
    base_limit = 1

    for muscle, count in muscle_day_count.items():
        if muscle == "有氧":
            continue  # 不對有氧扣分

        # 針對核心和欲加強訓練部位給出彈性限制
        if muscle == "核心":
            expected_core_times = max(1, len(user.training_days_list) // 2) if len(user.training_days_list) > 3 else 1
            limit = expected_core_times
        elif muscle in user.target_muscles:
            limit = base_limit + 1
        else:
            limit = base_limit

        if count > limit:
            penalty += (count - limit) * 0.1

    score = max(0, 1 - penalty)
    return round(score, 2)


# 評估整體訓練量是否合適
def evaluate_volume(df, user):
    total_volume = df["訓練量"].fillna(0).sum()
    if user.level == "beginner":
        ideal_range = (8000, 12000)
    elif user.level == "intermediate":
        ideal_range = (12000, 18000)
    else:
        ideal_range = (15000, 22000)

    min_v, max_v = ideal_range
    if min_v <= total_volume <= max_v:
        return 1.0
    elif total_volume < min_v:
        return round(max(0, 1 - (min_v - total_volume) * 0.01 / 100), 2)
    else:
        return round(max(0, 1 - (total_volume - max_v) * 0.01 / 100), 2)

# 圖表化呈現各項得分
def evaluate_and_plot(df, user):
    scores = {
        "Coverage": evaluate_coverage(df),
        "Volume": evaluate_volume(df, user),
        "Safety": evaluate_safety(df, user),
        "Target": evaluate_target(df, user),
        "Rest": evaluate_muscle_rest(df, user),
        "Cardio": evaluate_cardio(df),
        "Overuse": evaluate_overuse(df, user)
    }

    print("\n=== Fitness 各項目得分 ===")
    for k, v in scores.items():
        print(f"{k}: {v}")

    plt.figure(figsize=(10, 5))
    plt.bar(scores.keys(), scores.values())
    plt.ylim(0, 1)
    plt.title("Fitness Evaluation")
    plt.ylabel("Score")
    plt.xticks(rotation=45)
    
    # 儲存成圖片而不是顯示 GUI
    plt.tight_layout()
    plt.savefig("static/fitness_result.png")
    plt.close()