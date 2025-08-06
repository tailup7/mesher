# Auto Meshing with Optimal Mesh Size
<p align="center">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/0.png" alt="meshing" width="1000"/>
</p>

## Overview
This is code that automatically generates a tetra-prism hybrid mesh (* .msh) from tube shape (*.stl) by using Gmsh python API. The features are as follows. 
+ Output mesh data can be used for CFD.  
+ The mesh size is automatically adjusted even if there are areas where the tube diameter is extraordinary smaller or larger, which would normally require regionalization for meshing. <br>
( In this code, background mesh function of Gmsh is used to control the mesh size ( https://gmsh.info/doc/texinfo/gmsh.html#t7 ). )
+ Thickness of boundary layer (= prism cells) is also adjusted as figure below. <br>
+ Output mesh model can be deformed as shown below. <br>



<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/000.png" alt="meshing" width="600"/>
</p>

## Usage
+ Copy all the above files to your local environment.
+ Change directory containing the copied files. 
+ Make python venv and install requirements.txt (https://qiita.com/shun_sakamoto/items/7944d0ac4d30edf91fde).
+ If you don't install Gmsh itself, please delete the next sentence in the main.py.
+ ``` gmsh.fltk.run() ```
+ and then,
+ ``` python main.py ```
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
You can also deform mesh and do fluid analysis.

<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/deform.png" alt="meshing" width="800"/>
</p>

