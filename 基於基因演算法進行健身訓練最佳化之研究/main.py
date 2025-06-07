from user_input import create_user_from_dict
from chromosome import generate_weekly_muscle_schedule, generate_chromosome
from fitness import evaluate_and_plot
from GA_main import run_ga
from collections import defaultdict

# 建立使用者資料
user_data = {
    "name": "班",
    "age": 21,
    "height": 170,
    "weight": 62,
    "level": "beginner",
    "training_days_list": [1, 2, 3, 4, 5],
    "goal": "muscle_gain",
    "target_muscles": ["胸"],
    "known_max_weight_dict": {
        "腿推": {"weight": 80, "reps": 12},
        "臀推": {"weight": 45, "reps": 12},
        "胸推": {"weight": 40, "reps": 12},
        "槓鈴肩推": {"weight": 32, "reps": 10},
        "啞鈴側平舉": {"weight": 12, "reps": 12},
        "俯身飛鳥（啞鈴）": {"weight": 12, "reps": 12},
        "高位下拉": {"weight": 45, "reps": 10},
        "集中彎舉": {"weight": 12, "reps": 12},
        "斜板彎舉": {"weight": 32, "reps": 12},
        "繩索下壓": {"weight": 40, "reps": 12},
        "機械式捲腹": {"weight": 32, "reps": 15}
    }
}

def print_sorted_chromosome(chromosome_df):
    """依照訓練日排序並印出訓練菜單"""
    sorted_df = chromosome_df.copy()
    sorted_df["DayOrder"] = sorted_df["訓練日"].str.extract("(\d+)").astype(int)
    sorted_df = sorted_df.sort_values(by="DayOrder").drop(columns="DayOrder")
    
    print("\n=== 最佳染色體（依訓練日排序） ===")
    print(sorted_df)

def print_muscle_schedule(chromosome_df):
    """根據訓練菜單列出每天訓練的肌群"""
    schedule_by_day = defaultdict(list)
    for _, row in chromosome_df.iterrows():
        day = row["訓練日"]
        muscle = row["大肌群"]
        if muscle not in schedule_by_day[day]:
            schedule_by_day[day].append(muscle)

    sorted_schedule = dict(sorted(schedule_by_day.items(), key=lambda x: int(x[0].replace("Day", ""))))
    print("\n=== 每日肌群分配菜單 ===")
    for day, muscles in sorted_schedule.items():
        print(f"{day}: {muscles}")



# 執行 GA 主流程
best_chromosome, best_score = run_ga(user, generations=10, pop_size=20, elite_size=2, mutation_rate=0.1)

# 顯示最佳染色體
print_muscle_schedule(best_chromosome)
print_sorted_chromosome(best_chromosome)
print(f"\n最佳適應度分數: {best_score}")

# 評估與繪圖
evaluate_and_plot(best_chromosome, user)

