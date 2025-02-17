import mygmsh
import node 
import cell
import myio
import config
import models
import utility
import radius
import os

# TODO: インスタンスのリストをインスタンスとして定義すると、分かりにくいし冗長になるので、インスタンスのリストは普通に 
#           nodes_centerline = [] のように定義する

# parameter for tetraprism
N=4     # num of layers
r=1.4   # growth rate of layer's thickness
h=0.12  # first layer thickness

# parameter for boundarylater
first_layer_ratio = 0.015 # % of diameter
growth_rate = 1.2
num_of_layers = 6

# input file
filepath_stl = os.path.join("input", "WALL.stl")
filepath_centerline = os.path.join("input", "centerline.txt")

# backgroundmeshを作成
nodeids, coords ,filepath_stl_bgmsurface = mygmsh.generate_bgm(filepath_stl)
nodes_centerline, node_centerline_dict = myio.read_txt_centerline(filepath_centerline) #idが0スタートになってしまってるが、gmshと統一するなら0スタートに
edgeradii = radius.calculate_edgeradius(nodes_centerline.nodes_centerline, filepath_stl_bgmsurface)

# スカラー値(半径)を backgroundmesh にセットし、bgm.posとして出力
nodes_any = node.NodesAny()
node.coords_to_nodes(nodeids,coords,nodes_any)
                                                        # nodes_anyがインスタンスになっているために、返り値がなくても動作するが、インスタンスのリストを
nodeany_dict={}                                           # インスタンスにする意味はないし、使いにくいので、nodes_anyは普通のリストに変える
for node_any in nodes_any.nodes_any:
    nodeany_dict[node_any.id] = node_any  
    node_any.find_closest_centerlinenode(nodes_centerline.nodes_centerline)
    node_any.find_projectable_centerlineedge(nodes_centerline.nodes_centerline)
    node_any.set_edgeradius(edgeradii)
tetra_list = myio.read_msh_tetra()
myio.write_pos_bgm(tetra_list,nodeany_dict)

# bgm.posを参照し、粗密のある表面メッシュをVTK形式で出力
filepath_vtk = mygmsh.surfacemesh(filepath_stl)
surfacenodes,surfacetriangles = myio.read_vtk_outersurface(filepath_vtk)  # ここ、node idが1スタートになるように読むときに工夫を入れた
surfacenode_dict={}
for surfacenode in surfacenodes.nodes_any:
    surfacenode.find_closest_centerlinenode(nodes_centerline.nodes_centerline)
    surfacenode.find_projectable_centerlineedge(nodes_centerline.nodes_centerline)
    surfacenode.set_edgeradius(edgeradii)
    surfacenode_dict[surfacenode.id] = surfacenode

# 入力 surfacetriangles,
# 一番内側の層を作る#################################################################################
temp = set()
mostinnersurfacenode_dict={}
for surfacetriangle in surfacetriangles.triangles:
    surfacetriangle.calc_unitnormal(node_centerline_dict)

    nodes = [surfacetriangle.node0, surfacetriangle.node1, surfacetriangle.node2]
    for onenode in nodes:
        if onenode.id in temp:
            mostinnersurfacenode_dict[onenode.id].x += surfacetriangle.unitnormal_in[0]*config.boundarylayer_ratio*onenode.scalar_forlayer
            mostinnersurfacenode_dict[onenode.id].y += surfacetriangle.unitnormal_in[1]*config.boundarylayer_ratio*onenode.scalar_forlayer
            mostinnersurfacenode_dict[onenode.id].z += surfacetriangle.unitnormal_in[2]*config.boundarylayer_ratio*onenode.scalar_forlayer
            mostinnersurfacenode_dict[onenode.id].sumcountor += 1
        else:
            x =  surfacetriangle.unitnormal_in[0]*config.boundarylayer_ratio*onenode.scalar_forlayer
            y =  surfacetriangle.unitnormal_in[1]*config.boundarylayer_ratio*onenode.scalar_forlayer
            z =  surfacetriangle.unitnormal_in[2]*config.boundarylayer_ratio*onenode.scalar_forlayer
            mostinnersurfacenode = node.NodeAny(onenode.id, x, y, z)
            mostinnersurfacenode_dict[onenode.id] = mostinnersurfacenode
            temp.add(onenode.id)

mostinnersurfacenodes=[]
for i in range(1, config.num_of_surfacenodes+1): ### ここ変えた
    mostinnersurfacenode_dict[i].x = surfacenode_dict[i].x + mostinnersurfacenode_dict[i].x/mostinnersurfacenode_dict[i].sumcountor
    mostinnersurfacenode_dict[i].y = surfacenode_dict[i].y + mostinnersurfacenode_dict[i].y/mostinnersurfacenode_dict[i].sumcountor
    mostinnersurfacenode_dict[i].z = surfacenode_dict[i].z + mostinnersurfacenode_dict[i].z/mostinnersurfacenode_dict[i].sumcountor
    mostinnersurfacenodes.append(mostinnersurfacenode_dict[i])

mostinnersurfacetriangles=[]
for surfacetriangle in surfacetriangles.triangles:
    node0 = mostinnersurfacenode_dict[surfacetriangle.node0.id]  # idは同じだが、座標だけ変わる
    node1 = mostinnersurfacenode_dict[surfacetriangle.node1.id]
    node2 = mostinnersurfacenode_dict[surfacetriangle.node2.id]
    node0.find_closest_centerlinenode(nodes_centerline.nodes_centerline)
    node1.find_closest_centerlinenode(nodes_centerline.nodes_centerline)
    node2.find_closest_centerlinenode(nodes_centerline.nodes_centerline)
    mostinnersurfacetriangle = cell.Triangle(surfacetriangle.id,node0,node1,node2)
    mostinnersurfacetriangle.calc_unitnormal(node_centerline_dict)
    mostinnersurfacetriangles.append(mostinnersurfacetriangle)
####################################################################################
#出力 mostinnersurfacetriangles, mostinnersurfacenodes


filepath_stl = myio.write_stl_mostinnersurface(mostinnersurfacetriangles)
filepath_msh = mygmsh.make_innermesh(filepath_stl)

mesh=models.Mesh()
nodes_innerwall, node_innermesh_dict, triangles_innerwall, triangle_innerwall_dict, mesh = myio.read_msh_innermesh(filepath_msh,mesh)
nearest_pairs = utility.find_nearest_neighbors(nodes_innerwall, mostinnersurfacenodes)
cumulative_error=0
nodes_layersurface_dict1={}
nodes_layersurface_dict2={}
for node_innerwall, mostinnersurfacenode,distance in nearest_pairs:
    cumulative_error += distance
    nodes_layersurface_dict1[mostinnersurfacenode.id] = node_innerwall.id    # 表面のみだったときのid → 内部メッシュも含めたときのid
    nodes_layersurface_dict2[node_innerwall.id] = mostinnersurfacenode.id    # 内部メッシュも含めた node id → 表面メッシュのみだったときの node id

# make first layer
nodes_on_inletboundaryedge=[]
nodes_on_outletboundaryedge=[]
for surfacenode in surfacenodes.nodes_any:
    if node_innermesh_dict[nodes_layersurface_dict1[surfacenode.id]].on_inlet_boundaryedge:
        surfacenode.on_inlet_boundaryedge=True
        nodes_on_inletboundaryedge.append(surfacenode)
    if node_innermesh_dict[nodes_layersurface_dict1[surfacenode.id]].on_outlet_boundaryedge:
        surfacenode.on_outlet_boundaryedge=True
        nodes_on_outletboundaryedge.append(surfacenode)
    surfacenode.id = surfacenode.id + config.num_of_innermeshnodes
    
    surfacenode_dict[surfacenode.id]=surfacenode   

    mesh.nodes.append(surfacenode) ##########
    mesh.num_of_nodes += 1

for surfacetriangle in surfacetriangles.triangles:
    # surfacetriangle.node0.id = surfacetriangle.node0.id +config.num_of_innermeshnodes #surfacetriangleを構成するのはsurfacenodeであり、その
    # surfacetriangle.node1.id = surfacetriangle.node1.id +config.num_of_innermeshnodes # idはすでにうえで変えている。
    # surfacetriangle.node2.id = surfacetriangle.node2.id +config.num_of_innermeshnodes
    mesh.triangles_WALL.append(surfacetriangle)
    mesh.num_of_elements += 1

models.make_nth_layer(surfacetriangles,surfacenode_dict,nodes_on_inletboundaryedge,nodes_on_outletboundaryedge,nodes_layersurface_dict1,0.012,mesh)

myio.write_msh_allmesh(mesh)
mygmsh.gmsh.initialize()
mygmsh.gmsh.merge(os.path.join("output", "allmesh.msh"))
mygmsh.GUI_setting()
mygmsh.gmsh.fltk.run()