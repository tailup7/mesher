import node
import cell
import config
import utility
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from numpy.polynomial.polynomial import Polynomial
import tkinter as tk
from tkinter import filedialog

def select_csv(message):
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename(
        title=f"Select {message} centerline file (*.csv)",
        filetypes=[("CSV files", "*.csv")]  
    )
    return file_path

def select_stl():
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename(
        title="Select surface file",
        filetypes=[("stl files", "*.stl")]  
    )
    return file_path

def write_txt_parameter():
    if not os.path.exists("output"):
        os.makedirs("output")
    filepath = os.path.join("output", "memo.txt")
    memo=f"""num of centerlinenodes  : {config.num_of_centerlinenodes} 
MESHSIZE                : {config.MESHSIZE}
MESHSIZE_SCALING_FACTOR : {config.SCALING_FACTOR}
FIRST_LAYER_RATIO       : {config.FIRST_LAYER_RATIO}
GROWTH_RATE             : {config.GROWTH_RATE}
NUM_OF_LAYERS           : {config.NUM_OF_LAYERS}"""
    with open(filepath, "w") as f:
        f.write(memo)
    
# todo: original と targetで中心線の点数が違う時にerror出すように
def read_csv_centerline(filepath):
    df = pd.read_csv(filepath)
    nodes_centerline = [node.NodeCenterline(index, row['x'], row['y'], row['z']) for index, row in df.iterrows()]
    config.inlet_point = nodes_centerline[0]
    config.outlet_point = nodes_centerline[-1]
    config.num_of_centerlinenodes = len(nodes_centerline)

    # radius_listの総数を、【点群の数+1】 にする
    if "radius" in df.columns:
        radius_list = df["radius"].tolist()
        last_x = np.array([len(radius_list)-3, len(radius_list)-2, len(radius_list)-1])
        last_y = radius_list[-3:]
        polynominal_func = Polynomial.fit(last_x, last_y, 1)
        additional_radius = polynominal_func(len(radius_list))
        radius_list.append(additional_radius)
        config.inlet_radius = radius_list[0]
        config.outlet_radius = radius_list[-1]
    else:
        radius_list = None
    return nodes_centerline, radius_list

def add_radiusinfo_to_centerlinefile(filepath_centerline, radius_list):
    radius_list.pop()
    df=pd.read_csv(filepath_centerline)
    df["radius"] = radius_list
    df.to_csv(filepath_centerline, index=False)

def read_msh_tetra(filepath):
    tetra_list = []
    with open(filepath, 'r') as file:
        lines = file.readlines()
        for line in lines:
            columns = line.split()
            if len(columns) == 9 and columns[1] == '4':
                tetra = [int(columns[i]) for i in range(5, 9)]
                tetra_list.append(tetra)
    print("info_myio    : num of tetra is",len(tetra_list))
    return tetra_list

def write_pos_bgm(tetra_list,nodeany_dict,filename):
    filepath = os.path.join("output", f"bgm_{filename}.pos")
    with open(filepath, 'w') as f:
        f.write('View "background mesh" {\n')
        coords_list=[]
        scalars_list=[]
        for tetra in tetra_list:
            coords=[]
            scalars=[]
            for i in range(len(tetra)):
                coords.append(nodeany_dict[tetra[i]].x)
                coords.append(nodeany_dict[tetra[i]].y)
                coords.append(nodeany_dict[tetra[i]].z)
                scalars.append(nodeany_dict[tetra[i]].scalar_forbgm)
            coords_list.append(coords)
            scalars_list.append(scalars)
        for i in range(len(tetra_list)):
            c = coords_list[i]
            s = scalars_list[i]
            f.write(f"SS({c[0]},{c[1]},{c[2]},{c[3]},{c[4]},{c[5]},{c[6]},{c[7]},{c[8]},{c[9]},{c[10]},{c[11]})"
                    f"{{{s[0]:.2f},{s[1]:.2f},{s[2]:.2f},{s[3]:.2f}}};\n")
        f.write('};')
    print(f"output bgm_{filename}.pos")
    return filepath

def read_vtk_surfacemesh(filepath_vtk):
    with open(filepath_vtk, 'r') as file:
        lines = file.readlines()
    points_section = False
    cells_section = False

    for line in lines:
        line = line.strip()
        if line.startswith("POINTS"):
            points_section = True
            node_id=1
            surfacenode_dict = {}
            surfacenodes = []
            continue
        if line.startswith("CELLS"):
            points_section = False
            cells_section = True
            triangle_id=1   
            surfacetriangles = []
            continue

        if points_section:
            if not line: # 「行が空なら」
                points_section = False
                continue
            coords = list(map(float, line.split()))
            x=coords[0]
            y=coords[1]
            z=coords[2]
            surfacenode=node.NodeAny(node_id,x,y,z)
            surfacenode_dict[node_id]= surfacenode
            surfacenodes.append(surfacenode)
            node_id+=1
        if cells_section:
            if not line: # 「行が空なら」
                cells_section = False
                continue
            cell_data = list(map(int, line.split()))
            if cell_data[0] == 3:
                node0 = surfacenode_dict[cell_data[1]+1]
                node1 = surfacenode_dict[cell_data[2]+1]
                node2 = surfacenode_dict[cell_data[3]+1]
                surfacetriangle = cell.Triangle(triangle_id, node0, node1, node2)
                surfacetriangles.append(surfacetriangle)
                triangle_id += 1
    print("info_myio    : num of outersurface points is ",node_id-1)
    print("info_myio    : num of outersurface triangles is ",triangle_id-1)
    config.num_of_surfacenodes=node_id-1
    config.num_of_surfacetriangles = triangle_id-1
    
    return surfacenodes,surfacetriangles

def add_scalarinfo_to_surfacemesh_original_vtkfile(filepath_vtk,surfacetriangles):
    with open(filepath_vtk, "r") as f:
        lines = f.readlines()

    cell_types_section = False
    cell_types_list = []
    insert_index = None

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("CELL_TYPES"):
            cell_types_section = True
            num_cell_types = int(line.split()[1])
            continue

        if cell_types_section:
            if not line:
                cell_types_section = False
                insert_index = i  
                continue
            try:
                val = int(line)
                cell_types_list.append(val)
            except ValueError:
                continue

    if insert_index is None:
        insert_index = len(lines)
    scalar_values = []
    i_list = 0
    for ct in cell_types_list:
        if ct == 5:
            scalar_values.append(surfacetriangles[i_list].correspond_centerlinenode.id)
            i_list += 1
        else:
            scalar_values.append(0.0)

    # CELL_DATA セクションの生成
    cell_data_block = [
        f"\nCELL_DATA {len(cell_types_list)}\n",
        f"SCALARS ccnID float 1\n",
        "LOOKUP_TABLE default\n"
    ] + [f"{val}\n" for val in scalar_values]

    output_path = os.path.join("output", "surfacemesh_original_with_ccnID.vtk")
    new_lines = lines[:insert_index] + cell_data_block + lines[insert_index:]
    with open(output_path, "w") as f:
        f.writelines(new_lines)

def write_stl_innersurface(mesh,nodes_centerline,layernode_dict):
    filename = "innersurface_" + str(config.NUM_OF_LAYERS) + ".stl"
    filepath=os.path.join("output",filename)
    start = config.num_of_surfacetriangles*(config.NUM_OF_LAYERS-1)
    end = config.num_of_surfacetriangles*config.NUM_OF_LAYERS-1
    triangle_list=[]
    for i in range(start,end+1):
        id0 = mesh.prisms_INTERNAL[i].id0
        id1 = mesh.prisms_INTERNAL[i].id1
        id2 = mesh.prisms_INTERNAL[i].id2
        node0 = layernode_dict[id0]
        node1 = layernode_dict[id1]
        node2 = layernode_dict[id2]
        triangle = cell.Triangle(i, node0, node1, node2)
        triangle.calc_unitnormal(nodes_centerline)
        triangle_list.append(triangle)
    with open(filepath, 'w') as f:
        f.write("solid model\n")
        for triangle in triangle_list:
            f.write(f"  facet normal {triangle.unitnormal_out[0]} {triangle.unitnormal_out[1]} {triangle.unitnormal_out[2]}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {triangle.node0.x} {triangle.node0.y} {triangle.node0.z}\n")
            f.write(f"      vertex {triangle.node1.x} {triangle.node1.y} {triangle.node1.z}\n")
            f.write(f"      vertex {triangle.node2.x} {triangle.node2.y} {triangle.node2.z}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid model\n")
    return filepath

def write_stl_surfacetriangles(surfacetriangles,filename):
    path = Path(__file__).resolve().parent
    filepath = path / "output" / filename
    filepath = filepath.as_posix()
    with open(filepath, 'w') as f:
        f.write("solid model\n")
        for triangle in surfacetriangles:
            f.write(f"  facet normal {triangle.unitnormal_out[0]} {triangle.unitnormal_out[1]} {triangle.unitnormal_out[2]}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {triangle.node0.x} {triangle.node0.y} {triangle.node0.z}\n")
            f.write(f"      vertex {triangle.node1.x} {triangle.node1.y} {triangle.node1.z}\n")
            f.write(f"      vertex {triangle.node2.x} {triangle.node2.y} {triangle.node2.z}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid model\n")
    return filepath

def write_vtk_surfacemesh_with_ccnID(surfacenodes,surfacetriangles):
    filepath=os.path.join("output","surfacemesh_deformed_with_ccnID.vtk")
    point_header=f"""# vtk DataFile Version 2.0
WALL_0, Created by Gmsh 4.11.1 
ASCII
DATASET UNSTRUCTURED_GRID
POINTS {len(surfacenodes)} double\n"""
    cell_header=f"""CELLS {len(surfacetriangles)} {4*len(surfacetriangles)}\n"""
    celltypes_header = f"""CELL_TYPES {len(surfacetriangles)}\n"""
    celldata_header=f"""CELL_DATA {len(surfacetriangles)}
SCALARS ccnID float 1
LOOKUP_TABLE default\n"""
    
    with open(filepath, "w") as f:
        f.write(point_header)
        for pt in surfacenodes:
            f.write(f"{pt.x} {pt.y} {pt.z}\n")
        f.write(cell_header)
        for tri in surfacetriangles:
            f.write(f"3 {tri.node0.id-1} {tri.node1.id-1} {tri.node2.id-1}\n")
        f.write(celltypes_header)
        for tri in surfacetriangles:
            f.write("5\n")
        f.write(celldata_header)
        for tri in surfacetriangles:
            f.write(f"{tri.correspond_centerlinenode.id-1}\n")

def read_msh_innermesh(filepath,mesh):
    node_innermesh_dict={}
    nodesid_composing_innerwalltriangle=set()
    nodesid_composing_inlettriangle=set()
    nodesid_composing_outlettriangle=set()
    triangle_inlet_list=[]
    triangle_outlet_list=[]
    tetra_list=[]

    with open(filepath, "r") as file:
        lines = file.readlines()

    node_section = False
    skip_next_line_n = False
    skip_next_line_e=False
    element_section = False

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("$Nodes"):
            node_section = True
            skip_next_line_n = True 
            continue

        if skip_next_line_n:
            skip_next_line_n = False  
            num_of_innermeshnodes=int(line)
            continue

        if line.startswith("$EndNodes"):
            node_section = False
            continue

        if node_section:
            parts = line.split()
            if len(parts) < 4:
                continue  
            
            node_id = int(parts[0])
            x, y, z = map(float, parts[1:4])
            node_innermesh = node.NodeAny(node_id, x, y, z) 
            node_innermesh_dict[node_id]=node_innermesh

        if line.startswith("$Elements"):
            element_section = True
            skip_next_line_e = True  
            continue
        if skip_next_line_e:
            skip_next_line_e = False
            continue
        if line.startswith("$EndElements"):
            element_section = False
            continue

        if element_section:
            parts = line.split()
            if len(parts) < 5:
                continue 

            elem_id = int(parts[0])  # 要素ID
            elem_type = int(parts[1])  # 要素のタイプ
            physical_group = int(parts[3])  # physical number（4列目）

            if  elem_type == 2: 
                node0 = node_innermesh_dict[int(parts[-3])]
                node1 = node_innermesh_dict[int(parts[-2])]
                node2 = node_innermesh_dict[int(parts[-1])]

                if physical_group == 99 :
                    nodesid_composing_innerwalltriangle.update(map(int, parts[-3:])) #除外にもこれを使える

                elif physical_group == 20:
                    triangle_inlet = cell.Triangle(elem_id, node0, node1, node2)
                    nodesid_composing_inlettriangle.update(map(int, parts[-3:])) 
                    triangle_inlet_list.append(triangle_inlet)

                elif physical_group == 30:
                    triangle_outlet = cell.Triangle(elem_id, node0, node1, node2)
                    nodesid_composing_outlettriangle.update(map(int, parts[-3:]))
                    triangle_outlet_list.append(triangle_outlet)

            if  elem_type == 4: 
                id0 = int(parts[-4])
                id1 = int(parts[-3])
                id2 = int(parts[-2])
                id3 = int(parts[-1])
                tetra = cell.Tetra(id0,id1,id2,id3)
                tetra_list.append(tetra)

# 既存の最深層とinnerwalltriangleを重ね合わせ、辞書を作る
    nodes_mostinner=[]
    start = config.num_of_surfacenodes*config.NUM_OF_LAYERS
    end = config.num_of_surfacenodes*(config.NUM_OF_LAYERS+1)-1
    for i in range(start,end+1):
        nodes_mostinner.append(mesh.nodes[i])
    nodes_innerwalltriangle=[]
    for nodeid in nodesid_composing_innerwalltriangle:
        nodes_innerwalltriangle.append(node_innermesh_dict[nodeid])
    nearestpairs = utility.find_nearest_neighbors(nodes_innerwalltriangle,nodes_mostinner)
    nodes_innerwall_dict={}
    cumulative_error=0
    for i in range(len(nearestpairs)):
        nodes_innerwall_dict[nearestpairs[i][0].id] = nearestpairs[i][1]
        cumulative_error+=nearestpairs[i][2]
    print("cumulative error is",cumulative_error)

    # 99(innerwall)と20or30(端面)を構成するNodeはboundaryNodeとして抽出する
    nodesid_on_inlet_boundaryedge = nodesid_composing_innerwalltriangle & nodesid_composing_inlettriangle
    nodesid_on_outlet_boundaryedge= nodesid_composing_innerwalltriangle & nodesid_composing_outlettriangle
    print("num of nodesid_composing_innerwalltriangle is ",len(nodesid_composing_innerwalltriangle))
    print("num of nodesid_on_inlet_boundaryedge is ",len(nodesid_on_inlet_boundaryedge))
    for nodeid in nodesid_on_inlet_boundaryedge:
        nodes_innerwall_dict[nodeid].on_inlet_boundaryedge = True
    for nodeid in nodesid_on_outlet_boundaryedge:
        nodes_innerwall_dict[nodeid].on_outlet_boundaryedge = True
    #config.num_of_innermeshnodes = mesh.num_of_nodes

    # node id を書き換え,mesh info に追加
    node_countor=1
    for i in range(1,num_of_innermeshnodes+1):
        if i in nodesid_composing_innerwalltriangle:
            node_innermesh_dict[i].id = nodes_innerwall_dict[i].id
            continue
        node_innermesh_dict[i].id = node_countor+config.num_of_boundarylayernodes
        mesh.nodes.append(node_innermesh_dict[i])
        mesh.num_of_nodes += 1
        node_countor += 1

    # element情報をmesh infoに追加
    for triangle in triangle_inlet_list:
        triangle.id = mesh.num_of_elements + 1
        mesh.triangles_INLET.append(triangle)
        mesh.num_of_elements+=1
    for triangle in triangle_outlet_list:
        triangle.id = mesh.num_of_elements + 1
        mesh.triangles_OUTLET.append(triangle)
        mesh.num_of_elements+=1
    for tetra in tetra_list:
        tetra.id0=node_innermesh_dict[tetra.id0].id
        tetra.id1=node_innermesh_dict[tetra.id1].id
        tetra.id2=node_innermesh_dict[tetra.id2].id
        tetra.id3=node_innermesh_dict[tetra.id3].id
        mesh.tetras_INTERNAL.append(tetra)
        mesh.num_of_elements+=1

    return  mesh 

def write_msh_allmesh(mesh,filename):
    filepath = os.path.join("output", f"allmesh_{filename}.msh")
    with open(filepath, "w") as f:
        # $MeshFormat 
        f.write("$MeshFormat\n")
        f.write("2.2 0 8\n")
        f.write("$EndMeshFormat\n")
        f.write("$PhysicalNames\n")
        f.write("4\n")  
        f.write("2 10 \"WALL\"\n")
        f.write("2 20 \"INLET\"\n")
        f.write("2 30 \"OUTLET\"\n")
        f.write("3 100 \"INTERNAL\"\n")
        f.write("$EndPhysicalNames\n")
        # $Nodes 
        f.write("$Nodes\n")
        f.write(f"{mesh.num_of_nodes}\n")  
        nodes_sorted = sorted(mesh.nodes, key=lambda obj: obj.id)
        for node in nodes_sorted:
                f.write(f"{node.id} {node.x} {node.y} {node.z}\n")
        f.write("$EndNodes\n")
        # elements
        f.write("$Elements\n")
        f.write(f"{mesh.num_of_elements}\n")
        elements_countor=0
        for triangle in mesh.triangles_WALL:
            f.write(f"{triangle.id} 2 2 10 1 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
            elements_countor+=1

        for triangle in mesh.triangles_INLET:
            elements_countor+=1
            f.write(f"{elements_countor} 2 2 20 1 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
        for triangle in mesh.triangles_OUTLET:
            elements_countor+=1
            f.write(f"{elements_countor} 2 2 30 1 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
        for quad in mesh.quadrangles_INLET:
            elements_countor+=1
            f.write(f"{elements_countor} 3 2 20 1 {quad.id0} {quad.id1} {quad.id2} {quad.id3}\n")
        for quad in mesh.quadrangles_OUTLET:
            elements_countor+=1
            f.write(f"{elements_countor} 3 2 30 1 {quad.id0} {quad.id1} {quad.id2} {quad.id3}\n")
        for tetra in mesh.tetras_INTERNAL:
            elements_countor+=1
            f.write(f"{elements_countor} 4 2 100 1 {tetra.id0} {tetra.id1} {tetra.id2} {tetra.id3}\n")
        for prism in mesh.prisms_INTERNAL:
            elements_countor+=1
            f.write(f"{elements_countor} 6 2 100 1 {prism.id0} {prism.id1} {prism.id2} {prism.id3} {prism.id4} {prism.id5}\n")

        f.write("$EndElements\n")
