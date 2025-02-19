import node
import cell
import config
import sys
import os

def read_txt_centerline(filepath):
    if not os.path.isfile(filepath):
            print(f"Error: '{filepath}' does not exist.")
            sys.exit()
    with open(filepath, 'r') as file:
        lines = file.readlines()
    valid_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    nodes_centerline = []
    index = 0
    sum_x=0
    sum_y=0
    sum_z=0
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'): 
            parts = line.split() 
            x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            sum_x+=x
            sum_y+=y
            sum_z+=z 
            node_centerline = node.NodeCenterline(index, x, y, z)
            nodes_centerline.append(node_centerline)
            if index == 0:
                config.inlet_point = node_centerline
            elif index == len(valid_lines)-1:
                config.outlet_point = node_centerline
            index += 1
    config.num_of_centerlinenodes = index
    return nodes_centerline

def write_txt_edgeradii(edgeradii):
    os.makedirs("output",exist_ok = True)
    filepath=os.path.join("output","radius.txt")
    with open(filepath, 'w') as f:
        f.write(f"# {len(edgeradii)}\n")
        for edgeradius in edgeradii:
            f.write(f"{edgeradius}\n")

def read_msh_tetra():
    filepath = os.path.join("output", "bgm.msh")
    if not os.path.isfile(filepath):
        print(f"Error: '{filepath}' does not exist.")
        sys.exit()
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

def write_pos_bgm(tetra_list,nodeany_dict):
    filepath = os.path.join("output", "bgm.pos")
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

def read_vtk_outersurface(filepath_vtk):
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
            triangle_id=1   #不要..?
            surfacetriangles = []
            continue
        if points_section:
            if not line:
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
            if not line:
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
    return surfacenodes,surfacetriangles

def write_stl_mostinnersurface(triangle_list):
    filepath=os.path.join("output","mostinnersurface.stl")
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

def read_msh_innermesh(filepath,mesh):

    nodes_innerwall=[]
    node_innermesh_dict={}
    nodesid_composing_innerwalltriangle=set()
    nodesid_composing_inlettriangle=set()
    nodesid_composing_outlettriangle=set()

    with open(filepath, "r") as file:
        lines = file.readlines()

    node_section = False
    skip_next_line = False  
    element_section = False

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("$Nodes"):
            node_section = True
            skip_next_line = True 
            continue

        if skip_next_line:
            skip_next_line = False  
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
            mesh.nodes.append(node_innermesh)
            mesh.num_of_nodes+=1

        if line.startswith("$Elements"):
            element_section = True
            skip_next_line = True  
            continue
        if skip_next_line:
            skip_next_line = False
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
            physical_group = int(parts[3])  # 物理グループ（4列目）

            if  elem_type == 2: 
                node0 = node_innermesh_dict[int(parts[-3])]
                node1 = node_innermesh_dict[int(parts[-2])]
                node2 = node_innermesh_dict[int(parts[-1])]

                if physical_group == 99 :
                    nodes_innerwall.append(node0)
                    nodes_innerwall.append(node1)
                    nodes_innerwall.append(node2)
                    nodesid_composing_innerwalltriangle.update(map(int, parts[-3:]))

                elif physical_group == 20:
                    triangle_inlet = cell.Triangle(elem_id, node0, node1, node2)
                    nodesid_composing_inlettriangle.update(map(int, parts[-3:])) 
                    mesh.triangles_INLET.append(triangle_inlet)
                    mesh.num_of_elements += 1

                elif physical_group == 30:
                    triangle_outlet = cell.Triangle(elem_id, node0, node1, node2)
                    nodesid_composing_outlettriangle.update(map(int, parts[-3:]))
                    mesh.triangles_OUTLET.append(triangle_outlet)
                    mesh.num_of_elements += 1
            if  elem_type == 4: 
                id0 = int(parts[-4])
                id1 = int(parts[-3])
                id2 = int(parts[-2])
                id3 = int(parts[-1])
                tetra = cell.Tetra(id0,id1,id2,id3)
                mesh.tetras_INTERNAL.append(tetra)
                mesh.num_of_elements += 1 

    # 99(innerwall)と20or30(端面)を構成するNodeはboundaryNodeとして抽出する
    nodesid_on_inlet_boundaryedge = nodesid_composing_innerwalltriangle & nodesid_composing_inlettriangle
    nodesid_on_outlet_boundaryedge= nodesid_composing_innerwalltriangle & nodesid_composing_outlettriangle
    print("num of nodesid_composing_innerwalltriangle is ",len(nodesid_composing_innerwalltriangle))
    print("num of nodesid_on_inlet_boundaryedge is ",len(nodesid_on_inlet_boundaryedge))
    for nodeid in nodesid_on_inlet_boundaryedge:
        node_innermesh_dict[nodeid].on_inlet_boundaryedge = True
    for nodeid in nodesid_on_outlet_boundaryedge:
        node_innermesh_dict[nodeid].on_outlet_boundaryedge = True
    config.num_of_innermeshnodes = mesh.num_of_nodes

    return  nodes_innerwall, node_innermesh_dict, mesh

def write_msh_allmesh(mesh):
    filepath = os.path.join("output", "allmesh.msh")
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
            f.write(f"{triangle.id} 2 2 20 1 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
            elements_countor+=1
        for triangle in mesh.triangles_OUTLET:
            f.write(f"{triangle.id} 2 2 30 1 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
            elements_countor+=1

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
