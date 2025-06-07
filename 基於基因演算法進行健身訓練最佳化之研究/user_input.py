from typing import Optional, List

class User:
    def __init__(self, name: str, age: int, height: float, weight: float, level: str,
                 training_days_list: Optional[List[int]]=None, goal: str = "muscle_gain",
                 known_max_weight_dict: Optional[float] = None,
                 target_muscles: Optional[List[str]] = None):
        self.name = name
        self.age = age
        self.height = height
        self.weight = weight
        self.level = level.lower()
        self.goal = goal  # 增肌、減脂
        self.target_muscles = target_muscles or []
        self.bmi = self.weight / ((self.height/100)**2) #BMI計算
        self.training_days_list = training_days_list or [1,2,3]
        self.training_days = len(self.training_days_list) #計算天

        # 使用者最大重量資料
        self.known_max_weight_dict = known_max_weight_dict or {
            "腿推": {"weight": None, "reps": None},
            "臀推": {"weight": None, "reps": None},
            "胸推": {"weight": None, "reps": None},
            "槓鈴肩推": {"weight": None, "reps": None},
            "啞鈴側平舉": {"weight": None, "reps": None},
            "俯身飛鳥（啞鈴）": {"weight": None, "reps": None},
            "高位下拉": {"weight": None, "reps": None},
            "集中彎舉": {"weight": None, "reps": None},
            "斜板彎舉": {"weight": None, "reps": None},
            "繩索下壓": {"weight": None, "reps": None},
            "機械式捲腹": {"weight": None, "reps": None}
        }

        # 驗證基本資料
        self.validate()

        self.estimated_total_volume = self.estimate_total_volume()
    #防呆
    def validate(self):
        if self.age <= 14:
            raise ValueError("此程式不推薦年齡小於14歲")
        if self.weight <= 0:
            raise ValueError("體重不可小於 0")
        if self.height <= 100:
            raise ValueError("身高不可小於 100 公分")
        if self.bmi < 12:
            raise ValueError(f"BMI過低 ({self.bmi:.2f})，請確認輸入資料")
        if self.level not in {"beginner", "intermediate", "advanced"}:
            raise ValueError(f"未知的訓練等級：{self.level}")
        if self.goal not in {"muscle_gain", "fat_loss"}:
            raise ValueError(f"未知的訓練目標：{self.goal}")
        if not (3 <= len(self.training_days_list) <= 5):
            raise ValueError("訓練日數必須介於 3 到 5 天之間")
            
    def summary(self):
        return {
            "Name": self.name,
            "Age": self.age,
            "Height(cm)": self.height,
            "Weight(kg)": self.weight,
            "BMI": round(self.bmi, 2),
            "Level": self.level,
            "Goal": self.goal,
            "Estimated Total Volume (kg)": self.estimated_total_volume,
            "Target Muscles": self.target_muscles,
            "Weekly Training Days": self.training_days_list,
            "Known Max Weights": self.known_max_weight_dict
        }
    
    #根據等級推估一周合理訓練量
    def estimate_total_volume(self) -> int:
        if self.level == "beginner":
            return 6000
        elif self.level == "intermediate":
            return 12000
        elif self.level == "advanced":
            return 18000
        else:
            return 8000  # 預設值
        
    #透過重量次數計算1RM公式
    def estimate_1RM_by_reps(self,weight:float,reps:int):
        if reps <= 1:
            return weight
        return round(weight * (1 + 0.0333 * reps), 1)
    
    #避免收到前端的值不對
    def is_valid_input(self, entry: dict) -> bool:
        return (
            isinstance(entry, dict) and
            entry.get("weight") is not None and
            entry.get("reps") is not None and
            isinstance(entry["weight"], (int, float)) and
            isinstance(entry["reps"], int) and
            entry["weight"] > 0 and
            entry["reps"] > 0
        )
    #透過代表性動作推算其他部位1RM
    def estimate_muscle_group_1RM(self)-> dict[str, float]:
        d = self.known_max_weight_dict
        est = {}
        e1rm = self.estimate_1RM_by_reps

        #腿部
        if self.is_valid_input(d.get("腿推")):
            leg_1rm = e1rm(d["腿推"]["weight"], d["腿推"]["reps"])
            est["股四頭"] = leg_1rm
            est["股二頭"] = round(leg_1rm * 0.3, 1)
        else:
            raise ValueError("腿推資料不完整或格式錯誤")
        
        #臀部
        if self.is_valid_input(d.get("臀推")):
            est["臀肌"] = e1rm(d["臀推"]["weight"], d["臀推"]["reps"])
        else:
            raise ValueError("臀推資料不完整或格式錯誤")
        
        #胸部
        if self.is_valid_input(d.get("胸推")):
            chest_1rm = e1rm(d["胸推"]["weight"], d["胸推"]["reps"])
            est["胸大肌"] = chest_1rm
            est["中下胸"] = round(chest_1rm * 0.70, 1)
            est["上胸肌"] = round(chest_1rm * 0.15, 1)
        else:
            raise ValueError("胸推資料不完整或格式錯誤")
        
        #肩部
        if self.is_valid_input(d.get("槓鈴肩推")):
            est["前束"] = e1rm(d["槓鈴肩推"]["weight"], d["槓鈴肩推"]["reps"])
        else:
            raise ValueError("槓鈴肩推資料不完整或格式錯誤")
        
        if self.is_valid_input(d.get("啞鈴側平舉")):
            est["中束"] = e1rm(d["啞鈴側平舉"]["weight"], d["啞鈴側平舉"]["reps"])
        else:
            raise ValueError("啞鈴側平舉資料不完整或格式錯誤")
        
        if self.is_valid_input(d.get("俯身飛鳥（啞鈴）")):
            est["後束"] = e1rm(d["俯身飛鳥（啞鈴）"]["weight"], d["俯身飛鳥（啞鈴）"]["reps"])
        else:
            raise ValueError("俯身飛鳥資料不完整或格式錯誤")
          
        #背部
        if self.is_valid_input(d.get("高位下拉")):
            back_1rm = e1rm(d["高位下拉"]["weight"], d["高位下拉"]["reps"])
            est["背擴肌"] = round(back_1rm * 0.6, 1)
            est["斜方肌"] = round(back_1rm * 0.2, 1)
            est["中下背"] = round(back_1rm * 0.2, 1)
        else:
            raise ValueError("高位下拉資料不完整或格式錯誤")
        #二頭
        if self.is_valid_input(d.get("集中彎舉")):
            est["二頭(短頭)"] = e1rm(d["集中彎舉"]["weight"], d["集中彎舉"]["reps"])
            est["前臂"] = round(est["二頭(短頭)"] * 0.4, 1) 
        else:
            raise ValueError("集中彎舉資料不完整或格式錯誤")     
        if self.is_valid_input(d.get("斜板彎舉")):
            est["二頭(長頭)"] = e1rm(d["斜板彎舉"]["weight"], d["斜板彎舉"]["reps"])
        else:
            raise ValueError("斜板彎舉資料不完整或格式錯誤")        
        #三頭
        if self.is_valid_input(d.get("繩索下壓")):
            est["三頭"] = e1rm(d["繩索下壓"]["weight"], d["繩索下壓"]["reps"])
        else:
            raise ValueError("繩索下壓資料不完整或格式錯誤")        
        #核心
        if self.is_valid_input(d.get("機械式捲腹")):
            est["腹"] = e1rm(d["機械式捲腹"]["weight"], d["機械式捲腹"]["reps"])
        else:
            raise ValueError("機械式捲腹資料不完整或格式錯誤")
        return est

# 建立使用者並輸入資料
def create_user_from_dict(data: dict) -> User:
    try:
        # DayX 轉成數字
        raw_list = data.get("training_days_list", [])
        data["training_days_list"] = [int(day.replace("Day", "")) for day in raw_list]

        user = User(
            name=data.get("name", "未命名"),
            age=int(data.get("age", 18)),
            height=float(data.get("height", 170)),
            weight=float(data.get("weight", 60)),
            level=str(data.get("level", "beginner")),
            training_days_list=data.get("training_days_list", [1, 2, 3]),
            goal=data.get("goal", "muscle_gain"),
            target_muscles=data.get("target_muscles", []),
            known_max_weight_dict=data.get("known_max_weight_dict", None)
        )
        return user
    except Exception as e:
        raise ValueError(f"建立 User 物件失敗：{e}")