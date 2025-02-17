import utility
import config
import numpy as np
import sys

# gmsh.model.mesh.getNodes() の1つめの返り値は、得られた全Nodeのid のリスト。
# 2つめの返り値は、得られる全Nodeのx,y,z座標成分をまとめたリスト。これらをnodeごとの情報に整理する
def coords_to_nodes(nodeids, coords, nodes_any):
    if len(coords)%3!=0:
        print("mylib_info   : coords_to_nodes error.")
        sys.exit()
    else:
        for i in range(len(nodeids)):
            x = coords[3*i]
            y = coords[3*i+1]
            z = coords[3*i+2]
            id = nodeids[i]
            node_any = NodeAny(id,x,y,z)
            nodes_any.append(node_any)
    print(f"info_utility   : node count after postprocess gmsh is {len(nodes_any.nodes_any)}")

class NodeCenterline:
    def __init__(self,id,x,y,z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"NodeAny(id={self.id}, x={self.x}, y={self.y}, z={self.z})"

class NodesCenterline:
    def __init__(self):
        self.nodes_centerline=[]

    def append(self,node_centerline):
        self.nodes_centerline.append(node_centerline)

class NodeAny:
    def __init__(self,id,x,y,z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.closest_centerlinenode_id = None
        self.closest_centerlinenode_distance = None
        self.projectable_centerlineedge_id = None
        self.projectable_centerlineedge_distance = None
        self.edgeradius = None
        self.scalar_forbgm = None
        self.scalar_forlayer=None
        self.sumcountor = 1 
        self.on_inlet_boundaryedge=False
        self.on_outlet_boundaryedge=False

    def __str__(self):
        return f"NodeAny(id={self.id}, x={self.x}, y={self.y}, z={self.z})"
    
    def find_closest_centerlinenode(self,nodes_centerline):
        min_distance_square = float("inf")
        for node_centerline in nodes_centerline:
            distance_square = (self.x-node_centerline.x)**2 + (self.y-node_centerline.y)**2 + (self.z-node_centerline.z)**2
            if distance_square < min_distance_square:
                min_distance_square = distance_square
                self.closest_centerlinenode_id = node_centerline.id
                self.closest_centerlinenode_distance = np.sqrt(min_distance_square)

    # projectable_centerlineedge の総数は 中心線 node - 1
    def find_projectable_centerlineedge(self,nodes_centerline):
        ccid = self.closest_centerlinenode_id
        if ccid==0:
            if utility.can_P_project_to_AB(self,nodes_centerline[0],nodes_centerline[1]) == True:
                self.projectable_centerlineedge_id = 0
                self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, nodes_centerline[0], nodes_centerline[1])
        elif ccid == len(nodes_centerline)-1:
            if utility.can_P_project_to_AB(self,nodes_centerline[-2],nodes_centerline[-1]) == True:
                self.projectable_centerlineedge_id = nodes_centerline[-2].id
                self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, nodes_centerline[-2], nodes_centerline[-1])
        else:
            distance_temp = float("inf")
            if utility.can_P_project_to_AB(self,nodes_centerline[ccid-1],nodes_centerline[ccid]) == True:
                distance_temp = utility.calculate_PH_length(self, nodes_centerline[ccid-1], nodes_centerline[ccid])
                self.projectable_centerlineedge_id = ccid-1
                self.projectable_centerlineedge_distance = distance_temp
            if utility.can_P_project_to_AB(self,nodes_centerline[ccid],nodes_centerline[ccid+1]) == True:
                if utility.calculate_PH_length(self, nodes_centerline[ccid], nodes_centerline[ccid+1]) < distance_temp:
                    self.projectable_centerlineedge_id = ccid
                    self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, nodes_centerline[ccid], nodes_centerline[ccid+1])

    # edgeradii  の総数は、centerlinenodeの数 + 1
    def set_edgeradius(self,edgeradii):
        if self.projectable_centerlineedge_id != None:
            self.edgeradius = edgeradii[self.projectable_centerlineedge_id+1]
        else:
            if self.closest_centerlinenode_id==0:
                self.edgeradius=(edgeradii[0]+edgeradii[1])/2
            elif self.closest_centerlinenode_id==config.num_of_centerlinenodes-1:
                self.edgeradius=(edgeradii[-1]+edgeradii[-2])/2
            else:
                self.edgeradius=(edgeradii[self.closest_centerlinenode_id]+edgeradii[self.closest_centerlinenode_id+1])/2
        self.scalar_forbgm = self.edgeradius*config.scaling_factor
        self.scalar_forlayer = self.edgeradius*2

class NodesAny:
    def __init__(self):
        self.nodes_any=[]
    def append(self,node_any):
        self.nodes_any.append(node_any)