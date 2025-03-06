import numpy as np

class Triangle:
    def __init__(self,id,node0,node1,node2):
        self.id=id
        self.node0=node0
        self.node1=node1
        self.node2=node2

    def calc_unitnormal(self, nodes_centerline):
        vector0=np.array([self.node1.x-self.node0.x, self.node1.y-self.node0.y, self.node1.z-self.node0.z])
        vector1=np.array([self.node2.x-self.node0.x, self.node2.y-self.node0.y, self.node2.z-self.node0.z])
        normal = np.cross(vector0,vector1)
        n0 = np.array([self.node0.x,self.node0.y,self.node0.z])
        nc = np.array([ nodes_centerline[self.node0.closest_centerlinenode_id].x,
                        nodes_centerline[self.node0.closest_centerlinenode_id].y,
                        nodes_centerline[self.node0.closest_centerlinenode_id].z ])
        vec_in = nc-n0
        if np.dot(vec_in,normal)<0:
            self.unitnormal_out = normal/np.linalg.norm(normal)
            self.unitnormal_in = -self.unitnormal_out
        else:
            self.unitnormal_in = normal/np.linalg.norm(normal)
            self.unitnormal_out = - self.unitnormal_in
    
    def calc_centroid(self):
        x = (self.node0.x + self.node1.x + self.node2.x)/3
        y = (self.node0.y + self.node1.y + self.node2.y)/3
        z = (self.node0.z + self.node1.z + self.node2.z)/3
        self.centroid=np.array([x,y,z])

    def find_closest_centerlinenode(self,nodes_centerline):
        min_distance = float("inf")
        for i in range(len(nodes_centerline)):
            centerlinenode_vec=np.array([nodes_centerline[i].x, nodes_centerline[i].y, nodes_centerline[i].z])
            distance_temp=np.linalg.norm(self.centroid - centerlinenode_vec)
            if distance_temp < min_distance:
                self.correspond_centerlinenode = nodes_centerline[i]
                min_distance = distance_temp

    def assign_correspondcenterlinenode_to_surfacenode(self):
        self.node0.correspond_centerlinenodes.append(self.correspond_centerlinenode)
        self.node1.correspond_centerlinenodes.append(self.correspond_centerlinenode)
        self.node2.correspond_centerlinenodes.append(self.correspond_centerlinenode)

class Quad:
    def __init__(self,id0,id1,id2,id3):
        self.id0=id0
        self.id1=id1
        self.id2=id2
        self.id3=id3

class Tetra:
    def __init__(self,id0,id1,id2,id3):
        self.id0=id0
        self.id1=id1
        self.id2=id2
        self.id3=id3

class Prism:
    def __init__(self,id0,id1,id2,id3,id4,id5):
        self.id0=id0
        self.id1=id1
        self.id2=id2
        self.id3=id3
        self.id4=id4
        self.id5=id5