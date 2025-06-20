import config
import numpy as np
from scipy.spatial import KDTree

def can_P_project_to_AB(P,A,B):

#             projectable                        Not projectable
#
#                  P                                                     P
#                  |                                                     |
#                  |                                                     |
#                  |                                                     |  
#      A---------- H -----B                A------------------B          H
#       \     t    /                         \                          /
#                                                          t
    vector_AP = np.array([P.x-A.x,  P.y-A.y,  P.z-A.z])
    vector_AB = np.array([B.x-A.x,  B.y-A.y,  B.z-A.z])
    vector_AB_square = np.dot(vector_AB, vector_AB)
    t = np.dot(vector_AP,vector_AB) / vector_AB_square
    if 0 <= t and t <= 1:
        return True

def calculate_PH_length(P,A,B):
    vector_AP = np.array([P.x-A.x,  P.y-A.y,  P.z-A.z])
    vector_AB = np.array([B.x-A.x,  B.y-A.y,  B.z-A.z])
    vector_AB_square = np.dot(vector_AB, vector_AB)
    t = np.dot(vector_AP,vector_AB) / vector_AB_square
    vector_AH = t*vector_AB
    vector_PH = vector_AH - vector_AP
    return(np.linalg.norm(vector_PH))

def calculate_H(P,A,B):
    vector_AP = np.array([P.x-A.x,  P.y-A.y,  P.z-A.z])
    vector_AB = np.array([B.x-A.x,  B.y-A.y,  B.z-A.z])
    vector_AB_square = np.dot(vector_AB, vector_AB)
    t = np.dot(vector_AP,vector_AB) / vector_AB_square
    vector_AH = t*vector_AB
    vector_H = np.array([A.x,A.y,A.z]) + vector_AH
    return vector_H

def calculate_centroid(points):
    x_sum=0
    y_sum=0
    z_sum=0
    for i in range(len(points)):
        x_sum += points[i].x
        y_sum += points[i].y
        z_sum += points[i].z
    x=x_sum/len(points)
    y=y_sum/len(points)
    z=z_sum/len(points)
    return np.array([x,y,z])

# kdtree
# 返り値は 
#  list[tuple[instance_A, instance_B, distance(float)]]
def find_nearest_neighbors(instance_list_A,instance_list_B):
    points_A_np = np.array([[p.x, p.y, p.z] for p in instance_list_A])
    points_B_np = np.array([[p.x, p.y, p.z] for p in instance_list_B])

    kdtree = KDTree(points_B_np)
    distances, indices = kdtree.query(points_A_np)
    nearest_pairs = [(instance_list_A[i], instance_list_B[indices[i]], distances[i]) for i in range(len(instance_list_A))]
    return nearest_pairs

def vector(point):
    return np.array([point.x,point.y,point.z])

def find_right_neighbors(points,innerpoint_vec):
    centroid=calculate_centroid(points)
    point_temp=points[0]
    point_temp_next = None
    min_distance=float("inf")
    while point_temp.right_node_id==None:
        for point in points:
            if point_temp.id!=point.id:
                if np.dot(np.cross(vector(point_temp)-centroid,vector(point)-centroid),centroid-innerpoint_vec) >0:
                    distance = np.linalg.norm(vector(point)-vector(point_temp))
                    if distance < min_distance:
                        min_distance = distance
                        point_temp.right_node_id = point.id
                        point_temp_next = point
        point_temp=point_temp_next
        min_distance=float("inf")

def calc_point_to_triangle_distance(P, A, B, C):
    """
    点 P と三角形 ABC の最短距離を計算
    """
    # 辺ベクトル
    AB = vector(B) - vector(A)
    AC = vector(C) - vector(A)
    AP = vector(P) - vector(A)

    # 各種スカラー積
    d1 = np.dot(AB, AP)
    d2 = np.dot(AC, AP)
    d3 = np.dot(AB, AB)
    d4 = np.dot(AB, AC)
    d5 = np.dot(AC, AC)

    denom = d3 * d5 - d4 * d4

    # 重心座標(u,v)を計算
    if denom == 0:
        return np.linalg.norm(AP)  # 三角形が退化してる（点）
    
    v = (d5 * d1 - d4 * d2) / denom
    w = (d3 * d2 - d4 * d1) / denom
    u = 1 - v - w

    # 三角形内部にあるか？
    if u >= 0 and v >= 0 and w >= 0:
        # 三角形の面への垂直距離
        N = np.cross(AB, AC)
        N = N / np.linalg.norm(N)
        dist = abs(np.dot(AP, N))
    else:
        # 外側 → 各辺との距離 or 頂点との距離の最小値
        def segment_distance(P, Q, R):
            t = np.dot(vector(P) - vector(Q), vector(R) - vector(Q)) / np.dot(vector(R) - vector(Q), vector(R) - vector(Q))
            t = np.clip(t, 0, 1)
            projection = vector(Q) + t * (vector(R) - vector(Q))
            return np.linalg.norm(vector(P) - projection)

        dist = min(
            segment_distance(P, A, B),
            segment_distance(P, B, C),
            segment_distance(P, C, A)
        )
    return dist

def calculate_nth_layer_thickratio(n):
    thickratio_each_layer=[None]*config.NUM_OF_LAYERS
    thickratio_each_layer[0]=config.FIRST_LAYER_RATIO
    total_thickratio = 0
    for i in range(1,n):
        thickratio_each_layer[i] = thickratio_each_layer[i-1]*config.GROWTH_RATE
    for i in range(n):
        total_thickratio += thickratio_each_layer[i]
    return total_thickratio

# vmtk等で抽出した中心線は摂動を含むので、隣接7点の移動平均で平滑化する
def moving_average_for_tangentvec(nodes_centerline):
    tangentvec_smoothed_list = [0]*config.num_of_centerlinenodes
    tangentvec_smoothed_list[0] = sum(node.tangentvec for node in nodes_centerline[:4]) / 4
    tangentvec_smoothed_list[1] = sum(node.tangentvec for node in nodes_centerline[:5]) / 5
    tangentvec_smoothed_list[2] = sum(node.tangentvec for node in nodes_centerline[:6]) / 6
    tangentvec_smoothed_list[-1] = sum(node.tangentvec for node in nodes_centerline[-4:]) / 4
    tangentvec_smoothed_list[-2] = sum(node.tangentvec for node in nodes_centerline[-5:]) / 5
    tangentvec_smoothed_list[-3] = sum(node.tangentvec for node in nodes_centerline[-6:]) / 6
    for i in range(3,config.num_of_centerlinenodes-3):
        tangentvec_smoothed_list[i] = sum(node.tangentvec for node in nodes_centerline[i-3:i+4]) / 7
    for i in range(config.num_of_centerlinenodes):
        nodes_centerline[i].tangentvec = tangentvec_smoothed_list[i]

# vmtk等で抽出した中心線は摂動を含むので、隣接11点(左側5点+自分自身+右側5点)の移動平均で平滑化する
def moving_average_for_tangentvec_ver2(nodes_centerline):
    tangentvec_smoothed_list = [0]*config.num_of_centerlinenodes
    tangentvec_smoothed_list[0] = sum(node.tangentvec for node in nodes_centerline[:6]) / 6
    tangentvec_smoothed_list[1] = sum(node.tangentvec for node in nodes_centerline[:7]) / 7
    tangentvec_smoothed_list[2] = sum(node.tangentvec for node in nodes_centerline[:8]) / 8
    tangentvec_smoothed_list[3] = sum(node.tangentvec for node in nodes_centerline[:9]) / 9
    tangentvec_smoothed_list[4] = sum(node.tangentvec for node in nodes_centerline[:10]) / 10
    tangentvec_smoothed_list[-1] = sum(node.tangentvec for node in nodes_centerline[-6:]) / 6
    tangentvec_smoothed_list[-2] = sum(node.tangentvec for node in nodes_centerline[-7:]) / 7
    tangentvec_smoothed_list[-3] = sum(node.tangentvec for node in nodes_centerline[-8:]) / 8
    tangentvec_smoothed_list[-4] = sum(node.tangentvec for node in nodes_centerline[-9:]) / 9
    tangentvec_smoothed_list[-5] = sum(node.tangentvec for node in nodes_centerline[-10:]) / 10
    for i in range(5,config.num_of_centerlinenodes-5):
        tangentvec_smoothed_list[i] = sum(node.tangentvec for node in nodes_centerline[i-5:i+6]) / 11
    for i in range(config.num_of_centerlinenodes):
        nodes_centerline[i].tangentvec = tangentvec_smoothed_list[i]
