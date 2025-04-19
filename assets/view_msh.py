import gmsh
import tkinter as tk
from tkinter import filedialog

def GUI_setting():
    gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
    gmsh.option.setNumber("Mesh.Lines", 1)
    gmsh.option.setNumber("Geometry.PointLabels", 1)
    gmsh.option.setNumber("Mesh.LineWidth", 2)
    gmsh.option.setNumber("General.MouseInvertZoom", 1)
    gmsh.option.setNumber("General.Axes", 3)
    gmsh.option.setNumber("General.Trackball", 0)
    gmsh.option.setNumber("General.RotationX", 0)
    gmsh.option.setNumber("General.RotationY", 0)
    gmsh.option.setNumber("General.RotationZ", 0)
    gmsh.option.setNumber("General.Terminal", 1)

def select_file():
    root = tk.Tk()
    root.withdraw()  
    filepath = filedialog.askopenfilename(
        title=f"Select mesh file (*.msh)",
        filetypes=[("msh files", "*.msh")]  
    )
    return filepath

if __name__=="__main__":
    gmsh.initialize()
    filepath=select_file()
    GUI_setting()
    gmsh.merge(filepath)
    gmsh.fltk.run()
    gmsh.finalize()