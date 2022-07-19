from compas.datastructures import Mesh
from compas.geometry import distance_point_point
from itertools import product
from compas.colors import Color

class PlannerMesh(Mesh):
    def __init__(self, name=None, default_vertex_attributes=None, default_edge_attributes=None, default_face_attributes=None):
        _default_vertex_attributes = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'r':0.0, 'g':0.0, 'b':0.0}
        _default_edge_attributes = {}
        _default_face_attributes = {}
        if default_vertex_attributes:
            _default_vertex_attributes.update(default_vertex_attributes)
        if default_edge_attributes:
            _default_edge_attributes.update(default_edge_attributes)
        if default_face_attributes:
            _default_face_attributes.update(default_face_attributes)
        super(PlannerMesh, self).__init__(name=name or 'Mesh',
                                   default_vertex_attributes=_default_vertex_attributes,
                                   default_edge_attributes=_default_edge_attributes,
                                   default_face_attributes=_default_face_attributes)
    @classmethod
    def from_rhinomesh(cls, rhinomesh):
        """Convert a Rhino mesh to a COMPAS mesh.
        Parameters
        ----------
        cls: :class:`~compas.datastructures.Mesh`, optional
            The mesh type.
        Returns
        -------
        :class:`~compas.datastructures.Mesh`
            The equivalent COMPAS mesh.
        """
        mesh = cls()
        vertexcolors = rhinomesh.geometry.VertexColors
        if len(vertexcolors) == 0:
            for vertex in rhinomesh.geometry.Vertices:
                mesh.add_vertex(attr_dict=dict(x=float(vertex.X), y=float(vertex.Y), z=float(vertex.Z),
                                               r=255, g=255, b=255))
        else:
            for i, vertex in enumerate(rhinomesh.geometry.Vertices):
                mesh.add_vertex(attr_dict=dict(x=float(vertex.X), y=float(vertex.Y), z=float(vertex.Z),
                                               r=vertexcolors[i].R, g=vertexcolors[i].G, b=vertexcolors[i].B))

        for face in rhinomesh.geometry.Faces:
            if face.A == face.D or face.C == face.D:
                mesh.add_face([face.A, face.B, face.C])
            else:
                mesh.add_face([face.A, face.B, face.C, face.D])

        mesh.name = rhinomesh.name
        return mesh

    @classmethod
    def from_surface(cls, surface, nu=100, nv=None):
        nv = nv or nu
        vertices = [surface.point_at(i, j) for i, j in product(surface.u_space(nu + 1), surface.v_space(nv + 1))]
        faces = [[
            i * (nv + 1) + j,
            (i + 1) * (nv + 1) + j,
            (i + 1) * (nv + 1) + j + 1,
            i * (nv + 1) + j + 1
        ] for i, j in product(range(nu), range(nv))]
        return cls.from_vertices_and_faces(vertices, faces)

    def vertex_color(self, key, color_type='rgb'):
        color = Color.from_rgb255(
            self.vertex_attribute(key, 'r'),
            self.vertex_attribute(key, 'g'),
            self.vertex_attribute(key, 'b')
        )
        return color

    def face_color (self, key, color_type='rgb'):
        vertices = self.face_vertices(key)
        # center = self.face_center(key)
        vtx_colors = [self.vertex_color(vertex) for vertex in vertices]
        c12 = Color(vtx_colors[0].r*0.5+vtx_colors[1].r*0.5, vtx_colors[0].g*0.5+vtx_colors[1].g*0.5, vtx_colors[0].b*0.5+vtx_colors[1].b*0.5)
        c34 = Color(vtx_colors[2].r*0.5+vtx_colors[3].r*0.5, vtx_colors[2].g*0.5+vtx_colors[3].g*0.5, vtx_colors[2].b*0.5+vtx_colors[3].b*0.5)
        c1234 = Color(c12.r*0.5+c34.r*0.5, c12.g*0.5+c34.g*0.5, c12.b*0.5+c34.b*0.5)
        
        return vtx_colors[0]