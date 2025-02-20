# Auto Meshing with Optinal Mesh Size
<p align="center">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/0.png" alt="meshing" width="1000"/>
</p>

## Overview
チューブ形状のSTLを読み込み、テトラプリズム複合メッシュを作成するコード。流体解析ができるファイルが出力される。本来なら領域分けが必要な、管径が小さくなるor大きくなる部分があっても、自動でメッシュサイズを調整する。
メッシュサイズ制御には、gmshのバックグラウンドメッシュ機能を利用している( https://gmsh.info/doc/texinfo/gmsh.html#t7 )。<br>
出力される解析モデルは、VMDで変形させることができる。

## Usage
+ ローカルに上のファイルを全てコピーする
+ 「input」フォルダに「WALL.stl」と「centerline.txt」を用意する 
+ 「python main.py」 で実行 (必要なライブラリが無い場合はインストールする。 ex.「pip install gmsh」) 
+ 「output」フォルダに色々出力される。流体解析するデータは「allmesh.msh」
  + (gmsh本体をインストールすると、GUIで出力ファイルが確認できるので、おすすめします)
  + (gmsh本体のインストールが面倒な人は、「main.py」の下から2行目「gmsh.fltk.run()」(GUIを起動して結果を表示するコマンド) を消せば動くと思います。その場合はparaviewなどで「allmesh.vtk」を開いてメッシュを確認してください)

## input data
<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/inf.png" alt="meshing" width="600"/>
</p>
You need centerline point cloud (“centerline.txt”) and the surface of the tube shape (“WALL.stl”) in the “input” folder as input data (The first point listed in centerline.txt will be the inflow side). <br>
As figure shows, centerline point cloud must reach near the end face of the tube (The fineness of the centerline point cloud is not important). In addition, the end faces of the tube must be open. <br>
Shapes with bifurcations cannot be meshed >_<.

### CFD result with OpenFOAM
<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/00.png" alt="meshing" width="600"/>
</p>

