# vmtkで出力される中心線点群のデータファイルは、点の総数が多く、点間隔がバラバラであり、かつバイナリ形式なので
# 点間隔と点の総数を一定にリサンプリングし、csv形式に変換する

import re
import numpy as np
import vtk
import tkinter as tk
from tkinter import filedialog

def select_file():
    root = tk.Tk()
    root.withdraw()  
    filepath = filedialog.askopenfilename(
        title="Select centerline data (*.vtp)", 
        filetypes=[("Text Files", "*.vtp"), ("All Files", "*.*")]
    )
    if not filepath:
        print("No file selected.")
        return None
    return filepath

def convert_vtp_binary_to_ascii(input_filename, output_filename):
    # バイナリ形式のVTPファイルを読み込む
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(input_filename)
    reader.Update()
    # 書き込み用のVTPファイルを設定（ASCII形式で書き出す）
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(output_filename)
    writer.SetInputData(reader.GetOutput())
    writer.SetDataModeToAscii()  # ASCII形式で保存
    writer.Write()

def extract_pointssection_fromvtpfile(filepath):
    nodes_centerline=[]
    coords=[]
    with open (filepath,"r") as file:
        pointssection=False
        for line in file:
            if "<Points>" in line:
                pointssection=True
                continue
            if pointssection:
                if "<DataArray" in line :
                    continue
                if "<InformationKey" in line:
                    break
                nums = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                coords.extend(map(float, nums))

    for i in range(0, len(coords), 3):
        nodes_centerline.append([coords[i], coords[i+1], coords[i+2]])
    return np.array(nodes_centerline)

def get_num_from_console():
    while True:
        try:
            user_input = input("再サンプリング後の点群数を入力してください: ")
            num_points = int(user_input)
            if num_points <= 0:
                print("正の整数を入力してください。")
                continue
            return num_points
        except ValueError:
            print("無効な入力です。数値を入力してください。")

def read_points_from_file(filepath):
    points = []
    with open(filepath, 'r') as file:
        lines = file.readlines()
        for line in lines:
            # 空行やコメント行を無視
            if line.strip() and not line.startswith("#"):
                coordinates = list(map(float, line.split()))  # 数値をfloatに変換
                if len(coordinates) == 3:
                    points.append(coordinates)
    return np.array(points)

def compute_distance(points):
    """2つの座標の間の距離を計算する"""
    return np.sqrt(np.sum(np.diff(points, axis=0)**2, axis=1))

def resample_curve(points, num_points):
    """曲線を等間隔に再サンプリングする"""
    # 曲線全体の累積距離を計算
    distances = compute_distance(points)
    cumulative_distances = np.concatenate(([0], np.cumsum(distances)))

    # 曲線全体の長さ
    total_length = cumulative_distances[-1]

    # 新しい等間隔の点の位置を決定
    new_distances = np.linspace(0, total_length, num_points)

    # 補間用の新しい点を求める
    resampled_points = []
    for d in new_distances:
        # 距離がdに最も近い位置のインデックスを取得
        index = np.searchsorted(cumulative_distances, d)
        
        if index == 0:
            resampled_points.append(points[0])
        elif index == len(cumulative_distances):
            resampled_points.append(points[-1])
        else:
            # 線形補間を行う
            t = (d - cumulative_distances[index-1]) / (cumulative_distances[index] - cumulative_distances[index-1])
            p = points[index-1] + t * (points[index] - points[index-1])
            resampled_points.append(p)

    return np.array(resampled_points)

if __name__ == "__main__":
    filepath = select_file()
    if filepath:
        convert_vtp_binary_to_ascii(filepath, "vmtkcenterline_ascii.vtp")
        nodes_centerline=extract_pointssection_fromvtpfile("vmtkcenterline_ascii.vtp")
        num_of_newcenterline=get_num_from_console()
        resampled_points = resample_curve(nodes_centerline, num_of_newcenterline)
        np.savetxt("centerline_resampled.csv",resampled_points,fmt='%.6f', delimiter=",", header="x,y,z", comments='')