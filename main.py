import sys
import os
import gmsh
import func
import myio
import config
import meshinfo

already_meshing  = False
nodes_centerline = None
surfacenodes     = None 
surfacetriangles = None

def input_meshing_parameter():
    print("---mesh parameter---")
    print("FIRST_LAYER_RATIO : ",config.FIRST_LAYER_RATIO)
    print("GROWTH_RATE : ",config.GROWTH_RATE)
    print("NUM_OF_LAYERS",config.NUM_OF_LAYERS)
    change = input("Change parameters? (y/n): ").strip().lower()
    if change == "y":
        try:
            config.FIRST_LAYER_RATIO = float(input("Enter FIRST_LAYER_RATIO: "))
            config.GROWTH_RATE = float(input("Enter GROWTH_RATE: "))
            config.NUM_OF_LAYERS = int(input("Enter NUM_OF_LAYERS: "))
        except ValueError:
            print("Invalid input. Using default values.")

def meshing():
    global nodes_centerline
    global surfacenodes
    global surfacetriangles
    mesh = meshinfo.Mesh() 
    filepath_centerline = myio.select_csv()
    filepath_stl = myio.select_stl()
    nodes_centerline = myio.read_csv_original(filepath_centerline)
    radius_list = func.calc_radius(filepath_stl,nodes_centerline)
    func.generate_pos_bgm(filepath_stl, nodes_centerline, radius_list,"original")
    surfacenode_dict, surfacenodes, surfacetriangles, mesh = func.make_surfacemesh(filepath_stl,nodes_centerline, radius_list,mesh,"original")
    mesh, layernode_dict,surfacetriangles = func.make_prismlayer(surfacenode_dict,surfacetriangles,mesh)
    mesh = func.make_tetramesh(nodes_centerline,layernode_dict,mesh,"original")
    mesh=func.naming_inlet_outlet(mesh,nodes_centerline)
    myio.write_msh_allmesh(mesh,"original") 
    gmsh.initialize()
    gmsh.merge(os.path.join("output", "allmesh_original.msh"))
    gmsh.write(os.path.join("output","allmesh_original.vtk"))
    print("-------- Finished Make Mesh --------")
    func.GUI_setting()
    gmsh.fltk.run()
    gmsh.finalize()
    global already_meshing
    already_meshing = True

def deform():
    print("-------- Start Deform Mesh --------")
    filepath_target = myio.select_csv()
    mesh_deform = meshinfo.Mesh()
    global nodes_centerline
    global surfacenodes
    global surfacetriangles
    nodes_targetcenterline, radius_list_target = myio.read_csv_target(filepath_target)
    filepath_movedsurface, nodes_moved_dict, surfacetriangles_moved, mesh_deform = func.deform_surface(nodes_targetcenterline,  
                                                                                                        radius_list_target,
                                                                                                        nodes_centerline,
                                                                                                        surfacenodes,
                                                                                                        surfacetriangles,mesh_deform)
    if radius_list_target == None:
        radius_for_bgm = func.calc_radius(filepath_movedsurface,nodes_targetcenterline)
        for i in range(1,config.num_of_surfacenodes+1):
            nodes_moved_dict[i].find_projectable_centerlineedge(nodes_targetcenterline)
            nodes_moved_dict[i].set_edgeradius(radius_for_bgm)
    else:
        radius_for_bgm = radius_list_target
    func.generate_pos_bgm(filepath_movedsurface,nodes_targetcenterline, radius_for_bgm,"deform")
    mesh_deform, layernode_dict, surfacetriangles_moved = func.make_prismlayer(nodes_moved_dict,surfacetriangles_moved,mesh_deform)
    mesh_deform = func.make_tetramesh(nodes_targetcenterline,layernode_dict,mesh_deform,"deform")
    mesh_deform=func.naming_inlet_outlet(mesh_deform,nodes_targetcenterline)
    myio.write_msh_allmesh(mesh_deform,"deform")
    gmsh.initialize()    
    gmsh.merge(os.path.join("output", "allmesh_deform.msh"))
    gmsh.write(os.path.join("output","allmesh_deform.vtk"))
    print("-------- Finished Deform Mesh --------")
    func.GUI_setting()
    gmsh.fltk.run()
    gmsh.finalize()

def ask_which():
    which = input("Meshing or Deform? (m / d): ").strip().lower()
    try:
        if which == "m":
            meshing()
        elif which == "d" and already_meshing==True:
            deform()
        elif which == "d" and already_meshing==False:
            print("This procedure is currently in preparation. Please meshing first, sorry... ;;")
            sys.exit()
        else:
            print("Invalid input. Please enter 'm' for Meshing or 'd' for Deform.")
    except ValueError:
        print("Invalid input. Using default values.")

if __name__=="__main__":
    input_meshing_parameter()
    ask_which()
    ask_which()
