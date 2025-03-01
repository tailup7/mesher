from dataclasses import dataclass,field

@dataclass
class Mesh:
    num_of_nodes:int = 0
    nodes:list = field(default_factory=list)
    num_of_elements:int = 0
    triangles_WALL:list = field(default_factory=list)
    triangles_INLET:list = field(default_factory=list)
    triangles_OUTLET:list = field(default_factory=list)
    quadrangles_INLET:list = field(default_factory=list)
    quadrangles_OUTLET:list = field(default_factory=list)
    tetras_INTERNAL:list = field(default_factory=list)
    prisms_INTERNAL:list = field(default_factory=list)
    prisms_rearray_INTERNAL:list[list] = field(default_factory=list)