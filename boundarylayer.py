import utility
import node
import utility
import cell
import numpy as np
import config

def make_mostinnersurface(nodes_centerline,surfacenode_dict,surfacetriangles):
    temp = set()
    mostinnersurfacenode_dict={}
    for surfacetriangle in surfacetriangles:
        surfacetriangle.calc_unitnormal(nodes_centerline)
        nodes = [surfacetriangle.node0, surfacetriangle.node1, surfacetriangle.node2]
        for onenode in nodes:
            scalingfactor=utility.calculate_nth_layer_thickratio(config.NUM_OF_LAYERS)*onenode.scalar_forlayer
            if onenode.id in temp:
                mostinnersurfacenode_dict[onenode.id].x += scalingfactor*surfacetriangle.unitnormal_in[0]
                mostinnersurfacenode_dict[onenode.id].y += scalingfactor*surfacetriangle.unitnormal_in[1]
                mostinnersurfacenode_dict[onenode.id].z += scalingfactor*surfacetriangle.unitnormal_in[2]
                mostinnersurfacenode_dict[onenode.id].sumcountor += 1
            else:
                x =  scalingfactor*surfacetriangle.unitnormal_in[0]
                y =  scalingfactor*surfacetriangle.unitnormal_in[1]
                z =  scalingfactor*surfacetriangle.unitnormal_in[2]
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
        mostinnersurfacetriangle.calc_unitnormal(nodes_centerline)
        mostinnersurfacetriangles.append(mostinnersurfacetriangle)
    return mostinnersurfacetriangles, mostinnersurfacenodes

def make_nthlayer_surfacenode(n, surfacenode_dict,surfacetriangles, mesh):
    temp = set()
    nth_layer_surfacenode_dict={}
    layernode_dict={}
    for surfacetriangle in surfacetriangles:
        nodes = [surfacetriangle.node0, surfacetriangle.node1, surfacetriangle.node2]
        for onenode in nodes:
            scalingfactor = utility.calculate_nth_layer_thickratio(n)*onenode.scalar_forlayer
            if onenode.id in temp:
                nth_layer_surfacenode_dict[onenode.id].x += scalingfactor*surfacetriangle.unitnormal_in[0]
                nth_layer_surfacenode_dict[onenode.id].y += scalingfactor*surfacetriangle.unitnormal_in[1]
                nth_layer_surfacenode_dict[onenode.id].z += scalingfactor*surfacetriangle.unitnormal_in[2]
                nth_layer_surfacenode_dict[onenode.id].sumcountor += 1
            else:
                x =  scalingfactor*surfacetriangle.unitnormal_in[0]
                y =  scalingfactor*surfacetriangle.unitnormal_in[1]
                z =  scalingfactor*surfacetriangle.unitnormal_in[2]
                nth_layer_surfacenode = node.NodeAny(onenode.id + config.num_of_surfacenodes*n, x, y, z)
                nth_layer_surfacenode.closest_centerlinenode_id = onenode.closest_centerlinenode_id
                nth_layer_surfacenode_dict[onenode.id] = nth_layer_surfacenode
                temp.add(onenode.id)
    for i in range(1,config.num_of_surfacenodes+1):
        nth_layer_surfacenode_dict[i].x = surfacenode_dict[i].x + nth_layer_surfacenode_dict[i].x/nth_layer_surfacenode_dict[i].sumcountor
        nth_layer_surfacenode_dict[i].y = surfacenode_dict[i].y + nth_layer_surfacenode_dict[i].y/nth_layer_surfacenode_dict[i].sumcountor
        nth_layer_surfacenode_dict[i].z = surfacenode_dict[i].z + nth_layer_surfacenode_dict[i].z/nth_layer_surfacenode_dict[i].sumcountor
        layernode_dict[i+config.num_of_surfacenodes*n] = nth_layer_surfacenode_dict[i]
        mesh.nodes.append(nth_layer_surfacenode_dict[i])
        mesh.num_of_nodes += 1
    return mesh,layernode_dict

def make_nthlayer_quad(n,nodes_centerline, nodes_on_inletboundaryedge, nodes_on_outletboundaryedge,mesh):
    innerpoint_vec = np.array([nodes_centerline[5].x,nodes_centerline[5].y,nodes_centerline[5].z])
    utility.find_right_neighbors(nodes_on_inletboundaryedge, innerpoint_vec)
    for node_on_inletboundaryedge in nodes_on_inletboundaryedge:
        quad_id0=node_on_inletboundaryedge.id + config.num_of_surfacenodes*(n-1)
        quad_id1=node_on_inletboundaryedge.right_node_id + config.num_of_surfacenodes*(n-1)
        quad_id2=node_on_inletboundaryedge.right_node_id + config.num_of_surfacenodes*n
        quad_id3=node_on_inletboundaryedge.id + config.num_of_surfacenodes*n
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    innerpoint_vec = np.array([nodes_centerline[-5].x,nodes_centerline[-5].y,nodes_centerline[-5].z])
    utility.find_right_neighbors(nodes_on_outletboundaryedge, innerpoint_vec)
    for node_on_outletboundaryedge in nodes_on_outletboundaryedge:
        quad_id0=node_on_outletboundaryedge.id+ config.num_of_surfacenodes*(n-1)
        quad_id1=node_on_outletboundaryedge.right_node_id+ config.num_of_surfacenodes*(n-1)
        quad_id2=node_on_outletboundaryedge.right_node_id + config.num_of_surfacenodes*n
        quad_id3=node_on_outletboundaryedge.id + config.num_of_surfacenodes*n
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1
    return mesh

def make_nthlayer_quad_new(i,nodes_centerline, nodes_on_inletboundaryedge, nodes_on_outletboundaryedge,mesh):
    innerpoint_vec = np.array([nodes_centerline[5].x,nodes_centerline[5].y,nodes_centerline[5].z])
    utility.find_right_neighbors(nodes_on_inletboundaryedge, innerpoint_vec)
    for node_on_inletboundaryedge in nodes_on_inletboundaryedge:
        quad_id0=node_on_inletboundaryedge.id - config.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id1=node_on_inletboundaryedge.right_node_id - config.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id2=node_on_inletboundaryedge.right_node_id - config.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad_id3=node_on_inletboundaryedge.id - config.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    innerpoint_vec = np.array([nodes_centerline[-5].x,nodes_centerline[-5].y,nodes_centerline[-5].z])
    utility.find_right_neighbors(nodes_on_outletboundaryedge, innerpoint_vec)
    for node_on_outletboundaryedge in nodes_on_outletboundaryedge:
        quad_id0=node_on_outletboundaryedge.id- config.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id1=node_on_outletboundaryedge.right_node_id- config.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id2=node_on_outletboundaryedge.right_node_id - config.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad_id3=node_on_outletboundaryedge.id - config.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1
    return mesh

def make_nthlayer_prism(n,surfacetriangles,mesh):
    for surfacetriangle in surfacetriangles:
        prism_id0=surfacetriangle.node0.id + config.num_of_surfacenodes*n
        prism_id1=surfacetriangle.node1.id + config.num_of_surfacenodes*n
        prism_id2=surfacetriangle.node2.id + config.num_of_surfacenodes*n
        prism_id3=surfacetriangle.node0.id + config.num_of_surfacenodes*(n-1)
        prism_id4=surfacetriangle.node1.id + config.num_of_surfacenodes*(n-1)
        prism_id5=surfacetriangle.node2.id + config.num_of_surfacenodes*(n-1)
        nth_layer_prism = cell.Prism(prism_id0,prism_id1,prism_id2,prism_id3,prism_id4,prism_id5)
        mesh.prisms_INTERNAL.append(nth_layer_prism)
        mesh.num_of_elements+=1
    return mesh

def make_finallayer_quad(nodes_centerline,nodes_layersurface_dict,nodes_on_inletboundaryedge,nodes_on_outletboundaryedge,mesh):
    innerpoint_vec = np.array([nodes_centerline[5].x,nodes_centerline[5].y,nodes_centerline[5].z])
    utility.find_right_neighbors(nodes_on_inletboundaryedge, innerpoint_vec)
    for node_on_inletboundaryedge in nodes_on_inletboundaryedge:
        quad_id0=node_on_inletboundaryedge.id+ config.num_of_surfacenodes*(config.NUM_OF_LAYERS-1)
        quad_id1=node_on_inletboundaryedge.right_node_id+ config.num_of_surfacenodes*(config.NUM_OF_LAYERS-1)
        quad_id2=nodes_layersurface_dict[node_on_inletboundaryedge.right_node_id-config.num_of_innermeshnodes]
        quad_id3=nodes_layersurface_dict[node_on_inletboundaryedge.id-config.num_of_innermeshnodes]
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    innerpoint_vec = np.array([nodes_centerline[-5].x,nodes_centerline[-5].y,nodes_centerline[-5].z])
    utility.find_right_neighbors(nodes_on_outletboundaryedge, innerpoint_vec)
    for node_on_outletboundaryedge in nodes_on_outletboundaryedge:
        quad_id0=node_on_outletboundaryedge.id+ config.num_of_surfacenodes*(config.NUM_OF_LAYERS-1)
        quad_id1=node_on_outletboundaryedge.right_node_id+ config.num_of_surfacenodes*(config.NUM_OF_LAYERS-1)
        quad_id2=nodes_layersurface_dict[node_on_outletboundaryedge.right_node_id-config.num_of_innermeshnodes]
        quad_id3=nodes_layersurface_dict[node_on_outletboundaryedge.id-config.num_of_innermeshnodes]
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1
    return mesh

def make_finallayer_prism(surfacetriangles,nodes_layersurface_dict,mesh):
    for surfacetriangle in surfacetriangles:
        prism_id0=nodes_layersurface_dict[surfacetriangle.node0.id-config.num_of_innermeshnodes]
        prism_id1=nodes_layersurface_dict[surfacetriangle.node1.id-config.num_of_innermeshnodes]
        prism_id2=nodes_layersurface_dict[surfacetriangle.node2.id-config.num_of_innermeshnodes]
        prism_id3=surfacetriangle.node0.id+ config.num_of_surfacenodes*(config.NUM_OF_LAYERS-1)
        prism_id4=surfacetriangle.node1.id+ config.num_of_surfacenodes*(config.NUM_OF_LAYERS-1)
        prism_id5=surfacetriangle.node2.id+ config.num_of_surfacenodes*(config.NUM_OF_LAYERS-1)
        n5_layer_prism = cell.Prism(prism_id0,prism_id1,prism_id2,prism_id3,prism_id4,prism_id5)
        mesh.prisms_INTERNAL.append(n5_layer_prism)
        mesh.num_of_elements+=1
    return mesh