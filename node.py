import utility
import config
import numpy as np
import sys

class NodeCenterline:
    def __init__(self,id,x,y,z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"NodeAny(id={self.id}, x={self.x}, y={self.y}, z={self.z})"
    
    def calc_tangentvec(self,nodes_centerline):
        if self.id==0:
            self.tangentvec = np.array([nodes_centerline[1].x-self.x, 
                                        nodes_centerline[1].y-self.y, 
                                        nodes_centerline[1].z-self.z])/2
        elif self.id == config.num_of_centerlinenodes-1:
            self.tangentvec = np.array([self.x-nodes_centerline[self.id-1].x, 
                                        self.y-nodes_centerline[self.id-1].y, 
                                        self.z-nodes_centerline[self.id-1].z])/2
        else:
            self.tangentvec = np.array([nodes_centerline[self.id+1].x-nodes_centerline[self.id-1].x, 
                                        nodes_centerline[self.id+1].y-nodes_centerline[self.id-1].y, 
                                        nodes_centerline[self.id+1].z-nodes_centerline[self.id-1].z])/2

    def calc_parallel_vec(self,nodes_centerline):
        self.parallel_vec  =  np.array([self.x-nodes_centerline[self.id].x,
                                        self.y-nodes_centerline[self.id].y,
                                        self.z-nodes_centerline[self.id].z])

    def calc_rotation_matrix(self,nodes_centerline):
        identity_matrix=np.array([[1,0,0],[0,1,0],[0,0,1]])
        a=nodes_centerline[self.id].tangentvec
        b=self.tangentvec
        cross_product = np.cross(a,b)
        norm = np.linalg.norm(cross_product)
        if norm!=0:
            unit_crossvec = cross_product/norm
        else:
            unit_crossvec = cross_product

        crx = float(unit_crossvec[0])
        cry = float(unit_crossvec[1])
        crz = float(unit_crossvec[2])

        matrix1=np.array([[0, -crz, cry], [crz, 0, -crx], [-cry, crx, 0]])
        matrix2=np.array([[crx**2, crx*cry, crx*crz],[crx*cry, cry**2, cry*crz], [crx*crz, cry*crz, crz**2]])

        cos_theta = np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))
        cos_theta = np.clip(cos_theta, -1.0, 1.0) # 丸め誤差で-1~1に収まらない場合を防ぐ
        theta = np.arccos(cos_theta)

        self.rotation_matrix = np.cos(theta)*identity_matrix + np.sin(theta)*matrix1 + (1-np.cos(theta))*matrix2

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
        self.right_node_id=None
        self.correspond_centerlinenodes=[]

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
                self.projectable_H_vec = utility.calculate_H(self, nodes_centerline[0], nodes_centerline[1])
        elif ccid == len(nodes_centerline)-1:
            if utility.can_P_project_to_AB(self,nodes_centerline[-2],nodes_centerline[-1]) == True:
                self.projectable_centerlineedge_id = nodes_centerline[-2].id
                self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, nodes_centerline[-2], nodes_centerline[-1])
                self.projectable_H_vec = utility.calculate_H(self, nodes_centerline[-2], nodes_centerline[-1])
        else:
            distance_temp = float("inf")
            if utility.can_P_project_to_AB(self,nodes_centerline[ccid-1],nodes_centerline[ccid]) == True:
                distance_temp = utility.calculate_PH_length(self, nodes_centerline[ccid-1], nodes_centerline[ccid])
                self.projectable_H_vec = utility.calculate_H(self, nodes_centerline[ccid-1], nodes_centerline[ccid])
                self.projectable_centerlineedge_id = ccid-1
                self.projectable_centerlineedge_distance = distance_temp
            if utility.can_P_project_to_AB(self,nodes_centerline[ccid],nodes_centerline[ccid+1]) == True:
                if utility.calculate_PH_length(self, nodes_centerline[ccid], nodes_centerline[ccid+1]) < distance_temp:
                    self.projectable_H_vec = utility.calculate_H(self, nodes_centerline[ccid], nodes_centerline[ccid+1])
                    self.projectable_centerlineedge_id = ccid
                    self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, nodes_centerline[ccid], nodes_centerline[ccid+1])

    # radius_list  の総数は、centerlinenodeの数 + 1
    def set_edgeradius(self,radius_list):
        if self.projectable_centerlineedge_id != None:
            self.edgeradius = radius_list[self.projectable_centerlineedge_id+1]
        else:
            if self.closest_centerlinenode_id==0:
                self.edgeradius=(radius_list[0]+radius_list[1])/2
            elif self.closest_centerlinenode_id==config.num_of_centerlinenodes-1:
                self.edgeradius=(radius_list[-1]+radius_list[-2])/2
            else:
                self.edgeradius=(radius_list[self.closest_centerlinenode_id]+radius_list[self.closest_centerlinenode_id+1])/2
        self.scalar_forbgm = self.edgeradius*config.SCALING_FACTOR
        self.scalar_forlayer = self.edgeradius*2

class NodeMoved(NodeAny):
    def execute_deform_radius(self,radius_list_target,nodes_centerline):
        if self.projectable_centerlineedge_id != None:
            radius_direction_vec = utility.vector(self)-self.projectable_H_vec
            radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
            coef = radius_list_target[self.projectable_centerlineedge_id+1] - self.projectable_centerlineedge_distance
            deform_vector = coef*radius_direction_unitvec
            self.x += deform_vector[0]
            self.y += deform_vector[1]
            self.z += deform_vector[2]
        else:
            if self.closest_centerlinenode_id==0:
                radius_direction_vec = utility.vector(self)-utility.calculate_H(self,nodes_centerline[0],nodes_centerline[1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = radius_list_target[0] - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]
            elif self.closest_centerlinenode_id==config.num_of_centerlinenodes-1:
                radius_direction_vec = utility.vector(self)-utility.calculate_H(self,nodes_centerline[config.num_of_centerlinenodes-2],nodes_centerline[config.num_of_centerlinenodes-1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = radius_list_target[-1] - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]
            else:
                radius_direction_vec = utility.vector(self) - utility.vector(nodes_centerline[self.closest_centerlinenode_id])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = (radius_list_target[self.closest_centerlinenode_id] + radius_list_target[self.closest_centerlinenode_id+1])/2 - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]

# gmsh.model.mesh.getNodes() の1つめの返り値は、得られた全Nodeのid のリスト。
# 2つめの返り値は、得られる全Nodeのx,y,z座標成分をまとめたリスト。これらをnodeごとの情報に整理する
def coords_to_nodes(nodeids, coords):
    if len(coords)%3!=0:
        print("mylib_info   : coords_to_nodes error.")
        sys.exit()
    else:
        nodes_any=[]
        for i in range(len(nodeids)):
            x = coords[3*i]
            y = coords[3*i+1]
            z = coords[3*i+2]
            id = nodeids[i]
            node_any = NodeAny(id,x,y,z)
            nodes_any.append(node_any)
    return nodes_any