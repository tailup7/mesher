import config
import node
import myio
import boundarylayer
import gmsh
import os
import numpy as np
import sys
import trimesh
import utility
import cell

def calc_radius(filepath_stl, filepath_centerline, nodes_centerline):
    # 半径計算のため、読み込んだ表面形状を細かく再メッシュ
    if not gmsh.isInitialized():
        gmsh.initialize()
    path = os.path.dirname(os.path.abspath(__file__))
    gmsh.merge(os.path.join(path, filepath_stl)) 
    gmsh.model.mesh.classifySurfaces(angle = 40 * np.pi / 180, boundary=True, forReparametrization=True)
    gmsh.model.mesh.createGeometry()
    gmsh.model.geo.synchronize()
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
    gmsh.option.setNumber('Mesh.Algorithm', 1)
    gmsh.option.setNumber("Mesh.MeshSizeMin", config.MESHSIZE*0.5)
    gmsh.option.setNumber("Mesh.MeshSizeMax", config.MESHSIZE*0.5)
    gmsh.model.mesh.generate(2)
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    stl_file = os.path.join(output_folder, "for_calculate_radius.stl")
    gmsh.write(stl_file)

    mesh = trimesh.load_mesh(stl_file)
    vertices = mesh.vertices 
    unique_nodes = np.unique(vertices, axis=0)
    surfacenodes = unique_nodes.tolist()

    radius_list=[]
    countor=[]    
    radius_list_smooth = []
    for i in range(config.num_of_centerlinenodes+1):
        radius_list.append(0.0)
        countor.append(0)
        radius_list_smooth.append(0.0)

    for i in range(len(surfacenodes)):
        surfacenode=node.NodeAny(i,surfacenodes[i][0],surfacenodes[i][1],surfacenodes[i][2])
        surfacenode.find_closest_centerlinenode(nodes_centerline)
        surfacenode.find_projectable_centerlineedge(nodes_centerline)
        if surfacenode.projectable_centerlineedge_id != None:
            radius_list[surfacenode.projectable_centerlineedge_id+1] += surfacenode.projectable_centerlineedge_distance
            countor[surfacenode.projectable_centerlineedge_id+1]+=1
        else:
            if surfacenode.closest_centerlinenode_id==0:
                radius_list[0] += utility.calculate_PH_length(surfacenode,nodes_centerline[0],nodes_centerline[1])
                countor[0] += 1
            elif surfacenode.closest_centerlinenode_id==config.num_of_centerlinenodes-1:
                radius_list[config.num_of_centerlinenodes] += utility.calculate_PH_length(surfacenode,nodes_centerline[-2],nodes_centerline[-1])
                countor[config.num_of_centerlinenodes] += 1
            else:
                radius_list[surfacenode.closest_centerlinenode_id]+=surfacenode.closest_centerlinenode_distance
                countor[surfacenode.closest_centerlinenode_id] += 1
                radius_list[surfacenode.closest_centerlinenode_id+1]+=surfacenode.closest_centerlinenode_distance
                countor[surfacenode.closest_centerlinenode_id+1] += 1

    for i in range(len(radius_list)):
        if countor[i]!=0:
            radius_list[i] /= countor[i]
    
    if radius_list[0] < radius_list[1]*0.7:
        radius_list[0] = radius_list[1]
    if radius_list[-1] < radius_list[-2]*0.7:
        radius_list[-1]=radius_list[-2]

    # 応急処置的 (中心線点群の端がSTLの端面に届いていない場合)
    if radius_list[0] < radius_list[4]*0.7:
        radius_list[0] = radius_list[4]
    if radius_list[-1] < radius_list[-5]*0.7:
        radius_list[-1] = radius_list[-5]
    if radius_list[1] < radius_list[5]*0.7:
        radius_list[1] = radius_list[5]
    if radius_list[-2] < radius_list[-6]*0.7:
        radius_list[-2] = radius_list[-6]
    if radius_list[2] < radius_list[6]*0.7:
        radius_list[2] = radius_list[6]
    if radius_list[-3] < radius_list[-7]*0.7:
        radius_list[-3] = radius_list[-7]
    if radius_list[3] < radius_list[7]*0.7:
        radius_list[3] = radius_list[7]
    if radius_list[-4] < radius_list[-8]*0.7:
        radius_list[-4] = radius_list[-8]

    radius_list_smooth[0]=(radius_list[0]+radius_list[1])/2
    radius_list_smooth[-1]=(radius_list[-1]+radius_list[-2])/2
    for i in range(1,len(radius_list)-1):
        radius_list_smooth[i] = (radius_list[i-1]+radius_list[i]+radius_list[i+1])/3

    config.inlet_radius = radius_list_smooth[0]
    config.outlet_radius = radius_list_smooth[-1]

    myio.add_radiusinfo_to_centerlinefile(filepath_centerline, radius_list_smooth)
    gmsh.finalize()
    return radius_list_smooth

# generate background mesh
def generate_pos_bgm(filepath, nodes_centerline,radius_list,filename):
    if not gmsh.isInitialized():
        gmsh.initialize()
    gmsh.merge(filepath)  
    print("filepath of input stl at generate_pos_bgm :",filepath)
    gmsh.model.mesh.classifySurfaces(angle = 40 * np.pi / 180, boundary=True, forReparametrization=True)
    gmsh.model.mesh.createGeometry()
    gmsh.model.geo.synchronize()
    # メッシュオプション
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
    gmsh.option.setNumber('Mesh.Algorithm', 1)
    gmsh.option.setNumber("Mesh.MeshSizeMin", config.MESHSIZE)
    gmsh.option.setNumber("Mesh.MeshSizeMax", config.MESHSIZE)
    wall = gmsh.model.getEntities(2)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    wall_id = [e[1] for e in wall]
    print("wall=",wall)
    print("wall_id=",wall_id)

    boundary_curv = gmsh.model.getBoundary(wall)
    print("1D entities which make boundary_curv are",boundary_curv)
    boundary_curv_id = [e[1] for e in boundary_curv]
    print("IDs of 1D entities which make boundary_curv are ",boundary_curv_id)

    boundary_curv_id_list = gmsh.model.geo.addCurveLoops(boundary_curv_id)
    print("Remake curve loops . These IDs are ",boundary_curv_id_list)

    for i in boundary_curv_id_list:
        a=gmsh.model.geo.addPlaneSurface([i])
    print("Curve loops makes closed plane surface. IDs of plane surfaces are",a)

    gmsh.model.geo.synchronize()  
    check = gmsh.model.getEntities(2)
    print(check)
    surfaceAll_id = [e[1] for e in check]
    print("All 2D surface entities IDs are ",surfaceAll_id)
    surfaceLoop=gmsh.model.geo.addSurfaceLoop(surfaceAll_id)
    gmsh.model.geo.addVolume([surfaceLoop])
    gmsh.model.geo.synchronize()  
    gmsh.model.mesh.generate(3) 
    nodeids, coords, _ = gmsh.model.mesh.getNodes()
    nodes_any=node.coords_to_nodes(nodeids,coords)

    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    vtk_file = os.path.join(output_folder, f"bgm_{filename}.vtk")
    msh_file = os.path.join(output_folder, f"bgm_{filename}.msh")
    gmsh.write(vtk_file)
    gmsh.write(msh_file)
    print(f"output bgm_{filename}.vtk")
    print(f"output bgm_{filename}.msh")

    nodeany_dict={}                                          
    for node_any in nodes_any:
        nodeany_dict[node_any.id] = node_any  
        node_any.find_closest_centerlinenode(nodes_centerline)
        node_any.find_projectable_centerlineedge(nodes_centerline)
        node_any.set_edgeradius(radius_list)
    tetra_list = myio.read_msh_tetra(msh_file)
    filepath_pos=myio.write_pos_bgm(tetra_list,nodeany_dict,filename)

    gmsh.finalize()

def make_surfacemesh(filepath_stl,nodes_centerline, radius_list,mesh,filename):
    if not gmsh.isInitialized():
        gmsh.initialize()
    path = os.path.dirname(os.path.abspath(__file__))
    gmsh.merge(os.path.join(path, filepath_stl))
    filepath_pos=os.path.join(path, "output","bgm_original.pos")

    gmsh.model.mesh.classifySurfaces(angle = 40 * np.pi / 180, boundary=True, forReparametrization=True)
    gmsh.model.mesh.createGeometry()
    gmsh.model.geo.synchronize()

    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
    gmsh.option.setNumber('Mesh.Algorithm', 1)
    gmsh.option.setNumber("Mesh.Optimize", 10)

    gmsh.merge(filepath_pos)             
    bg_field = gmsh.model.mesh.field.add("PostView")    
    gmsh.model.mesh.field.setNumber(bg_field, "ViewIndex", 0) 
    gmsh.model.mesh.field.setAsBackgroundMesh(bg_field) 

    gmsh.model.geo.synchronize()

    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)      
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)     
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.optimize()
    output_folder = "output"
    vtk_file = os.path.join(output_folder, f"surfacemesh_{filename}.vtk")
    stl_file = os.path.join(output_folder, f"surfacemesh_{filename}.stl")
    gmsh.write(vtk_file)
    gmsh.write(stl_file)
    print(f"output surfacemesh_{filename}.vtk")
    print(f"output surfacemesh_{filename}.stl")

    surfacenodes,surfacetriangles = myio.read_vtk_surfacemesh(vtk_file) 
    surfacenode_dict={}
    for surfacenode in surfacenodes:
        surfacenode.find_closest_centerlinenode(nodes_centerline)        #
        surfacenode.find_projectable_centerlineedge(nodes_centerline)    #
        surfacenode.set_edgeradius(radius_list)                          #
        surfacenode_dict[surfacenode.id] = surfacenode
        mesh.nodes.append(surfacenode)
        mesh.num_of_nodes += 1
    for surfacetriangle in surfacetriangles:
        surfacetriangle.calc_unitnormal(nodes_centerline)                #
        surfacetriangle.calc_centroid()                                  #
        surfacetriangle.find_closest_centerlinenode(nodes_centerline)    #
        surfacetriangle.assign_correspondcenterlinenode_to_surfacenode()
        mesh.triangles_WALL.append(surfacetriangle)
        mesh.num_of_elements += 1

    myio.add_scalarinfo_to_surfacemesh_original_vtkfile(vtk_file,surfacetriangles)
    gmsh.finalize()
    return surfacenode_dict, surfacenodes, surfacetriangles, mesh

def make_prismlayer(surfacenode_dict,surfacetriangles,mesh):
    print("start generating prism layer")
    # 内側 1 ~ n 層を作成
    for i in range(1,config.NUM_OF_LAYERS+1):
        mesh,layernode_dict=boundarylayer.make_nthlayer_surfacenode(i, surfacenode_dict, surfacetriangles, mesh)
        mesh=boundarylayer.make_nthlayer_prism(i,surfacetriangles,mesh)
        config.num_of_boundarylayernodes = mesh.num_of_nodes
    print("finished generating prism layer")
    return mesh, layernode_dict

def make_tetramesh(nodes_centerline,layernode_dict,mesh,filename):
    filepath_stl_mostinner = myio.write_stl_innersurface(mesh,nodes_centerline,layernode_dict)
    gmsh.initialize()
    path = os.path.dirname(os.path.abspath(__file__))
    gmsh.merge(os.path.join(path, filepath_stl_mostinner))  

    gmsh.model.mesh.createTopology() # 境界面上のNodeに接続する形でメッシュを作るという制約
    
    innerwall = gmsh.model.getEntities(2)
    gmsh.model.geo.synchronize()
    innerwall_id=[]
    for i in innerwall:
        innerwall_id.append(i[1])
    gmsh.model.addPhysicalGroup(2, innerwall_id, 99)
    gmsh.model.setPhysicalName(2, 99, "INNERWALL")

    surfaceids_aroundvolume=[]
    for i in range(len(innerwall)):
        surfaceids_aroundvolume.append(innerwall[i][1])

    boundary_lines = gmsh.model.getBoundary(innerwall)

    boundary_line_id=[]
    for boundary_line in boundary_lines:
        boundary_line_id.append(boundary_line[1])

    boundary_curves = gmsh.model.geo.addCurveLoops(boundary_line_id)
    for boundary_curve in boundary_curves:
        boundary_surface_id = gmsh.model.geo.addPlaneSurface([boundary_curve])
        surfaceids_aroundvolume.append(boundary_surface_id)

    innerSurfaceLoop = gmsh.model.geo.addSurfaceLoop(surfaceids_aroundvolume)
    gmsh.model.geo.addVolume([innerSurfaceLoop])
    gmsh.model.geo.synchronize()

    # 先にメッシング
    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
    gmsh.option.setNumber('Mesh.Algorithm', 1)
    gmsh.option.setNumber("Mesh.Optimize", 10)
    gmsh.merge(os.path.join("output",f'bgm_{filename}.pos'))              
    bg_field = gmsh.model.mesh.field.add("PostView")    
    gmsh.model.mesh.field.setNumber(bg_field, "ViewIndex", 0) 
    gmsh.model.mesh.field.setAsBackgroundMesh(bg_field) 

    gmsh.model.geo.synchronize()

    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)      
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)     
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize()

    # 後から physical naming
    surfaces_after_voluming = gmsh.model.getEntities(2)
    something = []
    for surface_after_voluming in surfaces_after_voluming:
        something.append(surface_after_voluming[1])
    something = list(set(something)-set(innerwall_id))

    inletlist=[]
    outletlist=[]
    for i in range(len(something)):
        node_ids, node_coords, _ = gmsh.model.mesh.getNodes(2,something[i],True)
        center_x = 0.0
        center_y = 0.0
        center_z = 0.0
        for j in range(len(node_coords)):
            if j%3==0:
                center_x+=node_coords[j]
            elif j%3==1:
                center_y+=node_coords[j]
            else:
                center_z+=node_coords[j]
        center_x=float(center_x/len(node_ids))
        center_y=float(center_y/len(node_ids))
        center_z=float(center_z/len(node_ids))
        center=[center_x,center_y,center_z]
        inletsurface_center = np.array([config.inlet_point.x,config.inlet_point.y,config.inlet_point.z])
        outletsurface_center = np.array([config.outlet_point.x,config.outlet_point.y,config.outlet_point.z])
        distance_frominlet = np.linalg.norm(inletsurface_center-np.array(center))
        distance_fromoutlet = np.linalg.norm(outletsurface_center-np.array(center))
        if distance_frominlet < config.inlet_radius:
            inletlist.append(something[i])
        if distance_fromoutlet < config.outlet_radius:
            outletlist.append(something[i])
    print("INLET entities are ",inletlist)
    print("OUTLET entities are ",outletlist)
    if inletlist == []:
        print("can't find inlet surface.")
        sys.exit()
    if outletlist == []:
        print("can't find outlet surface.")
        sys.exit()

    gmsh.model.addPhysicalGroup(2, inletlist, 20)
    gmsh.model.setPhysicalName(2, 20, "INLET")

    gmsh.model.addPhysicalGroup(2, outletlist, 30)
    gmsh.model.setPhysicalName(2, 30, "OUTLET")

    volumeAll = gmsh.model.getEntities(3)
    three_dimension_list = []
    for i in range(len(volumeAll)):
        three_dimension_list.append(volumeAll[i][1])
    gmsh.model.addPhysicalGroup(3, three_dimension_list, 100)
    gmsh.model.setPhysicalName(3, 100, "INTERNAL")
    gmsh.model.geo.synchronize()

    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    output_folder="output"
    vtk_file = os.path.join(output_folder, f"innermesh_{filename}.vtk")
    stl_file = os.path.join(output_folder, f"innermesh_{filename}.stl")
    msh_file = os.path.join(output_folder, f"innermesh_{filename}.msh")
    gmsh.write(vtk_file)
    gmsh.write(stl_file)
    gmsh.write(msh_file)
    print(f"output innermesh_{filename}.vtk")
    print(f"output innermesh_{filename}.stl")
    print(f"output innermesh_{filename}.msh")
    mesh = myio.read_msh_innermesh(msh_file,mesh)
    gmsh.finalize()
    return mesh

def naming_inlet_outlet(mesh,nodes_centerline):
    nodes_on_inletboundaryedge=[]
    nodes_on_outletboundaryedge=[]
    start = config.num_of_surfacenodes*config.NUM_OF_LAYERS
    end = config.num_of_surfacenodes*(config.NUM_OF_LAYERS+1)-1
    for i in range(start,end+1):
        if mesh.nodes[i].on_inlet_boundaryedge == True:
            nodes_on_inletboundaryedge.append(mesh.nodes[i])
        if mesh.nodes[i].on_outlet_boundaryedge == True:
            nodes_on_outletboundaryedge.append(mesh.nodes[i])
    for i in range(1,config.NUM_OF_LAYERS+1):
        mesh = boundarylayer.make_nthlayer_quad(i,nodes_centerline, nodes_on_inletboundaryedge, nodes_on_outletboundaryedge,mesh)
    print("naming INLET OUTLET to quadrangles on surface.")
    return mesh

def deform_surface(nodes_targetcenterline, radius_list_target, nodes_centerline,surfacenodes,surfacetriangles,mesh):
    print("start deforming surface mesh")
    for i in range(config.num_of_centerlinenodes):
        nodes_centerline[i].calc_tangentvec(nodes_centerline)
        nodes_targetcenterline[i].calc_tangentvec(nodes_targetcenterline)
        
    utility.moving_average_for_tangentvec(nodes_centerline)
    utility.moving_average_for_tangentvec(nodes_targetcenterline)
    for i in range(config.num_of_centerlinenodes):
        nodes_targetcenterline[i].calc_parallel_vec(nodes_centerline)
        nodes_targetcenterline[i].calc_rotation_matrix(nodes_centerline)
    # 移動後の表面を作成
    surfacenodes_moved=[]
    nodes_moved_dict={}
    for surfacenode in surfacenodes:
        surfacenode_moved=node.NodeMoved(surfacenode.id,0,0,0)
        countor=0
        for correspond_centerlinenode in surfacenode.correspond_centerlinenodes:
            surfacenode_moved.x += correspond_centerlinenode.x # 複数のcorrespond_centerlinenode がある場合、起点が複数になってしまう。
            surfacenode_moved.y += correspond_centerlinenode.y
            surfacenode_moved.z += correspond_centerlinenode.z
            localvec = utility.vector(surfacenode)-utility.vector(correspond_centerlinenode)
            movementvec = (nodes_targetcenterline[correspond_centerlinenode.id].parallel_vec +
                                nodes_targetcenterline[correspond_centerlinenode.id].rotation_matrix @ localvec)
            surfacenode_moved.x += movementvec[0]
            surfacenode_moved.y += movementvec[1]
            surfacenode_moved.z += movementvec[2]
            countor += 1
        surfacenode_moved.x = surfacenode_moved.x/countor
        surfacenode_moved.y = surfacenode_moved.y/countor
        surfacenode_moved.z = surfacenode_moved.z/countor

        surfacenode_moved.find_closest_centerlinenode(nodes_targetcenterline)
        if radius_list_target != None:
            surfacenode_moved.find_projectable_centerlineedge(nodes_targetcenterline)
            surfacenode_moved.set_edgeradius(radius_list_target)
            surfacenode_moved.execute_deform_radius(radius_list_target,nodes_targetcenterline)

        mesh.nodes.append(surfacenode_moved)
        mesh.num_of_nodes += 1
        nodes_moved_dict[surfacenode.id]=surfacenode_moved
        surfacenodes_moved.append(surfacenode_moved)

    surfacetriangles_moved=[]
    for surfacetriangle in surfacetriangles:
        node0=nodes_moved_dict[surfacetriangle.node0.id]
        node1=nodes_moved_dict[surfacetriangle.node1.id]
        node2=nodes_moved_dict[surfacetriangle.node2.id]
        surfacetriangle_moved=cell.Triangle(surfacetriangle.id,node0,node1,node2)
        surfacetriangle_moved.calc_unitnormal(nodes_targetcenterline)
        surfacetriangle_moved.calc_centroid()
        surfacetriangle_moved.find_closest_centerlinenode(nodes_targetcenterline)
        # surfacetriangle_moved.assign_correspondcenterlinenode_to_surfacenode()  # これ必要ある??? ← 一旦消して試す
        surfacetriangles_moved.append(surfacetriangle_moved)
        mesh.triangles_WALL.append(surfacetriangle_moved)
        mesh.num_of_elements += 1

    filepath_movedsurface = myio.write_stl_surfacetriangles(surfacetriangles_moved,"movedsurface.stl")
    print("finished deforming surface mesh. output movedsurface.stl")
    return filepath_movedsurface,nodes_moved_dict,surfacetriangles_moved,mesh

def GUI_setting():
    gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
    gmsh.option.setNumber("Mesh.Lines", 1)
    gmsh.option.setNumber("Geometry.PointLabels", 1)
    gmsh.option.setNumber("Mesh.LineWidth", 2)
    gmsh.option.setNumber("General.MouseInvertZoom", 1)
    gmsh.option.setNumber("General.Axes", 3)
    gmsh.option.setNumber("General.Trackball", 0)
    gmsh.option.setNumber("General.RotationX", 0)
    gmsh.option.setNumber("General.RotationY", 0)
    gmsh.option.setNumber("General.RotationZ", 0)
    gmsh.option.setNumber("General.Terminal", 1)