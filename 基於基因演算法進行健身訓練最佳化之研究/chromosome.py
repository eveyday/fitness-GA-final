import random
import pandas as pd
import numpy as np
from exercise_db import exercise_dict
from user_input import User,create_user_from_dict

# 等級對應的訓練上限係數
level_factors = {
    "beginner": 1.0,
    "intermediate": 1.5,
    "advanced": 2.0
}
# 等級對應的訓練次數和組數
level_ranges = {
        "beginner": {"reps": (10, 15), "sets": (2, 3)},
        "intermediate": {"reps": (8, 12), "sets": (3, 4)},
        "advanced": {"reps": (6, 10), "sets": (4, 5)}
}
# 定義大肌群分類（用於休息時間設定）
big_muscles = ["胸", "背", "腿"]


#每日大肌群分配函數
def generate_weekly_muscle_schedule(user):
    base_muscles = ["胸", "背", "腿", "手臂", "肩", "臀"]
    training_days = user.training_days_list
    num_days = len(training_days)

    # Step 1: 準備肌群清單
    muscle_list = base_muscles.copy()
    # 核心訓練次數
    core_times = max(1, num_days // 2) if num_days > 3 else 1
    base_muscles.append("核心")
    muscle_list +=["核心"]*core_times

    #使用者是否有想加強訓練部位
    if user.target_muscles:
        muscle_list += user.target_muscles
    total_muscles = len(muscle_list)
    #平均分配到每一天
    base_per_day = total_muscles // num_days  # 每天至少要分配的肌群數
    remainder = total_muscles % num_days         # 有幾天要多一個肌群
    per_day_counts = [base_per_day + 1 if i < remainder else base_per_day for i in range(num_days)]

    #菜單
    schedule={}
    for i,day in enumerate(training_days):
        day_key = f"Day{day}"
        #每天從base_muscle隨機選取肌群
        today_muscles = [random.choice(base_muscles)for _ in range(per_day_counts[i])]
        if random.random()<0.5:
            today_muscles.append("有氧")
        schedule[day_key] = today_muscles
    return schedule

#產生動作
def generate_random_gene(muscle_group: str, sub_group: str, user: User):
    exercise = random.choice(exercise_dict[muscle_group][sub_group])
    #設定次數和組數
    if user.level not in level_ranges:
        raise ValueError(f"未知的等級：{user.level}")
    reps_range = level_ranges[user.level]["reps"]
    sets_range = level_ranges[user.level]["sets"]
    reps = random.randint(*reps_range)
    sets = random.randint(*sets_range)
    #設定休息時間
    if muscle_group in big_muscles:
        rest = random.choice([90,120])
    else:
        rest = random.choice([60,90])
    # 使用封裝好的重量估算函式
    training_weight = estimate_training_weight(user,sub_group,reps)

    if user.age >= 60:
        risk = exercise['老人危險度']
    else:
        risk = exercise['一般人危險度']

    return {
        "動作": exercise["動作"],
        "大肌群": muscle_group,
        "細項肌群": sub_group,
        "次數": reps,
        "組數": sets,
        "休息": rest,
        "重量": training_weight,
        "危險度": risk
    }

#產生重量函式
def estimate_training_weight(user:User,sub_group:str,reps:int) -> float:
    #預估使用者的重量應該介於多少適合增基
    level_intensity_range = {
    "beginner": (0.60, 0.65),
    "intermediate": (0.65, 0.75),
    "advanced": (0.75, 0.80)
    }
    #抓這個肌群的1RM
    muscle_1rm_dict = user.estimate_muscle_group_1RM()
    #拿出要計算的那個肌群的1RM
    if sub_group not in muscle_1rm_dict:
        raise ValueError(f"未知的肌群名稱：{sub_group}")
    muscle_1rm = muscle_1rm_dict[sub_group]
    #抓這個等級的強度範圍
    intensity_min, intensity_max = level_intensity_range.get(user.level, (0.6, 0.65))

    #根據次數微調(當次數越多重量要減輕)
    if reps >= 12:
        intensity = random.uniform(intensity_min, (intensity_min + intensity_max) / 2)
    elif reps <= 8:
        intensity = random.uniform((intensity_min + intensity_max) / 2, intensity_max)
    else:
        intensity = random.uniform(intensity_min, intensity_max)

    # 計算訓練重量
    training_weight = round(muscle_1rm * intensity, 1)

    return training_weight

#新手細部肌群選擇設計
def get_beginner_subgroups(muscle_group):
    mapping = {
        "胸": ["胸大肌", "中下胸", "上胸肌"],
        "手臂": ["二頭(短頭)", "二頭(長頭)", "三頭"],
        "腿": ["股四頭", "股二頭"],
        "臀": ["臀肌"],
        "背": ["背擴肌", "中下背"],
        "肩": ["前束", "後束"],
    }
    if muscle_group not in mapping:
        return []
    candidates = mapping[muscle_group]
    if muscle_group == "手臂":
        return [random.choice(["二頭(短頭)", "二頭(長頭)"]), "三頭"]
    elif muscle_group == "背":
        return ["背擴肌", "中下背"]
    elif muscle_group == "腿":
        return candidates
    elif muscle_group == "臀":
        return ["臀肌"]
    elif muscle_group == "肩":
        return ["前束", "後束"]
    elif muscle_group == "胸":
        return random.sample(candidates, 2)
    return []

# 產生染色體主函式 
def generate_chromosome(user: User, schedule: dict):
    chromosome = []
    total_volume = 0 #計算菜單訓練量
    for day, muscle_groups in schedule.items():
        for muscle in muscle_groups:

            #核心
            if muscle == "核心":
                sub_group = "腹"
                exercise = random.choice(exercise_dict[muscle][sub_group])
                reps = random.randint(12, 20)
                sets = random.randint(2, 4)
                rest = 60

                if exercise["動作"] == "機械式捲腹":
                    weight = estimate_training_weight(user, sub_group, reps)
                else:
                    weight = 0
                #計算此動作重量
                volume = reps * sets * weight
                total_volume += volume

                risk = exercise["老人危險度"] if user.age >= 60 else exercise["一般人危險度"]

                gene = {
                    "動作": exercise["動作"],
                    "大肌群": muscle,
                    "細項肌群": sub_group,
                    "次數": reps,
                    "組數": sets,
                    "休息": rest,
                    "重量": weight,
                    "危險度": risk,
                    "訓練日": day,
                    "訓練量": volume
                }
                chromosome.append(gene)

            #有氧
            elif muscle == "有氧":
                sub_group = "全身"
                exercise = random.choice(exercise_dict[muscle][sub_group])
                reps = random.randint(10, 20)
                sets = random.randint(2, 4)
                rest = 60
                weight = 0
                #計算此動作重量
                volume = reps * sets * weight
                total_volume += volume

                risk = exercise["老人危險度"] if user.age >= 60 else exercise["一般人危險度"]

                gene = {
                    "動作": exercise["動作"],
                    "大肌群": muscle,
                    "細項肌群": sub_group,
                    "次數": reps,
                    "組數": sets,
                    "休息": rest,
                    "重量": weight,
                    "危險度": risk,
                    "訓練日": day,
                    "訓練量": volume
                }
                chromosome.append(gene)

            #主肌群
            else:
                if user.level == "beginner":
                    subgroups = get_beginner_subgroups(muscle)
                else:
                    subgroups = list(exercise_dict[muscle].keys())

                for sub_group in subgroups:
                    gene = generate_random_gene(muscle, sub_group, user)
                    gene["訓練日"] = day

                    #計算重量
                    volume = gene["次數"] * gene["組數"] * gene["重量"]
                    gene["訓練量"] = volume
                    total_volume += volume
                    chromosome.append(gene)

    df = pd.DataFrame(chromosome)
    df.attrs["total_volume"] = total_volume

    return df,total_volume
                    