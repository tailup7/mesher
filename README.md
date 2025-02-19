# Auto Meshing with Optinal Mesh Size
<p align="center">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/0.png" alt="meshing" width="1000"/>
</p>

## 概要
チューブ形状のSTLを読み込み、テトラプリズム複合メッシュを作成するコード。流体解析ができるファイルが出力される。本来なら領域分けが必要な、管径が小さくなるor大きくなる部分があっても、自動でメッシュサイズを調整する。
メッシュサイズ制御には、gmshのバックグラウンドメッシュ機能を利用している( https://gmsh.info/doc/texinfo/gmsh.html#t7 )。<br>
出力される解析モデルは、VMDで変形させることができる。

## Usage
+ ローカルに上のファイルを全てコピーする
  + (gmsh本体をインストールすると、GUIで出力ファイルが確認できるので、おすすめします)
+ 「input」フォルダに「WALL.stl」と「centerline.txt」を用意する (WALL.stlは、端面が開いているチューブ形状のSTL, centerline.txtはその中心線点群)
+ 「python main.py」 で実行 (必要なライブラリが無い場合はインストールする。 ex.「pip install gmsh」) 
+ 「output」フォルダに色々出力される。流体解析するデータは「allmesh.msh」

## input data
<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/inf.png" alt="meshing" width="600"/>
</p>
You need centerline point cloud (“centerline.txt”) and the surface of the tube shape (“WALL.stl”) in the “input” folder as input data. As figure shows, centerline point cloud must reach near the end face of the tube shape (The fineness of the centerline point cloud is not important). In addition, the end faces of the tube shape must be open. Shapes with bifurcations cannot be meshed >_<.

### OpenFOAMで計算した結果
<p align="left">
  <img src="https://github.com/tailup7/mesher/blob/main/picture/00.png" alt="meshing" width="600"/>
</p>

