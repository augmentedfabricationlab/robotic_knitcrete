from compas.datastructures import Mesh, Network
from compas.geometry import Frame, Vector, Line, Point
from compas.geometry import cross_vectors, distance_point_point
import time

class SurfacePathPlanner():
    def __init__(self):
        self.mesh = None
        self.network = Network(name="network")
        self.network.default_node_attributes = {
            'x':0, 'y':0, 'z':0,
            'vx':0, 'vy':0, 'vz':0,
            'neighbors':0, 'number_of_neighbors':0
        }

    def set_quad_mesh(self, mesh):
        self.mesh = mesh
        return self.mesh

    def create_quad_mesh_from_surface(self, surface, nu, nv):
        self.mesh = surface.to_mesh(nu, nv)
        return self.mesh

    def set_network_nodes(self):
        for index in self.mesh.faces():
            self.add_node(index)

    def add_node(self, index, attr_dict={}, **kwattr):
        point = self.mesh.face_center(index)
        normal = self.mesh.face_normal(index)
        neighbors = self.mesh.face_neighbors(index)
        attr_dict.update({
            'x':point[0], 'y':point[1], 'z':point[2],
            'vx':normal[0], 'vy':normal[1], 'vz':normal[2],
            'neighbors':neighbors,
            'number_of_neighbors':len(neighbors)
        })
        attr_dict.update(**kwattr)
        self.network.add_node(key=index, attr_dict=attr_dict)

    def lowest_axis_path(self, orientation, image_values):
        """Creates a tool-path based on the given mesh topology.

        Args:
            mesh (compas mesh): Description of `mesh`
            orientation (int): X-axis = 1, Y-axis = 2, Z-axis =3
        """
        print('t0', time.time())
        _orientation = ['x', 'y', 'z']
        if self.mesh == None:
            raise ValueError
        if self.network == None:
            self.set_network_nodes()
        
        n = 0 # Number of interruptions

        # Getting the starting point
        
        cornernodes = self.network.nodes_where(conditions={'number_of_neighbors':2})
        if cornernodes != []:
            vals = [self.network.node_attribute(key=k, name=_orientation[orientation]) for k in cornernodes]
            minimum_orientation = min(vals)
            current = list(self.network.nodes_where(conditions= {
                _orientation[orientation]:minimum_orientation
            }))[0]
        else:
            # In case there are no corners, start the path on the face center with the lowest x/y/z value
            current = 0
        # Path finding process
        for index in self.mesh.faces():
            # Look for the neighbor with the lowest x/y/z
            neighbornodes = {}
            for i in self.network.node_attribute(key=current, name='neighbors'):
                if len(self.network.connected_edges(key=i))==0:
                    neighbornodes.update({self.network.node_attribute(key=i, name=_orientation[orientation]): i})
            # If neighbors found then find the closest one based on orientation
            if neighbornodes != {}:
                following = neighbornodes[min(neighbornodes.keys())]
                # Draw a line between the current and following face centerpoints
                self.network.add_edge(current, following)
            # If the face doesn't have free neighbors
            else:
                # But has remaining unconnected nodes
                if self.network.number_of_nodes()-1 != self.network.number_of_edges():
                    # Move to the closest available face centerpoint
                    following = self.move_to_closest(current)
                    # Draw a line between the current and the following face
                    self.network.add_edge(current, following)
                    n += 1
            current = following
        return self.network, n

    def move_to_closest(self, current):
        current_point = Point.from_data(self.network.node_coordinates(key=current))
        distances = {}
        for j in self.network.nodes():
            if len(self.network.connected_edges(key=j)) == 0:
                d = distance_point_point(current_point, Point.from_data(self.network.node_coordinates(key=j)))
                distances.update({d:j})
        min_d = min(distances.keys())
        following = distances[min_d]       
        return following