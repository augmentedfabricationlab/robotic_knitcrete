import math

from compas.utilities import linspace
from .planner_mesh import PlannerMesh
from compas.datastructures import Network
from compas.geometry import Frame, Vector, Point
from compas.geometry import Translation
from compas.geometry import cross_vectors, distance_point_point
from compas.colors import Color, ColorMap

class SurfacePathPlanner():
    def __init__(self):
        self.mesh = None
        self.network = Network(name="network")
        self.network.path = []
        self.network.default_node_attributes = {
            'x':0, 'y':0, 'z':0,
            'vx':0, 'vy':0, 'vz':0,
            'r':0, 'g':0, 'b':0,
            'color': None,
            'neighbors':0, 'number_of_neighbors':0,
            'frame':None,
            'thickness':0.0,
            'radius':0.0,
            'area':0.0,
            'velocity':0.0,
            'nozzle_distance':0.0,
            'tool_frame':None
        }
        self.fabrication_parameters = {
            'material_flowrate':500.0,          # l/hr
            'thickness_range':[0.008, 0.022],     # m
            'radius_range':[0.040, 0.075],        # m
            'distance_range':[0.100, 0.300],      # m
            'measured_radii':[0.0625, 0.075],        # [m]
            'measured_distances':[0.150, 0.300],  # [m]
            'measured_thicknesses':[0.012, 0.009], # [m]
        }
        self.color_map=None
        self.thickness_map=None

    def set_quad_mesh(self, mesh):
        self.mesh = mesh
        return self.mesh

    def set_quad_mesh_from_rhinomesh(self, rhinomesh):
        self.mesh = PlannerMesh.from_rhinomesh(rhinomesh)
        return self.mesh

    def create_quad_mesh_from_surface(self, surface, nu, nv):
        self.mesh = PlannerMesh.from_surface(surface, nu, nv)
        return self.mesh

    def set_network_nodes(self):
        for index in self.mesh.faces():
            self.add_node(index)

    def add_node(self, index, attr_dict={}, **kwattr):
        point = self.mesh.face_center(index)
        normal = self.mesh.face_normal(index)
        neighbors = self.mesh.face_neighbors(index)
        color = self.mesh.face_color(index)
        attr_dict.update({
            'x':point[0], 'y':point[1], 'z':point[2],
            'vx':normal[0], 'vy':normal[1], 'vz':normal[2],
            'r':color.rgb255[0], 'g':color.rgb255[1], 'b':color.rgb255[2],
            'color': color,
            'neighbors':neighbors,
            'number_of_neighbors':len(neighbors),
            'frame':None,
            'thickness':0.0,
            'radius':0.0,
            'area':0.0,
            'velocity':0.0,
            'nozzle_distance':0.0,
            'tool_frame':None
        })
        attr_dict.update(**kwattr)
        self.network.add_node(key=index, attr_dict=attr_dict)

    def add_edge(self, start, end):
        new_edge = self.network.add_edge(start, end)
        # if self.network.node_attribute(key=start, name='frame') is None:
        #     self.set_node_frame_from_edge(start, new_edge)
        # self.set_node_frame_from_edge(end, new_edge)
        if self.network.node_attribute(key=start, name='frame') is None:
            self.set_node_frame(start)
        self.set_node_frame(end)
        
    def set_node_frame_from_edge(self, node, edge):
        zvec = Vector.from_data(self.network.node_attributes(key=node, names=['vx','vy','vz']))
        xvec = self.network.edge_vector(edge[0], edge[1])
        yvec = cross_vectors(xvec, -zvec)
        frame = Frame(Point.from_data(self.network.node_coordinates(node)),
                      self.network.edge_vector(edge[0], edge[1]),
                      yvec)
        self.network.node_attribute(key=node, name='frame', value=frame)

    def set_node_frame(self, node):
        norm = Vector.from_data(self.network.node_attributes(key=node, names=['vx','vy','vz']))
        v1 = cross_vectors(norm, Vector.Yaxis())
        v2 = cross_vectors(norm,v1)
        frame = Frame(Point.from_data(self.network.node_coordinates(node)), v1, v2)
        self.network.node_attribute(key=node, name='frame', value=frame)
        return frame

    def get_node(self, **kwargs):
        """
        **kwargs can include any of the following:
        - any condition to find nodes based on network.default_node_attributes
        - 'orientation' : either 'x', 'y', or 'z'
        - 'index' : 0 or 1 for minimum or maximum value
        """
        conditions = {}
        func_dict = {0:min,1:max}
        for key, value in kwargs.items():
            if key in self.network.default_node_attributes.keys():
                conditions.update({key:value})
            elif key is 'index':
                func = func_dict[value]
        if 'orientation' not in locals():
            orientation = None
        if 'index' not in locals():
            func = None
            
        nodes = self.network.nodes_where(conditions)
        if nodes != []:
            if orientation is not None:
                vals = [self.network.node_attribute(key=k, name=orientation) for k in nodes]
                if func is not None:
                    fval = func(vals)
                    return (nodes)[vals.index(fval)]
                else:
                    return list(nodes)[0]
            else:
                return list(nodes)[0]
        else:
            # In case there are valid nodes, returns Nonetype
            return None

    def lowest_axis_path(self, orientation):
        """Creates a tool-path based on the given mesh topology.

        Args:
            mesh (compas mesh): Description of `mesh`
            orientation (int): X-axis = 1, Y-axis = 2, Z-axis =3
        """
        if self.mesh == None:
            raise ValueError
        if self.network == None:
            self.set_network_nodes()
        
        n = 0 # Number of interruptions        
        current = self.get_node(number_of_neighbors=2, orientation=orientation, index=0)
        # Getting the starting point
        print(current)
        # Path finding process
        for index in self.mesh.faces():
            # Look for the neighbor with the lowest x/y/z
            self.network.path.append(current)
            neighbornodes = {}
            for i in self.network.node_attribute(key=current, name='neighbors'):
                if len(self.network.connected_edges(key=i))==0:
                    neighbornodes.update({i:self.network.node_attribute(key=i, name=orientation)})
            # If neighbors found then find the closest one based on orientation
            if neighbornodes != {}:
                following = list(neighbornodes.keys())[list(neighbornodes.values()).index(min(list(neighbornodes.values())))]
                # Draw a line between the current and following face centerpoints
                self.add_edge(current, following)
            # If the face doesn't have free neighbors
            else:
                # But has remaining unconnected nodes
                if self.network.number_of_nodes()-1 != self.network.number_of_edges():
                    # Move to the closest available face centerpoint
                    following = self.move_to_closest(current)
                    # Draw a line between the current and the following face
                    self.add_edge(current, following)
                    n += 1
            current = following
        return self.network, n

    def move_to_closest(self, current):
        current_point = Point.from_data(self.network.node_coordinates(key=current))
        distances = {}
        nodes = [key for key in self.network.nodes() if len(self.network.connected_edges(key))==0]
        # print(nodes)
        for j in nodes:
            d = distance_point_point(current_point, Point.from_data(self.network.node_coordinates(key=j)))
            distances.update({j:d})
        min_d = min(distances.values())
        following = distances.keys()[distances.values().index(min_d)]
        return following

    def set_fabrication_parameters(self, *args, **kwargs):
        '''
        *args : dict {}
        **kwargs: keyword arguments and values
        '''
        self.fabrication_parameters.update(args)
        for key, value in kwargs.items():
            self.fabrication_parameters[key] = value

    def set_color_map(self, colors=None, color_map=None, rangetype="full"):
        if colors is not None:
            if len(colors)==1:
                color_map = ColorMap.from_color(colors[0], rangetype)
            elif len(colors)==2:
                color_map = ColorMap.from_two_colors(*colors)
            elif len(colors)==3:
                color_map = ColorMap.from_three_colors(*colors)
            elif len(colors)>3:
                raw_colors = []
                for color in colors:
                    raw_colors.append(color.rgb())
                color_map = ColorMap(raw_colors)
        self.color_map = color_map

    def set_thickness_map(self, thicknesses):
        thickness_map = []
        if len(thicknesses)==2:
            for i in linspace(0,1.0,256):
                thickness_map.append(thicknesses[0]*(1-i)+thicknesses[1]*i)
        elif len(thicknesses)==3:
            for i in linspace(0,1.0,128):
                thickness_map.append(thicknesses[0]*(1-i)+thicknesses[1]*i)
            for i in linspace(0,1.0,128):
                thickness_map.append(thicknesses[1]*(1-i)+thicknesses[2]*i)
        elif len(thicknesses)>3:
            thickness_map.extend(thicknesses)
        self.thickness_map = thickness_map

    def calculate_fabrication_parameters(self, num_layers, n_layer, measured=True):
        for node in self.network.nodes():
            self.set_node_area_radius(node)
            self.set_node_thickness(node)
            self.set_node_distance(node, num_layers, n_layer, measured)
            self.set_node_velocity(node)

    def set_node_area_radius(self, node):
        area = self.mesh.face_area(node)
        self.network.node_attribute(key=node, name='area', value=area)
        self.network.node_attribute(key=node, name='radius', value=math.sqrt(area/math.pi))

    def set_node_distance(self, node, num_layers, n_layer, measured=True):
        radius = self.network.node_attribute(key=node, name='radius')
        if measured:
            drange = self.fabrication_parameters['measured_distances']
            rrange = self.fabrication_parameters['measured_radii']
        else:
            drange = self.fabrication_parameters['distance_range']
            rrange = self.fabrication_parameters['radius_range']

        distance = ((drange[1]-drange[0])/(rrange[1]-rrange[0]))*radius
        distance_thickness = self.network.node_attribute(key=node, name='thickness')*(n_layer/num_layers)
        self.network.node_attribute(key=node, name='distance', value=distance)
        frame = self.network.node_attribute(node, 'frame')
        T = Translation.from_vector(frame.zaxis*-(distance+distance_thickness))
        tool_frame = frame.transformed(T)
        self.network.node_attribute(key=node, name='tool_frame', value=tool_frame)

    def set_node_thickness(self, node):
        node_color = self.network.node_attribute(node, 'color').rgb255
        n=0
        while n < 255:
            ncol = self.network.node_attribute(n, 'color').rgb255
            if ncol == node_color:
                break
            n+=1
        t = self.thickness_map[n]
        self.network.node_attribute(key=node, name='thickness', value=t)

    def set_node_velocity(self, node):
        volume = self.network.node_attribute(key=node, name='area')*self.network.node_attribute(key=node, name='thickness')
        velocity = self.network.node_attribute(key=node, name='radius')/(volume/(self.fabrication_parameters['material_flowrate']/60))
        self.network.node_attribute(key=node, name='velocity', value=velocity)
    
    def node_color(self, node, color_type='rgb'):
        return self.network.node_attribute(node, 'color').rgb255
