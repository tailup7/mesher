# Auto Meshing with Optimal Mesh Size
<p align="center">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/0.png" alt="meshing" width="1000"/>
</p>

## Overview
Code that reads in tuce shape and creates a tetra-prism composite mesh. Output file can be used for CFD.  
The mesh size is automatically adjusted even if there are areas where the tube diameter is extraordinary smaller or larger, which would normally require regionalization. <br>
The background mesh function of gmsh is used to control the mesh size ( https://gmsh.info/doc/texinfo/gmsh.html#t7 ). <br>
The output mesh file can be deformed as shown below.

## Usage
+ Copy all the above files to your local environment.
+ Change directory containing the copied files. 
+ Make python venv and install requirements.txt (https://qiita.com/shun_sakamoto/items/7944d0ac4d30edf91fde).
<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/gui.png" alt="meshing" width="500"/>
</p>


+ ``` python main.py ```
+ 「0」: If need, change meshing parameter.
+ 「1」: Select centerline data and tube surface data.
+ 「2」: Excute meshing. Mesh file "allmesh.vtk", "allmesh.msh" will be output in output folder.
  + I recommend installing Gmsh itself. With it, you can open (*.msh) files in the viewer.
  + (If you don't have gmsh, please view the allmesh.vtk file with paraview.)

## input data
<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/inf.png" alt="meshing" width="600"/>
</p>
You need centerline point cloud (*.csv) and the surface of the tube shape (*.stl).  (The first point listed in centerline.csv will be the inflow side). <br>
As figure shows, centerline point cloud must reach near the end face of the tube (The fineness of the centerline point cloud is not important). In addition, the end faces of the tube must be open. <br>
Shapes with bifurcations cannot be meshed >_<.

### CFD result with OpenFOAM
<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/00.png" alt="meshing" width="600"/>
</p>

# Deform Mesh 
You can also deform mesh.
