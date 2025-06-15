import sys
import os
import traceback
import time
import gmsh
import func
import myio
import config
import meshinfo

did_meshing      = False
surfacenodes     = None 
surfacetriangles = None

# gmsh.model.mesh.classifySurfaces の引数はどう設定するべきか

def input_meshing_parameter():
    print("------- mesh parameter -------")
    print("MESHSIZE_SCALING_FACTOR :", config.SCALING_FACTOR)
    print("FIRST_LAYER_RATIO       :", config.FIRST_LAYER_RATIO)
    print("GROWTH_RATE             :", config.GROWTH_RATE)
    print("NUM_OF_LAYERS           :", config.NUM_OF_LAYERS)
    change = input("Change parameters? (y/n): ").strip().lower()
    if change == "y":
        try:
            config.SCALING_FACTOR    = float(input("Enter MESHSIZE_SCALING_FACOTOR: "))
            config.FIRST_LAYER_RATIO = float(input("Enter FIRST_LAYER_RATIO: "))
            config.GROWTH_RATE       = float(input("Enter GROWTH_RATE: "))
            config.NUM_OF_LAYERS     = int(input("Enter NUM_OF_LAYERS: "))
        except ValueError:
            print("Invalid input. Using default values.")

def meshing():
    start=time.time()
    global surfacenodes
    global surfacetriangles
    mesh = meshinfo.Mesh() 
    filepath_centerline = myio.select_csv("original")
    filepath_stl = myio.select_stl()
    nodes_centerline, radius_list = myio.read_csv_centerline(filepath_centerline)
    if radius_list == None:
        radius_list = func.calc_radius(filepath_stl, filepath_centerline, nodes_centerline) #これは消す、変える。扁平な形状などは、最も直径が小さくなる部分で考えてメッシュサイズを設定する必要がある。
    myio.write_txt_parameter()
    func.generate_pos_bgm(filepath_stl, nodes_centerline, radius_list,"original", 40)  
    surfacenode_dict, surfacenodes, surfacetriangles, mesh = func.make_surfacemesh(filepath_stl,nodes_centerline, radius_list,mesh,"original")
    mesh, layernode_dict = func.make_prismlayer(surfacenode_dict,surfacetriangles,mesh)
    mesh = func.make_tetramesh(layernode_dict,mesh,"original")
    mesh = func.naming_inlet_outlet(mesh,nodes_centerline)
    myio.write_msh_allmesh(mesh,"original") 
    gmsh.initialize()
    gmsh.merge(os.path.join("output", "allmesh_original.msh"))
    gmsh.write(os.path.join("output","allmesh_original.vtk"))
    end = time.time()
    func.GUI_setting()
    gmsh.fltk.run()
    gmsh.finalize()
    elapsed_time = end-start
    print("-------- Finished Make Mesh --------")
    print(f"elapsed time : {elapsed_time:.4f} s")

def deform():
    start=time.time()
    print("-------- Start Deform Mesh --------")
    filepath_original = myio.select_csv("original")
    filepath_target = myio.select_csv("target")
    mesh_deform = meshinfo.Mesh()
    global surfacenodes
    global surfacetriangles
    nodes_centerline, radius_list_original = myio.read_csv_centerline(filepath_original)
    nodes_targetcenterline, radius_list_target = myio.read_csv_centerline(filepath_target)
    filepath_surfacemesh_deformed, nodes_moved_dict, surfacetriangles_moved, mesh_deform = func.deform_surface(nodes_targetcenterline,  
                                                                                                        radius_list_target,
                                                                                                        nodes_centerline,
                                                                                                        surfacenodes,
                                                                                                        surfacetriangles,mesh_deform)
    if radius_list_target == None:
        radius_for_bgm = func.calc_radius(filepath_surfacemesh_deformed,filepath_target,nodes_targetcenterline)
        for i in range(1,config.num_of_surfacenodes+1):
            nodes_moved_dict[i].find_projectable_centerlineedge(nodes_targetcenterline)
            nodes_moved_dict[i].set_edgeradius(radius_for_bgm)
    else:
        radius_for_bgm = radius_list_target
    func.generate_pos_bgm(filepath_surfacemesh_deformed,nodes_targetcenterline, radius_for_bgm,"deform", 40) # ここの最後の引数、angle_classifyは
    mesh_deform, layernode_dict = func.make_prismlayer(nodes_moved_dict,surfacetriangles_moved,mesh_deform)  # いくつにするべきか
    mesh_deform = func.make_tetramesh(layernode_dict,mesh_deform,"deform")
    mesh_deform = func.naming_inlet_outlet(mesh_deform,nodes_targetcenterline)
    myio.write_msh_allmesh(mesh_deform,"deform")
    gmsh.initialize()    
    gmsh.merge(os.path.join("output", "allmesh_deform.msh"))
    gmsh.write(os.path.join("output","allmesh_deform.vtk"))
    end = time.time()
    elapsed_time = end-start
    func.GUI_setting()
    gmsh.fltk.run()
    gmsh.finalize()
    print("-------- Finished Deform Mesh --------")
    print("how many times edgeswap ", config.edgeswap_count)
    print(f"elapsed time : {elapsed_time:.4f} s")

def ask_which(did_meshing):
    which = input("Meshing or Deform? (m / d): ").strip().lower()
    try:
        if which == "m":
            meshing()
            did_meshing=True
        elif which == "d" and did_meshing == True:
            while True:
                edgeswap_input = input("Do edgeswap? (y/n): ").strip().lower()
                if edgeswap_input in ("y", "n"):
                    config.EDGESWAP = (edgeswap_input == "y")
                    with open("output/memo.txt", "a") as f:
                        f.write(f"edge_swap               : {config.EDGESWAP}\n")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
            deform()
        elif which == "d" and did_meshing == False:
            print("This procedure is currently in preparation. Please meshing first, sorry... ;;")
            sys.exit()
        else:
            print("Invalid input. Please enter 'm' for Meshing or 'd' for Deform.")
    except ValueError:
        print("Invalid input. Using default values.")
        traceback.print_exc()
    return did_meshing

if __name__ == "__main__":
    input_meshing_parameter()
    did_meshing = ask_which(did_meshing)
    did_meshing = ask_which(did_meshing)