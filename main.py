import sys
import os
import traceback
import time
import gmsh
import func
import myio
import config
import meshinfo

surfacenodes          = None 
surfacetriangles      = None
filepath_vtk_original = None

# gmsh.model.mesh.classifySurfaces の引数はどう設定するべきか

def meshing():
    start=time.time()
    global surfacenodes
    global surfacetriangles
    global filepath_vtk_original
    mesh = meshinfo.Mesh() 
    filepath_centerline = myio.select_csv("original")
    filepath_stl = myio.select_stl()
    nodes_centerline, radius_list = myio.read_csv_centerline(filepath_centerline)
    if radius_list == None:
        radius_list = func.calc_radius(filepath_stl, filepath_centerline, nodes_centerline) #これは消す、変える。扁平な形状などは、最も直径が小さくなる部分で考えてメッシュサイズを設定する必要がある。
    myio.write_txt_parameter()
    func.generate_pos_bgm(filepath_stl, nodes_centerline, radius_list,"original", 40)  
    surfacenodes, surfacetriangles, filepath_vtk_original = func.make_surfacemesh(filepath_stl,"original")
    surfacenode_dict = func.correspond_surface_to_centerlinenode(surfacenodes, surfacetriangles, nodes_centerline, radius_list, mesh, filepath_vtk_original)
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

def deform(did_meshing):   
    start=time.time()
    print("-------- Start Deform Mesh --------")
    filepath_original = myio.select_csv("original")
    filepath_target = myio.select_csv("target")
    mesh_original = meshinfo.Mesh() # meshingをせずdeformを選択した場合のために追加。本質的には不要だがfunc.correspond_surface_to_centerlinenodeの引数に含める必要があるため書いておく。引数含め消せそうだったら消す
    mesh_deform = meshinfo.Mesh()
    if did_meshing == True:
        global surfacenodes                  
        global surfacetriangles
        global filepath_vtk_original               
    elif did_meshing == False:
        filepath_stl_original = myio.select_stl()  # 絶対パス
        filepath_vtk_original = myio.convert_stl_to_vtk(filepath_stl_original)  # 絶対パス
        surfacenodes, surfacetriangles = myio.read_vtk_surfacemesh(filepath_vtk_original)   
    nodes_centerline, radius_list_original     = myio.read_csv_centerline(filepath_original)
    nodes_targetcenterline, radius_list_target = myio.read_csv_centerline(filepath_target)
    # 左辺の返り値はこの後の処理では使わないが、meshingの方では返り値を使っているので仕方なく残している。消せそうだったら消す。
    surfacenode_dict = func.correspond_surface_to_centerlinenode(surfacenodes, surfacetriangles, nodes_centerline, radius_list_original, mesh_original, filepath_vtk_original)
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
            myio.input_meshing_parameter()
            meshing()
            did_meshing = True

        elif which == "d":
            if did_meshing == False:
                myio.input_meshing_parameter()
            myio.write_txt_parameter()    ### TODO : この段階だと num_of_centerlinenodes が NONE になっているので、どのタイミングでmemo.txtを書き出すかは改良の余地あり
            edgeswap_input = input("Do edgeswap? (y/n): ").strip().lower()
            if edgeswap_input in ("y", "n"):
                config.EDGESWAP = (edgeswap_input == "y")
                with open("output/memo.txt", "a") as f:
                    f.write(f"edge_swap               : {config.EDGESWAP}\n")
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
            deform(did_meshing)
            sys.exit()
        else:
            print("Invalid input. Please enter 'm' for Meshing or 'd' for Deform.")
    except ValueError:
        print("Invalid input. Using default values.")
        traceback.print_exc()
    return did_meshing

if __name__ == "__main__":
    did_meshing = False
    did_meshing = ask_which(did_meshing)
    did_meshing = ask_which(did_meshing)