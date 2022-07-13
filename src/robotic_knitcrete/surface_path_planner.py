from genericpath import exists
from .planner_mesh import PlannerMesh
from compas.datastructures import Network
from compas.geometry import Frame, Vector, Point
from compas.geometry import cross_vectors, distance_point_point
import time

class SurfacePathPlanner():
    def __init__(self):
        self.mesh = None
        self.network = Network(name="network")
        self.network.path = []
        self.network.default_node_attributes = {
            'x':0, 'y':0, 'z':0,
            'vx':0, 'vy':0, 'vz':0,
            'neighbors':0, 'number_of_neighbors':0,
            'frame':None,
            'path_key':None
        }

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
        color = [0,0,0]
        attr_dict.update({
            'x':point[0], 'y':point[1], 'z':point[2],
            'vx':normal[0], 'vy':normal[1], 'vz':normal[2],
            'r':color[0], 'g':color[1], 'b':color[2],
            'neighbors':neighbors,
            'number_of_neighbors':len(neighbors),
            'frame':None,
            'path_key':None
        })
        attr_dict.update(**kwattr)
        self.network.add_node(key=index, attr_dict=attr_dict)

    def add_edge(self, start, end):
        new_edge = self.network.add_edge(start, end)
        if self.network.node_attribute(key=start, name='frame') is None:
            self.set_node_frame_from_edge(start, new_edge)
        self.set_node_frame_from_edge(end, new_edge)
        
    def set_node_frame_from_edge(self, node, edge):
        zvec = Vector.from_data(self.network.node_attributes(key=node, names=['vx','vy','vz']))
        xvec = self.network.edge_vector(edge[0], edge[1])
        yvec = cross_vectors(xvec, -zvec)
        frame = Frame(Point.from_data(self.network.node_coordinates(node)),
                      self.network.edge_vector(edge[0], edge[1]),
                      yvec)
        self.network.node_attribute(key=node, name='frame', value=frame)

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
            
        nodes = self.network.nodes_where(conditions=conditions)
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