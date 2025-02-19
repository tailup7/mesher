import mygmsh
import node 
import cell
import myio
import config
import models
import utility
import radius
import boundarylayer
import gmsh
import os

# input file
filepath_stl = os.path.join("input", "WALL.stl")
filepath_centerline = os.path.join("input", "centerline.txt")

# backgroundmeshを作成, 管径をもとにスカラー値をセットしてbgm.posとして出力
nodeids, coords ,filepath_stl_bgmsurface = mygmsh.generate_bgm(filepath_stl)
nodes_centerline, node_centerline_dict = myio.read_txt_centerline(filepath_centerline) 
edgeradii = radius.calculate_edgeradius(nodes_centerline, filepath_stl_bgmsurface)
nodes_any = node.coords_to_nodes(nodeids,coords)
nodeany_dict={}                                          
for node_any in nodes_any:
    nodeany_dict[node_any.id] = node_any  
    node_any.find_closest_centerlinenode(nodes_centerline)
    node_any.find_projectable_centerlineedge(nodes_centerline)
    node_any.set_edgeradius(edgeradii)
tetra_list = myio.read_msh_tetra()
myio.write_pos_bgm(tetra_list,nodeany_dict)

# bgm.posを参照し、粗密のある表面メッシュをVTK形式で出力
filepath_vtk = mygmsh.surfacemesh(filepath_stl)
surfacenodes,surfacetriangles = myio.read_vtk_outersurface(filepath_vtk) 
surfacenode_dict={}
for surfacenode in surfacenodes:
    surfacenode.find_closest_centerlinenode(nodes_centerline)
    surfacenode.find_projectable_centerlineedge(nodes_centerline)
    surfacenode.set_edgeradius(edgeradii)
    surfacenode_dict[surfacenode.id] = surfacenode

# 入力 surfacetriangles,
# 一番内側の層を作る#################################################################################
temp = set()
mostinnersurfacenode_dict={}
for surfacetriangle in surfacetriangles:
    surfacetriangle.calc_unitnormal(node_centerline_dict)

    nodes = [surfacetriangle.node0, surfacetriangle.node1, surfacetriangle.node2]
    for onenode in nodes:
        if onenode.id in temp:
            mostinnersurfacenode_dict[onenode.id].x += surfacetriangle.unitnormal_in[0]*utility.calculate_nth_layer_thickratio(config.num_of_layers)*onenode.scalar_forlayer
            mostinnersurfacenode_dict[onenode.id].y += surfacetriangle.unitnormal_in[1]*utility.calculate_nth_layer_thickratio(config.num_of_layers)*onenode.scalar_forlayer
            mostinnersurfacenode_dict[onenode.id].z += surfacetriangle.unitnormal_in[2]*utility.calculate_nth_layer_thickratio(config.num_of_layers)*onenode.scalar_forlayer
            mostinnersurfacenode_dict[onenode.id].sumcountor += 1
        else:
            x =  surfacetriangle.unitnormal_in[0]*utility.calculate_nth_layer_thickratio(config.num_of_layers)*onenode.scalar_forlayer
            y =  surfacetriangle.unitnormal_in[1]*utility.calculate_nth_layer_thickratio(config.num_of_layers)*onenode.scalar_forlayer
            z =  surfacetriangle.unitnormal_in[2]*utility.calculate_nth_layer_thickratio(config.num_of_layers)*onenode.scalar_forlayer
            mostinnersurfacenode = node.NodeAny(onenode.id, x, y, z)
            mostinnersurfacenode_dict[onenode.id] = mostinnersurfacenode
            temp.add(onenode.id)

mostinnersurfacenodes=[]
for i in range(1, config.num_of_surfacenodes+1): 
    mostinnersurfacenode_dict[i].x = surfacenode_dict[i].x + mostinnersurfacenode_dict[i].x/mostinnersurfacenode_dict[i].sumcountor
    mostinnersurfacenode_dict[i].y = surfacenode_dict[i].y + mostinnersurfacenode_dict[i].y/mostinnersurfacenode_dict[i].sumcountor
    mostinnersurfacenode_dict[i].z = surfacenode_dict[i].z + mostinnersurfacenode_dict[i].z/mostinnersurfacenode_dict[i].sumcountor
    mostinnersurfacenodes.append(mostinnersurfacenode_dict[i])

mostinnersurfacetriangles=[]
for surfacetriangle in surfacetriangles:
    node0 = mostinnersurfacenode_dict[surfacetriangle.node0.id]  # idは同じだが、座標だけ変わる
    node1 = mostinnersurfacenode_dict[surfacetriangle.node1.id]
    node2 = mostinnersurfacenode_dict[surfacetriangle.node2.id]
    node0.find_closest_centerlinenode(nodes_centerline)
    node1.find_closest_centerlinenode(nodes_centerline)
    node2.find_closest_centerlinenode(nodes_centerline)
    mostinnersurfacetriangle = cell.Triangle(surfacetriangle.id,node0,node1,node2)
    mostinnersurfacetriangle.calc_unitnormal(node_centerline_dict)
    mostinnersurfacetriangles.append(mostinnersurfacetriangle)
####################################################################################
#出力 mostinnersurfacetriangles, mostinnersurfacenodes

# make tetramesh and add to msh file
filepath_stl = myio.write_stl_mostinnersurface(mostinnersurfacetriangles)
filepath_msh = mygmsh.make_innermesh(filepath_stl)
mesh=models.Mesh()
nodes_innerwall, node_innermesh_dict,mesh = myio.read_msh_innermesh(filepath_msh,mesh)
nearest_pairs = utility.find_nearest_neighbors(nodes_innerwall, mostinnersurfacenodes)
cumulative_error=0
nodes_layersurface_dict={}
for node_innerwall, mostinnersurfacenode,distance in nearest_pairs:
    cumulative_error += distance
    nodes_layersurface_dict[mostinnersurfacenode.id] = node_innerwall.id    # 表面のみだったときのid → 内部メッシュも含めたときのid
print("cumulative eroor is", cumulative_error)

# reset ids of outersurface and add to msh file
nodes_on_inletboundaryedge=[]
nodes_on_outletboundaryedge=[]
for surfacenode in surfacenodes:
    if node_innermesh_dict[nodes_layersurface_dict[surfacenode.id]].on_inlet_boundaryedge:
        surfacenode.on_inlet_boundaryedge=True
        nodes_on_inletboundaryedge.append(surfacenode)
    if node_innermesh_dict[nodes_layersurface_dict[surfacenode.id]].on_outlet_boundaryedge:
        surfacenode.on_outlet_boundaryedge=True
        nodes_on_outletboundaryedge.append(surfacenode)
    surfacenode.id = surfacenode.id + config.num_of_innermeshnodes
    surfacenode_dict[surfacenode.id]=surfacenode   
    mesh.nodes.append(surfacenode) 
    mesh.num_of_nodes += 1

# add outersurface triangles to msh file 
for surfacetriangle in surfacetriangles:
    mesh.triangles_WALL.append(surfacetriangle)
    mesh.num_of_elements += 1

for i in range (1,config.num_of_layers):
    mesh = boundarylayer.make_nthlayer_surfacenode(i, surfacenode_dict, surfacetriangles, mesh)
    mesh = boundarylayer.make_nthlayer_quad(i,nodes_centerline, nodes_on_inletboundaryedge, nodes_on_outletboundaryedge,mesh)
    mesh = boundarylayer.make_nthlayer_prism(i,surfacetriangles,mesh)

mesh=boundarylayer.make_finallayer_quad(nodes_centerline,nodes_layersurface_dict,nodes_on_inletboundaryedge,nodes_on_outletboundaryedge,mesh)
mesh=boundarylayer.make_finallayer_prism(surfacetriangles,nodes_layersurface_dict,mesh)


#models.make_nth_layer(nodes_centerline,surfacetriangles,surfacenode_dict,nodes_on_inletboundaryedge,nodes_on_outletboundaryedge,nodes_layersurface_dict,0.012,mesh)

myio.write_msh_allmesh(mesh)

gmsh.initialize()
gmsh.merge(os.path.join("output", "allmesh.msh"))
gmsh.write(os.path.join("output","allmesh.vtk"))
# mygmsh.GUI_setting()
# mygmsh.gmsh.fltk.run()
gmsh.finalize()