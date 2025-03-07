cmake_minimum_required(VERSION 3.12 FATAL_ERROR)

project(TubesFromSplines)

find_package(VTK COMPONENTS 
  CommonColor
  CommonComputationalGeometry
  CommonCore
  CommonDataModel
  FiltersCore
  FiltersSources
  InteractionStyle
  RenderingContextOpenGL2
  RenderingCore
  RenderingFreeType
  RenderingGL2PSOpenGL2
  RenderingOpenGL2
  IOGeometry
)

if (NOT VTK_FOUND)
  message(FATAL_ERROR "TubesFromSplines: Unable to find the VTK build folder.")
endif()

# Prevent a "command line is too long" failure in Windows.
set(CMAKE_NINJA_FORCE_RESPONSE_FILE "ON" CACHE BOOL "Force Ninja to use response files.")

add_executable(TubesFromSplines MACOSX_BUNDLE TubesFromSplines.cxx)

target_link_libraries(TubesFromSplines PRIVATE 
  VTK::CommonColor
  VTK::CommonComputationalGeometry
  VTK::CommonCore
  VTK::CommonDataModel
  VTK::FiltersCore
  VTK::FiltersSources
  VTK::InteractionStyle
  VTK::RenderingContextOpenGL2
  VTK::RenderingCore
  VTK::RenderingFreeType
  VTK::RenderingGL2PSOpenGL2
  VTK::RenderingOpenGL2
  VTK::IOGeometry  
)

vtk_module_autoinit(
  TARGETS TubesFromSplines
  MODULES 
    VTK::CommonColor
    VTK::CommonComputationalGeometry
    VTK::CommonCore
    VTK::CommonDataModel
    VTK::FiltersCore
    VTK::FiltersSources
    VTK::InteractionStyle
    VTK::RenderingContextOpenGL2
    VTK::RenderingCore
    VTK::RenderingFreeType
    VTK::RenderingGL2PSOpenGL2
    VTK::RenderingOpenGL2
    VTK::IOGeometry  
)
set(CMAKE_PREFIX_PATH "C:/ut/vtk/install") 