import numpy as np
from scipy.spatial import KDTree
from sklearn.decomposition import PCA

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

def find_right_neighbors_3d(points, reference_point):
    """
    点群を主成分分析（PCA）で最適な平面に投影し、
    reference_point から見て右回りの順番を決定する。
    
    :param points: Pointインスタンスのリスト
    :param reference_point: (x, y, z) の基準点
    :return: (ソートされた点のリスト, 右隣の点のリスト)
    """
    # 1. 点群を NumPy 配列に変換
    point_matrix = np.array([[p.x, p.y, p.z] for p in points])

    # 2. PCA を実行し、主成分平面を取得
    pca = PCA(n_components=2)
    projected_2d = pca.fit_transform(point_matrix)  # 3D点群を2D空間に投影

    # 3. 基準点も同じ平面に投影する
    ref_matrix = np.array([reference_point])
    projected_ref = pca.transform(ref_matrix)[0]  # (x', y')

    # 4. 基準点からの角度を計算
    centroid_x, centroid_y = projected_ref  # 基準点の投影座標
    angles = np.arctan2(projected_2d[:,1] - centroid_y, projected_2d[:,0] - centroid_x)

    # 5. 角度で **右回り** にソート（通常は左回りなので符号を反転）
    sorted_indices = np.argsort(-angles)  # 角度のソート方向を逆にする
    sorted_points = [points[i] for i in sorted_indices]

    # 6. 右隣の点を対応付け（ソート順で一つ次の点を右隣とする）
    right_neighbors = np.roll(sorted_points, shift=-1).tolist()

    return sorted_points, right_neighbors

#Pointはid,x,y,zをインスタンス変数に持つインスタンス
#points = [
#    Point(0, 1.0, 2.0, 3.0),
#    Point(1, 4.0, 5.0, 6.0),
#    Point(2, 7.0, 8.0, 9.0),
#    Point(3, 10.0, 11.0, 12.0)
#]
#だとして、右回りに並べ替えた結果が1つめの返り値
#sorted_points = [
#    Point(2, 7.0, 8.0, 9.0),
#    Point(0, 1.0, 2.0, 3.0),
#    Point(3, 10.0, 11.0, 12.0),
#    Point(1, 4.0, 5.0, 6.0)
#]
# 各点の右隣の点を表すのが、2つめの返値
#right_neighbors = [
#    Point(0, 1.0, 2.0, 3.0),  # Point(2) の右隣
#    Point(3, 10.0, 11.0, 12.0), # Point(0) の右隣
#    Point(1, 4.0, 5.0, 6.0),  # Point(3) の右隣
#    Point(2, 7.0, 8.0, 9.0)   # Point(1) の右隣 (ループ)
#]