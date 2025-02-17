import gmsh
import tkinter as tk
from tkinter import filedialog
import os

root = tk.Tk()
root.withdraw()  # GUIウィンドウを表示しない
filepath = filedialog.askopenfilename()



gmsh.initialize()

path = os.path.dirname(os.path.abspath(__file__))
gmsh.merge(os.path.join(path, filepath))
# 1がON/0がOFF
# 2次元メッシュの可視化ON/OFF
gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
    
gmsh.option.setNumber("Mesh.Lines", 1)
# 0次元のEntityの可視化ON?OFF
gmsh.option.setNumber("Geometry.PointLabels", 1)
# メッシュの線の太さを指定
gmsh.option.setNumber("Mesh.LineWidth", 2)
# gmshではマウスのホイールのズーンオン/ズームオフがparaviewとは逆なので、paraviewと一緒にする
gmsh.option.setNumber("General.MouseInvertZoom", 1)
# モデルのサイズが簡単に確認できるように、モデルを囲む直方体メモリを表示
gmsh.option.setNumber("General.Axes", 3)
    
gmsh.option.setNumber("General.Trackball", 0)
# GUIが表示された時の、目線の方向を(0,0,0)に指定
gmsh.option.setNumber("General.RotationX", 0)
gmsh.option.setNumber("General.RotationY", 0)
gmsh.option.setNumber("General.RotationZ", 0)
# gmshのターミナルに情報を表示
gmsh.option.setNumber("General.Terminal", 1)

gmsh.fltk.run()
gmsh.finalize()