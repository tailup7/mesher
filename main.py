import tkinter as tk
from tkinter import filedialog
import sys
import threading
import time
import func
import myio
import config
import meshinfo
import gmsh
import os
import time
from dataclasses import dataclass,field

class RedirectedOutput:
    """標準出力を `tkinter.Text` にリダイレクトするクラス"""
    def __init__(self, text_widget, color="black"):
        self.text_widget = text_widget
        self.color = color

    def write(self, message):
        self.text_widget.insert(tk.END, message, self.color)  # テキストウィジェットの末尾に追加
        self.text_widget.see(tk.END)  # 最新の出力を自動スクロール

    def flush(self):
        pass  # `flush()` を必要とする場合があるので定義

@dataclass
class Data:
    nodes_centerline:list = field(default_factory=list)
    surfacenodes:list = field(default_factory=list)
    surfacetriangles:list = field(default_factory=list)

default_parameters={
    "MESHSIZE" : 0.5,
    "SCALING_FACTOR" : 0.2,
    "FIRST_LAYER_RATIO":0.015,
    "GROWTH_RATE":1.2,
    "NUM_OF_LAYERS":5
}


Switch=False
data=Data()
gmsh.initialize()

input_files=[]
parameter_entries = {}

# **GUI セットアップ**
root = tk.Tk()
root.title("Mesh Deformation")
root.geometry("800x500") 

# **グリッドレイアウトの設定**
root.grid_rowconfigure(0, weight=1) 
root.grid_rowconfigure(1, weight=1) 
root.grid_rowconfigure(2, weight=1)  
root.grid_rowconfigure(3, weight=2)
root.grid_rowconfigure(4, weight=2)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=2)
root.grid_columnconfigure(2, weight=2)

# **パラメータ入力エリア**
param_frame = tk.Frame(root, relief=tk.RAISED, borderwidth=1)
param_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
# **パラメータタイトル**
label_title = tk.Label(param_frame, text="Meshing Parameter", font=("Arial", 14, "bold"))
label_title.grid(row=0, column=0,  pady=5)
# **各パラメータの入力エリア**
row_index = 1
for param, default_value in default_parameters.items():
    tk.Label(param_frame, text=f"{param}:", anchor="w").grid(row=row_index, column=0, sticky="w", padx=5, pady=3)
    entry = tk.Entry(param_frame, width=10)
    entry.grid(row=row_index, column=1, padx=5, pady=3)
    entry.insert(0, str(default_value))  
    parameter_entries[param] = entry  
    row_index += 1

# **メッシュ生成ボタンエリア**
top_frame = tk.Frame(root, relief=tk.GROOVE, borderwidth=2)
top_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=5)

# テキストウィジェットエリア(コンソール出力を表示する)
bottom_frame = tk.Frame(root)
bottom_frame.grid(row=3, column=0, rowspan=2,columnspan=3,sticky="nsew")

# **入力ファイルリスト表示エリア**
file_frame = tk.Frame(root)
file_frame.grid(row=0, column=1, sticky="nw",padx=10,pady=5)  
listbox_frame = tk.Frame(root)
listbox_frame.grid(row=0, column=1, sticky="n", pady=35)  

# **スクロールバー**
scrollbar = tk.Scrollbar(bottom_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
# **テキストウィジェット（出力エリア）**
text_output = tk.Text(bottom_frame, wrap="word", height=18, width=50, yscrollcommand=scrollbar.set)
text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
# **スクロールバーとテキストの連動**
scrollbar.config(command=text_output.yview)

# **テキストのスタイル**
text_output.tag_configure("stdout", foreground="black")
text_output.tag_configure("stderr", foreground="red")

# **標準出力と標準エラーを `tkinter.Text` にリダイレクト**
sys.stdout = RedirectedOutput(text_output, "stdout")
sys.stderr = RedirectedOutput(text_output, "stderr")

# テキストウィジェット  **処理時間表示エリア**
time_frame = tk.Frame(root)
time_frame.grid(row=2, column=2, sticky="s")
# **処理時間表示ラベル**
time_label = tk.Label(time_frame, text="processing time: --- s", font=("Arial", 12), fg="blue")
time_label.pack(pady=10)

def update_config():
    for param, entry in parameter_entries.items():
        value = entry.get() 
        try:
            if "." in value: 
                setattr(config, param, float(value))
            else: 
                setattr(config, param, int(value))
        except ValueError:
            print(f"⚠ {param} の入力が無効です。数値を入力してください。")
    print("パラメータが更新されました:", {param: getattr(config, param) for param in default_parameters})

def select_files():
    files = filedialog.askopenfilenames(title="select input file",filetypes=[("All files","*.*"), ("STL files","*.stl"), ("Text files","*.txt")])
    for file in files:
        if file not in input_files:
            input_files.append(file)
            listbox.insert(tk.END, file)  

def button1_makemesh():
    global Switch
    if len(input_files)!=2:
        print("エラー: 中心線(*.txt)、表面(*.stl)の順に入力してください！")
        return
    def worker():
        start_time=time.perf_counter() 

        mesh = meshinfo.Mesh() 

        filepath_centerline = input_files[0]
        filepath_stl = input_files[1]
        print(input_files[0])
        print(input_files[1])

        update_config()

        nodes_centerline = myio.read_txt_centerline(filepath_centerline) 
        edgeradii=func.calc_edgeradii(filepath_stl,nodes_centerline)
        root.after(0, gmsh_finalize)  

        root.after(0, gmsh_initialize)
        func.generate_pos_bgm(filepath_stl,nodes_centerline,edgeradii,"original")
        root.after(0, gmsh_finalize) 
        
        root.after(0, gmsh_initialize)
        surfacenode_dict, surfacenodes, surfacetriangles, mesh = func.make_surfacemesh(filepath_stl,nodes_centerline, edgeradii,mesh,"original")
        root.after(0, gmsh_finalize) 

        mesh, layernode_dict,surfacetriangles = func.make_prismlayer(surfacenode_dict,surfacetriangles,mesh)

        root.after(0, gmsh_initialize)
        mesh = func.make_tetramesh(nodes_centerline,layernode_dict,mesh,"original")
        root.after(0, gmsh_finalize)  

        mesh=func.naming_inlet_outlet(mesh,nodes_centerline)
            
        myio.write_msh_allmesh(mesh,"original")    
        gmsh.initialize()
        gmsh.merge(os.path.join("output", "allmesh_original.msh"))
        gmsh.write(os.path.join("output","allmesh_original.vtk"))
        func.GUI_setting()
        gmsh.fltk.run()
        root.after(0, gmsh_finalize)  

        root.after(0, lambda : setattr(data, "nodes_centerline", nodes_centerline))
        root.after(0, lambda : setattr(data, "surfacenodes", surfacenodes))
        root.after(0, lambda : setattr(data, "surfacetriangles", surfacetriangles))
        elapsed_time = time.perf_counter() - start_time  
        root.after(0, lambda: update_time_label(elapsed_time)) 
        root.after(0, set_switch_true)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

def button2_deformmesh():
    if Switch:
        if len(input_files)!=2:
            print("Error")
            return
        def worker():
            gmsh.initialize()
            start_time=time.perf_counter()

            update_config()
            filepath_targetcenterline = input_files[0]
            filepath_radius = input_files[1]
            mesh_deform = meshinfo.Mesh()
            
            targetradius = myio.read_txt_edgeradii(filepath_radius)
            nodes_targetcenterline = myio.read_txt_targetcenterline(filepath_targetcenterline)

            filepath_movedsurface, nodes_moved_dict, surfacetriangles_moved, mesh_deform = func.deform_surface(nodes_targetcenterline,  
                                                                                                                targetradius,
                                                                                                                data.nodes_centerline,
                                                                                                                data.surfacenodes,
                                                                                                                data.surfacetriangles,mesh_deform)

            root.after(0, gmsh_initialize)
            func.generate_pos_bgm(filepath_movedsurface,nodes_targetcenterline,targetradius,"deform")
            root.after(0, gmsh_finalize) 

            # 左辺の返り値surfacetrianglesは不要な気がする
            mesh_deform, layernode_dict, surfacetriangles_moved = func.make_prismlayer(nodes_moved_dict,surfacetriangles_moved,mesh_deform)

            root.after(0, gmsh_initialize)
            mesh_deform = func.make_tetramesh(nodes_targetcenterline,layernode_dict,mesh_deform,"deform")
            root.after(0, gmsh_finalize)  

            mesh_deform=func.naming_inlet_outlet(mesh_deform,nodes_targetcenterline)
            
            myio.write_msh_allmesh(mesh_deform,"deform")    
            gmsh.initialize()
            gmsh.merge(os.path.join("output", "allmesh_deform.msh"))
            gmsh.write(os.path.join("output","allmesh_deform.vtk"))
            func.GUI_setting()
            gmsh.fltk.run()

            elapsed_time = time.perf_counter() - start_time
            root.after(0, lambda: update_time_label(elapsed_time))
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

def description():
    print("Make Mesh   : Please input two files. 1.centerline (.txt) 2.tubesurface (.stl)")
    print("Deform Mesh : If Make Mesh is already executed, you need...")
    print("              1. target_centerline (.txt) 2. target_radius (.txt)")

def gmsh_finalize():
    gmsh.finalize()
    print("Execute gmsh.finalize()")

def gmsh_initialize():
    gmsh.initialize()
    print("Execute gmsh.initialize()")

def update_time_label(elapsed_time):
    time_label.config(text=f"processing time: {elapsed_time:.4f} s")

def reset_files():
    input_files.clear()  
    listbox.delete(0, tk.END)  

def set_switch_true():
    global Switch
    Switch = True

gmsh.finalize()

# **ファイル選択ボタン**
select_button = tk.Button(file_frame, text="Select input files", command=select_files)
select_button.grid(row=0, column=0, padx=5)  

# **ファイル一覧表示用の Listbox**
listbox = tk.Listbox(listbox_frame, width=50, height=10)
listbox.grid(row=0, column=0, sticky="nsew")  

# **ファイルリセットボタン**
reset_button = tk.Button(file_frame, text="Reset files", command=reset_files)
reset_button.grid(row=0, column=1, padx=5)  # `select_button` の隣に配置

#**処理ボタン**
button1 = tk.Button(top_frame, text="Make Mesh", command=button1_makemesh)
button1.grid(row=2, column=2, padx=10, pady=5)

button2 = tk.Button(top_frame, text="Deform Mesh", command=button2_deformmesh)
button2.grid(row=3, column=2, padx=10, pady=5)

description()
root.mainloop()