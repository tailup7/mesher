# 1から見て、2との表面間距離
import os
import numpy as np
import myio
import utility

if __name__=="__main__":
    filepath1 = myio.select_vtk()
    filepath2 = myio.select_vtk()
    surfacenodes1,surfacenode_dict1,surfacetriangles1,surfacetriangle_dict1 = myio.read_vtk_for_hausdorff(filepath1)
    surfacenodes2,surfacenode_dict2,surfacetriangles2,surfacetriangle_dict2 = myio.read_vtk_for_hausdorff(filepath2)
    haus=[]
    for i in range(len(surfacenodes1)):
        min_distance=float("inf")
        for j in range(len(surfacenodes2)):
            tmp = np.linalg.norm(utility.vector(surfacenodes1[i])-utility.vector(surfacenodes2[j]))
            if tmp < min_distance:
                min_distance = tmp
                surfacenodes1[i].closest_surfacenode_id = j+1

        min_distance_to_triangle=float("inf")
        for j in range(len(surfacenodes2[surfacenodes1[i].closest_surfacenode_id-1].related_triangle_ids)):
            A = surfacenode_dict2[surfacetriangle_dict2[surfacenodes2[surfacenodes1[i].closest_surfacenode_id-1].related_triangle_ids[j]].node0.id]
            B = surfacenode_dict2[surfacetriangle_dict2[surfacenodes2[surfacenodes1[i].closest_surfacenode_id-1].related_triangle_ids[j]].node1.id]
            C = surfacenode_dict2[surfacetriangle_dict2[surfacenodes2[surfacenodes1[i].closest_surfacenode_id-1].related_triangle_ids[j]].node2.id]
            tmp = utility.calc_point_to_triangle_distance(surfacenodes1[i], A,B,C)
            if tmp < min_distance_to_triangle:
                min_distance_to_triangle = tmp
        haus.append(min_distance_to_triangle)
    myio.write_vtk_hausdorff(surfacenodes1,haus)

    haus_min=float("inf")
    haus_max=0.0
    haus_ave=0.0
    countor=0
    for i in range(len(haus)):
        if haus[i] < haus_min:
            haus_min = haus[i]
        if haus[i] > haus_max:
            haus_max=haus[i]
        haus_ave+=haus[i]
        countor+=1
    haus_ave/=countor        

    filepath_haus = os.path.join("output", "hausdorff.txt")
    memo=f"""max_hausdorff_distance  : {haus_max} 
min_hausdorff_distance  : {haus_min}
ave_hausdorff_distance  : {haus_ave}"""
    with open(filepath_haus, "w") as f:
        f.write(memo)
