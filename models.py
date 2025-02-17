from dataclasses import dataclass,field
import config
import node
import cell
import utility

@dataclass
class Mesh:
    num_of_nodes:int = 0
    nodes:list = field(default_factory=list)
    num_of_elements:int = 0
    triangles_WALL:list = field(default_factory=list)
    triangles_INLET:list = field(default_factory=list)
    triangles_OUTLET:list = field(default_factory=list)
    quadrangles_INLET:list = field(default_factory=list)
    quadrangles_OUTLET:list = field(default_factory=list)
    tetras_INTERNAL:list = field(default_factory=list)
    prisms_INTERNAL:list = field(default_factory=list)

    triangles_INNERWALL:list = field(default_factory=list)
    nodes_innersurface:list = field(default_factory=list)


def make_nth_layer(surfacetriangles,surfacenode_dict, nodes_on_inletboundaryedge,nodes_on_outletboundaryedge,nodes_layersurface_dict1,thickratio,mesh):
    #2層目のsurfacenode
    temp = set()
    nth_layer_surfacenode_dict={}
    first_id=float("inf")
    last_id=0
    for surfacetriangle in surfacetriangles:
        nodes = [surfacetriangle.node0, surfacetriangle.node1, surfacetriangle.node2]
        for onenode in nodes:
            if first_id > onenode.id:
                first_id = onenode.id
            if last_id < onenode.id:
                last_id = onenode.id

            if onenode.id in temp:
                nth_layer_surfacenode_dict[onenode.id].x += surfacetriangle.unitnormal_in[0]*thickratio*onenode.scalar_forlayer
                nth_layer_surfacenode_dict[onenode.id].y += surfacetriangle.unitnormal_in[1]*thickratio*onenode.scalar_forlayer
                nth_layer_surfacenode_dict[onenode.id].z += surfacetriangle.unitnormal_in[2]*thickratio*onenode.scalar_forlayer
                nth_layer_surfacenode_dict[onenode.id].sumcountor += 1
            else:
                x =  surfacetriangle.unitnormal_in[0]*thickratio*onenode.scalar_forlayer
                y =  surfacetriangle.unitnormal_in[1]*thickratio*onenode.scalar_forlayer
                z =  surfacetriangle.unitnormal_in[2]*thickratio*onenode.scalar_forlayer
                nth_layer_surfacenode = node.NodeAny(onenode.id + config.num_of_surfacenodes, x, y, z)
                nth_layer_surfacenode_dict[onenode.id] = nth_layer_surfacenode
                temp.add(onenode.id)
    nth_layer_surfacenodes=[]
    for i in range(first_id, last_id+1): ### ここ変えた
        nth_layer_surfacenode_dict[i].x = surfacenode_dict[i].x + nth_layer_surfacenode_dict[i].x/nth_layer_surfacenode_dict[i].sumcountor
        nth_layer_surfacenode_dict[i].y = surfacenode_dict[i].y + nth_layer_surfacenode_dict[i].y/nth_layer_surfacenode_dict[i].sumcountor
        nth_layer_surfacenode_dict[i].z = surfacenode_dict[i].z + nth_layer_surfacenode_dict[i].z/nth_layer_surfacenode_dict[i].sumcountor
        nth_layer_surfacenodes.append(nth_layer_surfacenode_dict[i])
        mesh.nodes.append(nth_layer_surfacenode_dict[i])
        mesh.num_of_nodes += 1

    # 流入出面の四角形
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_inletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id
        quad_id1=right_neighbors[i].id
        quad_id2=right_neighbors[i].id + config.num_of_surfacenodes
        quad_id3=sorted_points[i].id + config.num_of_surfacenodes
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_outletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id
        quad_id1=right_neighbors[i].id
        quad_id2=right_neighbors[i].id + config.num_of_surfacenodes
        quad_id3=sorted_points[i].id + config.num_of_surfacenodes
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1

    # プリズム
    for surfacetriangle in surfacetriangles:
        prism_id0=surfacetriangle.node0.id + config.num_of_surfacenodes
        prism_id1=surfacetriangle.node1.id + config.num_of_surfacenodes
        prism_id2=surfacetriangle.node2.id + config.num_of_surfacenodes
        prism_id3=surfacetriangle.node0.id
        prism_id4=surfacetriangle.node1.id
        prism_id5=surfacetriangle.node2.id
        nth_layer_prism = cell.Prism(prism_id0,prism_id1,prism_id2,prism_id3,prism_id4,prism_id5)
        mesh.prisms_INTERNAL.append(nth_layer_prism)
        mesh.num_of_elements+=1

    #3層目のsurfacenode
    temp = set()
    n3_layer_surfacenode_dict={}
    first_id=float("inf")
    last_id=0
    for surfacetriangle in surfacetriangles:
        nodes = [surfacetriangle.node0, surfacetriangle.node1, surfacetriangle.node2]
        for onenode in nodes:
            if first_id > onenode.id:
                first_id = onenode.id
            if last_id < onenode.id:
                last_id = onenode.id

            if onenode.id in temp:
                n3_layer_surfacenode_dict[onenode.id].x += surfacetriangle.unitnormal_in[0]*0.03*onenode.scalar_forlayer
                n3_layer_surfacenode_dict[onenode.id].y += surfacetriangle.unitnormal_in[1]*0.03*onenode.scalar_forlayer
                n3_layer_surfacenode_dict[onenode.id].z += surfacetriangle.unitnormal_in[2]*0.03*onenode.scalar_forlayer
                n3_layer_surfacenode_dict[onenode.id].sumcountor += 1
            else:
                x =  surfacetriangle.unitnormal_in[0]*0.03*onenode.scalar_forlayer
                y =  surfacetriangle.unitnormal_in[1]*0.03*onenode.scalar_forlayer
                z =  surfacetriangle.unitnormal_in[2]*0.03*onenode.scalar_forlayer
                n3_layer_surfacenode = node.NodeAny(onenode.id + config.num_of_surfacenodes*2, x, y, z)
                n3_layer_surfacenode_dict[onenode.id] = n3_layer_surfacenode
                temp.add(onenode.id)
    n3_layer_surfacenodes=[]
    for i in range(first_id, last_id+1): ### ここ変えた
        n3_layer_surfacenode_dict[i].x = surfacenode_dict[i].x + n3_layer_surfacenode_dict[i].x/n3_layer_surfacenode_dict[i].sumcountor
        n3_layer_surfacenode_dict[i].y = surfacenode_dict[i].y + n3_layer_surfacenode_dict[i].y/n3_layer_surfacenode_dict[i].sumcountor
        n3_layer_surfacenode_dict[i].z = surfacenode_dict[i].z + n3_layer_surfacenode_dict[i].z/n3_layer_surfacenode_dict[i].sumcountor
        n3_layer_surfacenodes.append(n3_layer_surfacenode_dict[i])
        mesh.nodes.append(n3_layer_surfacenode_dict[i])
        mesh.num_of_nodes += 1

    # 流入出面の四角形
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_inletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id+ config.num_of_surfacenodes
        quad_id1=right_neighbors[i].id+ config.num_of_surfacenodes
        quad_id2=right_neighbors[i].id + config.num_of_surfacenodes*2
        quad_id3=sorted_points[i].id + config.num_of_surfacenodes*2
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_outletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id+ config.num_of_surfacenodes
        quad_id1=right_neighbors[i].id+ config.num_of_surfacenodes
        quad_id2=right_neighbors[i].id + config.num_of_surfacenodes*2
        quad_id3=sorted_points[i].id + config.num_of_surfacenodes*2
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1

    # プリズム
    for surfacetriangle in surfacetriangles:
        prism_id0=surfacetriangle.node0.id + config.num_of_surfacenodes*2
        prism_id1=surfacetriangle.node1.id + config.num_of_surfacenodes*2
        prism_id2=surfacetriangle.node2.id + config.num_of_surfacenodes*2
        prism_id3=surfacetriangle.node0.id+ config.num_of_surfacenodes
        prism_id4=surfacetriangle.node1.id+ config.num_of_surfacenodes
        prism_id5=surfacetriangle.node2.id+ config.num_of_surfacenodes
        n3_layer_prism = cell.Prism(prism_id0,prism_id1,prism_id2,prism_id3,prism_id4,prism_id5)
        mesh.prisms_INTERNAL.append(n3_layer_prism)
        mesh.num_of_elements+=1

    #4層目のsurfacenode
    temp = set()
    n4_layer_surfacenode_dict={}
    first_id=float("inf")
    last_id=0
    for surfacetriangle in surfacetriangles:
        nodes = [surfacetriangle.node0, surfacetriangle.node1, surfacetriangle.node2]
        for onenode in nodes:
            if first_id > onenode.id:
                first_id = onenode.id
            if last_id < onenode.id:
                last_id = onenode.id

            if onenode.id in temp:
                n4_layer_surfacenode_dict[onenode.id].x += surfacetriangle.unitnormal_in[0]*0.08*onenode.scalar_forlayer
                n4_layer_surfacenode_dict[onenode.id].y += surfacetriangle.unitnormal_in[1]*0.08*onenode.scalar_forlayer
                n4_layer_surfacenode_dict[onenode.id].z += surfacetriangle.unitnormal_in[2]*0.08*onenode.scalar_forlayer
                n4_layer_surfacenode_dict[onenode.id].sumcountor += 1
            else:
                x =  surfacetriangle.unitnormal_in[0]*0.08*onenode.scalar_forlayer
                y =  surfacetriangle.unitnormal_in[1]*0.08*onenode.scalar_forlayer
                z =  surfacetriangle.unitnormal_in[2]*0.08*onenode.scalar_forlayer
                n4_layer_surfacenode = node.NodeAny(onenode.id + config.num_of_surfacenodes*3, x, y, z)
                n4_layer_surfacenode_dict[onenode.id] = n4_layer_surfacenode  
                temp.add(onenode.id)
    n4_layer_surfacenodes=[]
    for i in range(first_id, last_id+1): ### ここ変えた
        n4_layer_surfacenode_dict[i].x = surfacenode_dict[i].x + n4_layer_surfacenode_dict[i].x/n4_layer_surfacenode_dict[i].sumcountor
        n4_layer_surfacenode_dict[i].y = surfacenode_dict[i].y + n4_layer_surfacenode_dict[i].y/n4_layer_surfacenode_dict[i].sumcountor
        n4_layer_surfacenode_dict[i].z = surfacenode_dict[i].z + n4_layer_surfacenode_dict[i].z/n4_layer_surfacenode_dict[i].sumcountor
        n4_layer_surfacenodes.append(n4_layer_surfacenode_dict[i])  ### 不要..?
        mesh.nodes.append(n4_layer_surfacenode_dict[i])
        mesh.num_of_nodes += 1

    # 流入出面の四角形
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_inletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id+ config.num_of_surfacenodes*2
        quad_id1=right_neighbors[i].id+ config.num_of_surfacenodes*2
        quad_id2=right_neighbors[i].id + config.num_of_surfacenodes*3
        quad_id3=sorted_points[i].id + config.num_of_surfacenodes*3
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_outletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id+ config.num_of_surfacenodes*2
        quad_id1=right_neighbors[i].id+ config.num_of_surfacenodes*2
        quad_id2=right_neighbors[i].id + config.num_of_surfacenodes*3
        quad_id3=sorted_points[i].id + config.num_of_surfacenodes*3
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1

    # プリズム
    for surfacetriangle in surfacetriangles:
        prism_id0=surfacetriangle.node0.id + config.num_of_surfacenodes*3
        prism_id1=surfacetriangle.node1.id + config.num_of_surfacenodes*3
        prism_id2=surfacetriangle.node2.id + config.num_of_surfacenodes*3
        prism_id3=surfacetriangle.node0.id+ config.num_of_surfacenodes*2
        prism_id4=surfacetriangle.node1.id+ config.num_of_surfacenodes*2
        prism_id5=surfacetriangle.node2.id+ config.num_of_surfacenodes*2
        n4_layer_prism = cell.Prism(prism_id0,prism_id1,prism_id2,prism_id3,prism_id4,prism_id5)
        mesh.prisms_INTERNAL.append(n4_layer_prism)
        mesh.num_of_elements+=1


#### 最後の層
    # 流入出面の四角形
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_inletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id+ config.num_of_surfacenodes*3
        quad_id1=right_neighbors[i].id+ config.num_of_surfacenodes*3
        quad_id2=nodes_layersurface_dict1[right_neighbors[i].id-config.num_of_innermeshnodes]
        quad_id3=nodes_layersurface_dict1[sorted_points[i].id-config.num_of_innermeshnodes]
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    sorted_points, right_neighbors = utility.find_right_neighbors_3d(nodes_on_outletboundaryedge, config.reference_point)
    for i in range(len(sorted_points)):
        quad_id0=sorted_points[i].id+ config.num_of_surfacenodes*3
        quad_id1=right_neighbors[i].id+ config.num_of_surfacenodes*3
        quad_id2=nodes_layersurface_dict1[right_neighbors[i].id-config.num_of_innermeshnodes]
        quad_id3=nodes_layersurface_dict1[sorted_points[i].id-config.num_of_innermeshnodes]
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1
        
    # プリズム
    for surfacetriangle in surfacetriangles:
        prism_id0=nodes_layersurface_dict1[surfacetriangle.node0.id-config.num_of_innermeshnodes]
        prism_id1=nodes_layersurface_dict1[surfacetriangle.node1.id-config.num_of_innermeshnodes]
        prism_id2=nodes_layersurface_dict1[surfacetriangle.node2.id-config.num_of_innermeshnodes]
        prism_id3=surfacetriangle.node0.id+ config.num_of_surfacenodes*3
        prism_id4=surfacetriangle.node1.id+ config.num_of_surfacenodes*3
        prism_id5=surfacetriangle.node2.id+ config.num_of_surfacenodes*3
        n5_layer_prism = cell.Prism(prism_id0,prism_id1,prism_id2,prism_id3,prism_id4,prism_id5)
        mesh.prisms_INTERNAL.append(n5_layer_prism)
        mesh.num_of_elements+=1