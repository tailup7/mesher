import pandas as pd
import numpy as np

# CSVファイルの読み込み
df = pd.read_csv("original.csv")

# 累積距離を計算
def calculate_curve_length(points):
    total_length = 0.0
    for i in range(1, len(points)):
        p1 = points[i - 1]
        p2 = points[i]
        distance = np.linalg.norm(p2 - p1)  # ユークリッド距離を計算
        total_length += distance
    return total_length

# 各点の座標をnumpy配列に変換
points = df.values
curve_length = calculate_curve_length(points)

print(f"Curve Length: {curve_length}")
