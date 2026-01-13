"""
shape_library.py - Wireframe path generation for all shapes
Each shape returns polylines for GL_LINE_STRIP rendering
"""

import numpy as np


def generate_dna_helix(height=150, radius=40, turns=4, points_per_turn=50):
    """
    Two intertwined helical tubes with connecting rungs
    Returns polylines for both strands + rungs
    """
    polylines = []

    # Total points along helix
    num_points = turns * points_per_turn
    t = np.linspace(0, turns * 2 * np.pi, num_points)
    y = np.linspace(-height / 2, height / 2, num_points)

    # Strand 1
    x1 = radius * np.cos(t)
    z1 = radius * np.sin(t)
    strand1 = np.column_stack([x1, y, z1])
    polylines.append(strand1)

    # Strand 2 (180° offset)
    x2 = radius * np.cos(t + np.pi)
    z2 = radius * np.sin(t + np.pi)
    strand2 = np.column_stack([x2, y, z2])
    polylines.append(strand2)

    # Connecting rungs (every 10 points)
    for i in range(0, num_points, 10):
        rung = np.array([strand1[i], strand2[i]])
        polylines.append(rung)

    # Key vertices (where rungs connect)
    vertices = np.vstack([strand1[::10], strand2[::10]])

    return {
        'polylines': polylines,
        'vertices': vertices,
        'particle_paths': [strand1, strand2]  # Particles flow along strands
    }


def generate_torus_knot(p=3, q=2, R=60, r=20, num_points=500):
    """
    Mathematical torus knot - creates stunning 3D complexity
    p=3, q=2 creates classic trefoil knot
    """
    t = np.linspace(0, 2 * np.pi * q, num_points)

    x = (R + r * np.cos(p * t)) * np.cos(q * t)
    y = (R + r * np.cos(p * t)) * np.sin(q * t)
    z = r * np.sin(p * t)

    path = np.column_stack([x, y, z])

    return {
        'polylines': [path],
        'vertices': path[::50],  # Highlight every 50th point
        'particle_paths': [path]
    }


def generate_lorenz_attractor(num_points=2000, scale=3.0):
    """
    Chaotic butterfly attractor - mesmerizing in 3D
    """
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    dt = 0.01

    x, y, z = 0.1, 0.0, 0.0
    points = [[x * scale, y * scale, z * scale]]

    for _ in range(num_points - 1):
        dx = sigma * (y - x) * dt
        dy = (x * (rho - z) - y) * dt
        dz = (x * y - beta * z) * dt
        x, y, z = x + dx, y + dy, z + dz
        points.append([x * scale, y * scale, z * scale])

    path = np.array(points)

    # Center the attractor
    path -= path.mean(axis=0)

    return {
        'polylines': [path],
        'vertices': path[::100],  # Key points along attractor
        'particle_paths': [path]
    }


def generate_wireframe_cube(size=100):
    """
    12 edges + 8 glowing vertices
    Classic holographic containment grid look
    """
    s = size / 2

    # 8 vertices
    vertices = np.array([
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],  # Bottom
        [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]       # Top
    ])

    # 12 edges as index pairs
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom square
        (4, 5), (5, 6), (6, 7), (7, 4),  # Top square
        (0, 4), (1, 5), (2, 6), (3, 7)   # Vertical edges
    ]

    polylines = [np.array([vertices[i], vertices[j]]) for i, j in edges]

    # Particle paths along edges
    particle_paths = polylines.copy()

    return {
        'polylines': polylines,
        'vertices': vertices,
        'particle_paths': particle_paths
    }


def generate_icosphere(radius=70, subdivisions=2):
    """
    Geodesic sphere wireframe - more interesting than simple sphere
    """
    # Start with icosahedron vertices
    phi = (1 + np.sqrt(5)) / 2  # Golden ratio

    icosa_vertices = np.array([
        [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
        [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
        [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
    ])
    icosa_vertices = icosa_vertices / np.linalg.norm(icosa_vertices[0]) * radius

    # Icosahedron faces (triangles)
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
    ]

    # Subdivide faces for more detail
    vertices = icosa_vertices.tolist()
    current_faces = list(faces)

    vertex_cache = {}

    def get_middle_point(v1_idx, v2_idx):
        """Get or create middle point between two vertices"""
        key = tuple(sorted([v1_idx, v2_idx]))
        if key in vertex_cache:
            return vertex_cache[key]

        v1 = np.array(vertices[v1_idx])
        v2 = np.array(vertices[v2_idx])
        middle = (v1 + v2) / 2
        # Project onto sphere
        middle = middle / np.linalg.norm(middle) * radius

        new_idx = len(vertices)
        vertices.append(middle.tolist())
        vertex_cache[key] = new_idx
        return new_idx

    for _ in range(subdivisions):
        new_faces = []
        vertex_cache = {}

        for face in current_faces:
            v0, v1, v2 = face

            # Get middle points
            a = get_middle_point(v0, v1)
            b = get_middle_point(v1, v2)
            c = get_middle_point(v2, v0)

            # Create 4 new faces
            new_faces.append((v0, a, c))
            new_faces.append((v1, b, a))
            new_faces.append((v2, c, b))
            new_faces.append((a, b, c))

        current_faces = new_faces

    vertices = np.array(vertices)

    # Extract unique edges
    edges = set()
    for face in current_faces:
        for i in range(3):
            edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
            edges.add(edge)

    polylines = [np.array([vertices[i], vertices[j]]) for i, j in edges]

    return {
        'polylines': polylines,
        'vertices': vertices,
        'particle_paths': polylines[:30]  # Subset for particle paths
    }


def generate_mobius_strip(R=60, w=25, num_points=200):
    """
    Non-orientable surface - mind-bending topology
    """
    u = np.linspace(0, 2 * np.pi, num_points)

    # Create two edge curves of the strip
    polylines = []
    edges = []

    for v_offset in [-w / 2, w / 2]:
        v = v_offset
        x = (R + v * np.cos(u / 2)) * np.cos(u)
        y = (R + v * np.cos(u / 2)) * np.sin(u)
        z = v * np.sin(u / 2)
        edge = np.column_stack([x, y, z])
        edges.append(edge)
        polylines.append(edge)

    # Add cross-lines connecting edges
    for i in range(0, num_points, 10):
        cross = np.array([
            edges[0][i],
            edges[1][i]
        ])
        polylines.append(cross)

    return {
        'polylines': polylines,
        'vertices': edges[0][::20],
        'particle_paths': edges  # Particles along edges
    }


def generate_double_helix_torus(R=50, r=15, wraps=6, num_points=500):
    """
    Two helices wrapped around a torus - stunning complexity
    """
    t = np.linspace(0, 2 * np.pi, num_points)

    polylines = []
    strands = []

    for phase in [0, np.pi]:  # Two strands, opposite sides
        # Position along torus centerline
        cx = R * np.cos(t)
        cy = R * np.sin(t)

        # Helix offset perpendicular to centerline
        helix_angle = wraps * t + phase

        # Offset in radial and z directions
        offset_r = r * np.cos(helix_angle)
        offset_z = r * np.sin(helix_angle)

        # Apply offset radially outward
        x = cx + offset_r * np.cos(t)
        y = cy + offset_r * np.sin(t)
        z = offset_z

        strand = np.column_stack([x, y, z])
        strands.append(strand)
        polylines.append(strand)

    # Connecting rungs
    for i in range(0, num_points, 25):
        rung = np.array([strands[0][i], strands[1][i]])
        polylines.append(rung)

    return {
        'polylines': polylines,
        'vertices': strands[0][::50],
        'particle_paths': strands
    }


class ShapeLibrary:
    """Manager for all wireframe shapes"""

    def __init__(self):
        self.shapes = [
            ('DNA Double Helix', generate_dna_helix),
            ('Torus Knot', generate_torus_knot),
            ('Lorenz Attractor', generate_lorenz_attractor),
            ('Wireframe Cube', generate_wireframe_cube),
            ('Icosphere', generate_icosphere),
            ('Möbius Strip', generate_mobius_strip),
            ('Double Helix Torus', generate_double_helix_torus),
        ]
        self._cached_shapes = {}

    @property
    def shape_count(self):
        return len(self.shapes)

    def get_shape(self, index):
        """Get shape data by index, with caching"""
        if index not in self._cached_shapes:
            name, generator = self.shapes[index % len(self.shapes)]
            self._cached_shapes[index] = generator()
        return self._cached_shapes[index]

    def get_shape_name(self, index):
        """Get shape name by index"""
        return self.shapes[index % len(self.shapes)][0]

    def clear_cache(self):
        """Clear cached shape data"""
        self._cached_shapes = {}
