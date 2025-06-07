import random
import pandas as pd
from chromosome import (generate_weekly_muscle_schedule,
                        generate_chromosome,
                        generate_random_gene
                        )
from fitness import evaluate_fitness
import matplotlib.pyplot as plt

# 1. 初始化族群
def initialize_population(user, pop_size):
    population = []
    for _ in range(pop_size):
        schedule = generate_weekly_muscle_schedule(user)
        chromosome, _ = generate_chromosome(user, schedule)
        population.append(chromosome)
    return population

# 2. 評估族群適應度
def evaluate_population(population, user):
    scored_population = []
    for chromosome in population:
        score, _ = evaluate_fitness(chromosome, user, verbose=False)
        scored_population.append((chromosome, score))
    return sorted(scored_population, key=lambda x: x[1], reverse=True)

# 3. 選擇（Tournament Selection）
def tournament_selection(scored_population, k=3):
    selected = random.sample(scored_population, k)
    selected = sorted(selected, key=lambda x: x[1], reverse=True)
    return selected[0][0]  # 回傳最佳染色體

# 4. 交配（Day-level crossover）
def crossover(parent1, parent2):
    days = list(parent1["訓練日"].unique())
    cut = random.randint(1, len(days) - 1)
    cut_day = days[cut]

    child = pd.concat([
        parent1[parent1["訓練日"] <= cut_day],
        parent2[parent2["訓練日"] > cut_day]
    ])
    return child.reset_index(drop=True)

# 5. 突變（隨機替換一天）
def mutate(chromosome, user, mutation_rate=0.1):
    if random.random() < mutation_rate:
        # 隨機選一天
        day = random.choice(chromosome["訓練日"].unique())
        new_schedule = {day: list(set(chromosome[chromosome["訓練日"] == day]["大肌群"]))}
        mutated_day, _ = generate_chromosome(user, new_schedule)
        # 移除原本該天
        chromosome = chromosome[chromosome["訓練日"] != day]
        # 合併
        chromosome = pd.concat([chromosome, mutated_day], ignore_index=True)
    return chromosome

# 6. 主要 GA 流程
def run_ga(user, generations=100, pop_size=50, elite_size=2, mutation_rate=0.1):
    population = initialize_population(user, pop_size)
    
    best_score_ever = 0
    stop_counter = 0
    patience = 20  # 連續幾代沒進步就停
    fitness_history = [] #用來記錄所有fitness
    for gen in range(generations):
        print(f"\n=== Generation {gen + 1} ===")
        scored = evaluate_population(population, user)
        current_best_score = scored[0][1]
        fitness_history.append(current_best_score)#用來將資料放到fitness_history中
        print(f"Best score: {current_best_score}")

        # Early Stopping 檢查
        if current_best_score > best_score_ever:
            best_score_ever = current_best_score
            stop_counter = 0
        else:
            stop_counter += 1
            if stop_counter >= patience:
                print(f"\nEarly stopping: 已連續 {patience} 代無進步，提前停止演化。")
                break

        # 精英保留
        new_population = [x[0] for x in scored[:elite_size]]

        # 生出下一代
        while len(new_population) < pop_size:
            p1 = tournament_selection(scored)
            p2 = tournament_selection(scored)
            child = crossover(p1, p2)
            child = mutate(child, user, mutation_rate)
            new_population.append(child)

        population = new_population
    #  畫圖
    plt.figure(figsize=(8, 4))
    plt.plot(range(1, len(fitness_history) + 1), fitness_history, marker='o')
    plt.xlabel("Generation")
    plt.ylabel("Best Fitness Score")
    plt.title("GA Fitness Progression")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("static/fitness_progression.png")
    plt.close()
    # 最終結果
    final_scored = evaluate_population(population, user)
    best_chromosome = final_scored[0][0]
    best_score = final_scored[0][1]
    return best_chromosome, best_score