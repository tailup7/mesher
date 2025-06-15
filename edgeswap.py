import utility
import cell
import numpy as np
import config

class PairDict:
    def __init__(self):
        self.pair_dict = {}
    def _normalize_pair(self, a, b):
        return tuple(sorted((a, b)))  
    def add_pair(self, a, b, value):
        self.pair_dict[self._normalize_pair(a, b)] = value
    def remove_pair(self, a, b):
        key = self._normalize_pair(a, b)
        if key in self.pair_dict:
            del self.pair_dict[key]
    def get_value(self, a, b):
        return self.pair_dict.get(self._normalize_pair(a, b))
    
def edgeswap(surfacetriangles,surfacetriangle_dict, nodes_moved_dict):
    config.edgeswap_count_pre = config.edgeswap_count

    for surfacetriangle in surfacetriangles:
        surfacetriangle.already_swaped = False

    surfacetriangles_swaped = []
    pair_dict = PairDict()              
    for surfacetriangle in surfacetriangles:
        node0 = nodes_moved_dict[surfacetriangle.node0.id]
        node1 = nodes_moved_dict[surfacetriangle.node1.id]
        node2 = nodes_moved_dict[surfacetriangle.node2.id]
        # node0 とnode1 に対して
        if pair_dict.get_value(node0.id, node1.id) == None:
            pair_dict.add_pair(node0.id, node1.id, surfacetriangle.id)
        else:
            pair_triangle = surfacetriangle_dict[pair_dict.get_value(node0.id,node1.id)]  
            if pair_triangle.already_swaped == False and surfacetriangle.already_swaped == False:
                pair_triangle_nodeids =  {pair_triangle.node0.id, pair_triangle.node1.id, pair_triangle.node2.id}
                pair_triangle_vertexid = next(iter(pair_triangle_nodeids - {node0.id, node1.id}))
                if utility.can_P_project_to_AB(node2, node0, node1) and utility.can_P_project_to_AB(nodes_moved_dict[pair_triangle_vertexid], node0, node1):
                    this_triangle_quality  = cell.calc_cell_quality(node0, node1, node2)
                    pair_triangle_quality  = cell.calc_cell_quality(node0, node1,nodes_moved_dict[pair_triangle_vertexid])
                    temp_triangle1_quality = cell.calc_cell_quality(node1, node2,nodes_moved_dict[pair_triangle_vertexid])
                    temp_triangle2_quality = cell.calc_cell_quality(node0, node2,nodes_moved_dict[pair_triangle_vertexid])
                    if ( min(this_triangle_quality, pair_triangle_quality) >= min(temp_triangle1_quality, temp_triangle2_quality) and 
                            max(this_triangle_quality, pair_triangle_quality) >= max(temp_triangle1_quality, temp_triangle2_quality) ):
                        # this_triangleの各nodeを再定義
                        surfacetriangle.node0 = node1
                        surfacetriangle.node1 = node2
                        surfacetriangle.node2 = nodes_moved_dict[pair_triangle_vertexid]
                        # pair_triangleの各nodeを再定義
                        surfacetriangle_dict[pair_dict.get_value(node0.id,node1.id)].node0 = node0
                        surfacetriangle_dict[pair_dict.get_value(node0.id,node1.id)].node1 = nodes_moved_dict[pair_triangle_vertexid]
                        surfacetriangle_dict[pair_dict.get_value(node0.id,node1.id)].node2 = node2
                        # swap後、法線ベクトルの再計算
                        surfacetriangle.calc_unitnormal() 
                        surfacetriangle_dict[pair_dict.get_value(node0.id,node1.id)].calc_unitnormal()
                        # swap後、this triangleとpair triangle を swap済みにする
                        surfacetriangle.already_swaped = True
                        surfacetriangle_dict[pair_dict.get_value(node0.id,node1.id)].already_swaped = True
                        config.edgeswap_count+=1
                        print(f"do edgeswap at triangle {surfacetriangle.id}")

        # node1 とnode2 に対して 
        if pair_dict.get_value(node1.id, node2.id) == None:
            pair_dict.add_pair(node1.id, node2.id, surfacetriangle.id)
        else:
            pair_triangle = surfacetriangle_dict[pair_dict.get_value(node1.id,node2.id)]  
            if pair_triangle.already_swaped == False and surfacetriangle.already_swaped == False:
                pair_triangle_nodeids =  {pair_triangle.node0.id, pair_triangle.node1.id, pair_triangle.node2.id}
                pair_triangle_vertexid = next(iter(pair_triangle_nodeids-{node1.id, node2.id}))
                if utility.can_P_project_to_AB(node0,node1,node2) and utility.can_P_project_to_AB(nodes_moved_dict[pair_triangle_vertexid],node1,node2):
                    this_triangle_quality  = cell.calc_cell_quality(node0,node1,node2) ###
                    pair_triangle_quality  = cell.calc_cell_quality(node1,node2,nodes_moved_dict[pair_triangle_vertexid])
                    temp_triangle1_quality = cell.calc_cell_quality(node0,node1,nodes_moved_dict[pair_triangle_vertexid])
                    temp_triangle2_quality = cell.calc_cell_quality(node0,node2,nodes_moved_dict[pair_triangle_vertexid])
                    if ( min(this_triangle_quality, pair_triangle_quality) >= min(temp_triangle1_quality, temp_triangle2_quality) and 
                            max(this_triangle_quality, pair_triangle_quality) >= max(temp_triangle1_quality, temp_triangle2_quality) ):
                        # this_triangleの各nodeを再定義
                        surfacetriangle.node1 = nodes_moved_dict[pair_triangle_vertexid]
                        # pair_triangleの各nodeを再定義
                        surfacetriangle_dict[pair_dict.get_value(node1.id,node2.id)].node0 = node0
                        surfacetriangle_dict[pair_dict.get_value(node1.id,node2.id)].node1 = node1
                        surfacetriangle_dict[pair_dict.get_value(node1.id,node2.id)].node2 = nodes_moved_dict[pair_triangle_vertexid]
                        # swap後、法線ベクトルの再計算
                        surfacetriangle.calc_unitnormal()
                        surfacetriangle_dict[pair_dict.get_value(node1.id,node2.id)].calc_unitnormal()
                        # swap後、this triangleとpair triangle を swap済みにする
                        surfacetriangle.already_swaped = True
                        surfacetriangle_dict[pair_dict.get_value(node1.id,node2.id)].already_swaped = True
                        config.edgeswap_count+=1
                        print(f"do edgeswap at triangle {surfacetriangle.id}")

        # node2 とnode0 に対して 
        if pair_dict.get_value(node2.id, node0.id) == None:
            pair_dict.add_pair(node2.id, node0.id, surfacetriangle.id)
        else:
            pair_triangle = surfacetriangle_dict[pair_dict.get_value(node2.id,node0.id)]
            if pair_triangle.already_swaped == False and surfacetriangle.already_swaped == False:  
                pair_triangle_nodeids =  {pair_triangle.node0.id, pair_triangle.node1.id, pair_triangle.node2.id}
                pair_triangle_vertexid = next(iter(pair_triangle_nodeids-{node2.id, node0.id}))
                if utility.can_P_project_to_AB(node1,node2,node0) and utility.can_P_project_to_AB(nodes_moved_dict[pair_triangle_vertexid],node2,node0):
                    this_triangle_quality  = cell.calc_cell_quality(node0,node1,node2)
                    pair_triangle_quality  = cell.calc_cell_quality(node0,node2,nodes_moved_dict[pair_triangle_vertexid])
                    temp_triangle1_quality = cell.calc_cell_quality(node0,node1,nodes_moved_dict[pair_triangle_vertexid])
                    temp_triangle2_quality = cell.calc_cell_quality(node1,node2,nodes_moved_dict[pair_triangle_vertexid])
                    if ( min(this_triangle_quality, pair_triangle_quality) >= min(temp_triangle1_quality, temp_triangle2_quality) and 
                            max(this_triangle_quality, pair_triangle_quality) >= max(temp_triangle1_quality, temp_triangle2_quality) ):
                        # this_triangleの各nodeを再定義
                        surfacetriangle.node2 = nodes_moved_dict[pair_triangle_vertexid]
                        # pair_triangleの各nodeを再定義
                        surfacetriangle_dict[pair_dict.get_value(node2.id,node0.id)].node0 = nodes_moved_dict[pair_triangle_vertexid]
                        surfacetriangle_dict[pair_dict.get_value(node2.id,node0.id)].node1 = node1
                        surfacetriangle_dict[pair_dict.get_value(node2.id,node0.id)].node2 = node2
                        # swap後、法線ベクトルの再計算
                        surfacetriangle.calc_unitnormal()
                        surfacetriangle_dict[pair_dict.get_value(node2.id,node0.id)].calc_unitnormal()
                        # swap後、this triangleとpair triangle を swap済みにする
                        surfacetriangle.already_swaped = True
                        surfacetriangle_dict[pair_dict.get_value(node2.id,node0.id)].already_swaped = True
                        config.edgeswap_count+=1
                        print(f"do edgeswap at triangle {surfacetriangle.id}")
        surfacetriangles_swaped.append(surfacetriangle)
    return surfacetriangles_swaped