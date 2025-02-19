import config
import gmsh
import os
import numpy as np
import sys

# generate background mesh
def generate_bgm(filepath):
    gmsh.initialize(sys.argv)
    path = os.path.dirname(os.path.abspath(__file__))
    gmsh.merge(os.path.join(path, filepath))  
    
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
    print("boundary_curv=",boundary_curv)
    boundary_curv_id = [e[1] for e in boundary_curv]
    print("boundary_curv_id=",boundary_curv_id)

    boundary_curv_id_list = gmsh.model.geo.addCurveLoops(boundary_curv_id)
    print("boundary_curv_id_list=",boundary_curv_id_list)

    for i in boundary_curv_id_list:
        a=gmsh.model.geo.addPlaneSurface([i])
        print("a=",a)

    gmsh.model.geo.synchronize()  
    check = gmsh.model.getEntities(2)
    print(check)
    surfaceAll_id = [e[1] for e in check]
    print("surfaceAll_id=",surfaceAll_id)
    surfaceLoop=gmsh.model.geo.addSurfaceLoop(surfaceAll_id)
    gmsh.model.geo.addVolume([surfaceLoop])
    gmsh.model.geo.synchronize()  
    gmsh.model.mesh.generate(3) 
    nodeids, coords, _ = gmsh.model.mesh.getNodes()

    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    vtk_file = os.path.join(output_folder, "bgm.vtk")
    msh_file = os.path.join(output_folder, "bgm.msh")
    gmsh.write(vtk_file)
    gmsh.write(msh_file)
    gmsh.finalize()

    # 半径計算のため、読み込んだ表面形状を細かく再メッシュ
    gmsh.initialize(sys.argv)
    path = os.path.dirname(os.path.abspath(__file__))
    gmsh.merge(os.path.join(path, filepath)) 
    gmsh.model.mesh.classifySurfaces(angle = 40 * np.pi / 180, boundary=True, forReparametrization=True)
    gmsh.model.mesh.createGeometry()
    gmsh.model.geo.synchronize()
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
    gmsh.option.setNumber('Mesh.Algorithm', 1)
    gmsh.option.setNumber("Mesh.MeshSizeMin", config.MESHSIZE*0.5)
    gmsh.option.setNumber("Mesh.MeshSizeMax", config.MESHSIZE*0.5)
    gmsh.model.mesh.generate(2)
    stl_file = os.path.join(output_folder, "for_calculate_radius.stl")
    gmsh.write(stl_file)
    gmsh.finalize()

    return nodeids, coords,stl_file

def surfacemesh(filepath_stl):
    gmsh.initialize()

    path = os.path.dirname(os.path.abspath(__file__))
    gmsh.merge(os.path.join(path, filepath_stl))

    gmsh.model.mesh.classifySurfaces(angle = 40 * np.pi / 180, boundary=True, forReparametrization=True)
    gmsh.model.mesh.createGeometry()
    gmsh.model.geo.synchronize()

    gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
    gmsh.option.setNumber('Mesh.Algorithm', 1)
    gmsh.option.setNumber("Mesh.Optimize", 10)

    gmsh.merge(os.path.join("output",'bgm.pos'))             
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
    vtk_file = os.path.join(output_folder, "surfacemesh.vtk")
    stl_file = os.path.join(output_folder, "surfacemesh.stl")
    gmsh.write(vtk_file)
    gmsh.write(stl_file)
    gmsh.finalize()
    return vtk_file

def make_innermesh(filepath_stl):
    gmsh.initialize()

    path = os.path.dirname(os.path.abspath(__file__))
    gmsh.merge(os.path.join(path, filepath_stl))  

    gmsh.model.mesh.createTopology()
    
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
    gmsh.merge(os.path.join("output",'bgm.pos'))              
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
    vtk_file = os.path.join(output_folder, "innermesh.vtk")
    stl_file = os.path.join(output_folder, "innermesh.stl")
    msh_file = os.path.join(output_folder, "innermesh.msh")
    gmsh.write(vtk_file)
    gmsh.write(stl_file)
    gmsh.write(msh_file)

    gmsh.finalize()
    return msh_file

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