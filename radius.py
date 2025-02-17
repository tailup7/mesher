import utility
import node
import myio
import node
import trimesh
import numpy as np
import config

def calculate_edgeradius(nodes_centerline,filepath_stl_bgmsurface):
    mesh = trimesh.load_mesh(filepath_stl_bgmsurface)
    vertices = mesh.vertices 
    unique_nodes = np.unique(vertices, axis=0)
    surfacenodes = unique_nodes.tolist()

    edgeradii=[]
    countor=[]    
    edgeradii_smooth = []
    for i in range(config.num_of_centerlinenodes+1):
        edgeradii.append(0.0)
        countor.append(0)
        edgeradii_smooth.append(0.0)

    for i in range(len(surfacenodes)):
        surfacenode=node.NodeAny(i,surfacenodes[i][0],surfacenodes[i][1],surfacenodes[i][2])
        surfacenode.find_closest_centerlinenode(nodes_centerline)
        surfacenode.find_projectable_centerlineedge(nodes_centerline)
        if surfacenode.projectable_centerlineedge_id != None:
            edgeradii[surfacenode.projectable_centerlineedge_id+1] += surfacenode.projectable_centerlineedge_distance
            countor[surfacenode.projectable_centerlineedge_id+1]+=1
        else:
            if surfacenode.closest_centerlinenode_id==0:
                edgeradii[0] += utility.calculate_PH_length(surfacenode,nodes_centerline[0],nodes_centerline[1])
                countor[0] += 1
            elif surfacenode.closest_centerlinenode_id==config.num_of_centerlinenodes-1:
                edgeradii[config.num_of_centerlinenodes] += utility.calculate_PH_length(surfacenode,nodes_centerline[-2],nodes_centerline[-1])
                countor[config.num_of_centerlinenodes] += 1
            else:
                edgeradii[surfacenode.closest_centerlinenode_id]+=surfacenode.closest_centerlinenode_distance
                countor[surfacenode.closest_centerlinenode_id] += 1
                edgeradii[surfacenode.closest_centerlinenode_id+1]+=surfacenode.closest_centerlinenode_distance
                countor[surfacenode.closest_centerlinenode_id+1] += 1

    for i in range(len(edgeradii)):
        if countor[i]!=0:
            edgeradii[i]=edgeradii[i]/countor[i]
    
    if edgeradii[0] < edgeradii[1]*0.7:
        edgeradii[0] = edgeradii[1]
    if edgeradii[-1] < edgeradii[-2]*0.7:
        edgeradii[-1]=edgeradii[-2]

    edgeradii_smooth[0]=(edgeradii[0]+edgeradii[1])/2
    edgeradii_smooth[-1]=(edgeradii[-1]+edgeradii[-2])/2
    for i in range(1,len(edgeradii)-1):
        edgeradii_smooth[i] = (edgeradii[i-1]+edgeradii[i]+edgeradii[i+1])/3

    config.inlet_radius = edgeradii_smooth[0]
    config.outlet_radius = edgeradii_smooth[-1]
    myio.write_txt_edgeradii(edgeradii_smooth)
    return edgeradii_smooth



