"""
wireframe_renderer.py - OpenGL wireframe with glow effects
Multi-pass rendering for holographic appearance
"""

from OpenGL.GL import *
import numpy as np

from config import (
    WIREFRAME_LINE_WIDTH,
    WIREFRAME_GLOW_PASSES,
    WIREFRAME_GLOW_FALLOFF,
    WIREFRAME_GLOW_EXPANSION,
    PARTICLE_SIZE,
    COLOR_NEAR,
    COLOR_MID,
    COLOR_FAR,
    Z_NEAR_THRESHOLD,
    Z_FAR_THRESHOLD,
)


class WireframeRenderer:
    """OpenGL renderer for glowing wireframe meshes and particles"""

    def __init__(self):
        self.setup_opengl()

    def setup_opengl(self):
        """Initialize OpenGL state for holographic rendering"""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # ADDITIVE blending for glow
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glDisable(GL_DEPTH_TEST)  # Disable for additive transparency
        glClearColor(0, 0, 0, 1)

    def get_depth_color(self, z):
        """
        Calculate color based on Z depth
        Returns (r, g, b) normalized 0-1
        """
        # Normalize z to 0-1 range
        z_range = Z_NEAR_THRESHOLD - Z_FAR_THRESHOLD
        if z_range == 0:
            z_norm = 0.5
        else:
            z_norm = np.clip(
                (z - Z_FAR_THRESHOLD) / z_range, 0, 1
            )

        if z_norm < 0.5:
            # Far to mid: magenta to white
            t = z_norm * 2
            r = (COLOR_FAR[0] + (COLOR_MID[0] - COLOR_FAR[0]) * t) / 255
            g = (COLOR_FAR[1] + (COLOR_MID[1] - COLOR_FAR[1]) * t) / 255
            b = (COLOR_FAR[2] + (COLOR_MID[2] - COLOR_FAR[2]) * t) / 255
        else:
            # Mid to near: white to cyan
            t = (z_norm - 0.5) * 2
            r = (COLOR_MID[0] + (COLOR_NEAR[0] - COLOR_MID[0]) * t) / 255
            g = (COLOR_MID[1] + (COLOR_NEAR[1] - COLOR_MID[1]) * t) / 255
            b = (COLOR_MID[2] + (COLOR_NEAR[2] - COLOR_MID[2]) * t) / 255

        return (r, g, b)

    def render_wireframe(self, shape_data, rotation_angle=0, alpha_multiplier=1.0):
        """
        Render wireframe with multi-pass glow effect

        Args:
            shape_data: Dictionary with 'polylines' and 'vertices'
            rotation_angle: Rotation in radians
            alpha_multiplier: Overall alpha for transitions (0-1)
        """
        glPushMatrix()
        glRotatef(np.degrees(rotation_angle), 0, 1, 0)

        # Multi-pass rendering for glow (outer passes first)
        for glow_pass in range(WIREFRAME_GLOW_PASSES, 0, -1):
            # Outer passes are wider and dimmer (create glow)
            line_width = WIREFRAME_LINE_WIDTH * (
                WIREFRAME_GLOW_EXPANSION ** (glow_pass - 1)
            )
            alpha = (WIREFRAME_GLOW_FALLOFF ** (glow_pass - 1)) * alpha_multiplier

            glLineWidth(line_width)

            # Render all polylines
            for polyline in shape_data['polylines']:
                glBegin(GL_LINE_STRIP)
                for point in polyline:
                    color = self.get_depth_color(point[2])
                    glColor4f(color[0], color[1], color[2], alpha)
                    glVertex3f(point[0], point[1], point[2])
                glEnd()

        # Render emphasized vertices (brightest points)
        if 'vertices' in shape_data and len(shape_data['vertices']) > 0:
            glPointSize(WIREFRAME_LINE_WIDTH * 2)
            glBegin(GL_POINTS)
            for vertex in shape_data['vertices']:
                color = self.get_depth_color(vertex[2])
                glColor4f(color[0], color[1], color[2], alpha_multiplier)
                glVertex3f(vertex[0], vertex[1], vertex[2])
            glEnd()

        glPopMatrix()

    def render_particles(self, particles, rotation_angle=0, alpha_multiplier=1.0):
        """
        Render sparse particle aura

        Args:
            particles: list of {'position': [x,y,z], 'trail': [[x,y,z], ...]}
            rotation_angle: Rotation in radians
            alpha_multiplier: Overall alpha for transitions (0-1)
        """
        glPushMatrix()
        glRotatef(np.degrees(rotation_angle), 0, 1, 0)

        for particle in particles:
            pos = particle['position']
            color = self.get_depth_color(pos[2])

            # Render particle with glow (multiple passes)
            for glow_pass in range(2, 0, -1):
                point_size = PARTICLE_SIZE * (1.5 ** (glow_pass - 1))
                alpha = (0.6 ** (glow_pass - 1)) * alpha_multiplier

                glPointSize(point_size)
                glBegin(GL_POINTS)
                glColor4f(color[0], color[1], color[2], alpha)
                glVertex3f(pos[0], pos[1], pos[2])
                glEnd()

            # Render trail if exists
            if 'trail' in particle and len(particle['trail']) > 1:
                glLineWidth(1.5)
                glBegin(GL_LINE_STRIP)
                trail_len = len(particle['trail'])
                for i, trail_pos in enumerate(particle['trail']):
                    # Trail fades out toward the end
                    trail_alpha = 0.7 * (i / trail_len) * alpha_multiplier
                    trail_color = self.get_depth_color(trail_pos[2])
                    glColor4f(
                        trail_color[0],
                        trail_color[1],
                        trail_color[2],
                        trail_alpha
                    )
                    glVertex3f(trail_pos[0], trail_pos[1], trail_pos[2])
                glEnd()

        glPopMatrix()

    def render_dissolve_effect(self, shape_data, rotation_angle, progress):
        """
        Render wireframe dissolving into particles

        Args:
            shape_data: Shape to dissolve
            rotation_angle: Current rotation
            progress: 0-1 dissolve progress (0=solid, 1=dissolved)
        """
        alpha = 1.0 - progress

        # Render with decreasing alpha
        self.render_wireframe(shape_data, rotation_angle, alpha)

        # Add some scatter particles during dissolve
        if progress > 0.2:
            scatter_alpha = (progress - 0.2) / 0.8
            glPushMatrix()
            glRotatef(np.degrees(rotation_angle), 0, 1, 0)

            # Emit particles from vertices
            if 'vertices' in shape_data:
                glPointSize(PARTICLE_SIZE)
                glBegin(GL_POINTS)
                for vertex in shape_data['vertices']:
                    # Random offset based on progress
                    offset = np.random.randn(3) * progress * 50
                    pos = vertex + offset
                    color = self.get_depth_color(pos[2])
                    glColor4f(
                        color[0], color[1], color[2],
                        scatter_alpha * np.random.uniform(0.3, 1.0)
                    )
                    glVertex3f(pos[0], pos[1], pos[2])
                glEnd()

            glPopMatrix()

    def render_reform_effect(self, shape_data, rotation_angle, progress):
        """
        Render wireframe reforming from particles

        Args:
            shape_data: Shape to reform into
            rotation_angle: Current rotation
            progress: 0-1 reform progress (0=particles, 1=solid)
        """
        alpha = progress

        # Render with increasing alpha
        self.render_wireframe(shape_data, rotation_angle, alpha)

        # Converging particles during reform
        if progress < 0.8:
            scatter_alpha = 1.0 - (progress / 0.8)
            glPushMatrix()
            glRotatef(np.degrees(rotation_angle), 0, 1, 0)

            # Particles converging to vertices
            if 'vertices' in shape_data:
                glPointSize(PARTICLE_SIZE)
                glBegin(GL_POINTS)
                for vertex in shape_data['vertices']:
                    # Offset decreases as progress increases
                    offset = np.random.randn(3) * (1 - progress) * 80
                    pos = vertex + offset
                    color = self.get_depth_color(pos[2])
                    glColor4f(
                        color[0], color[1], color[2],
                        scatter_alpha * np.random.uniform(0.3, 1.0)
                    )
                    glVertex3f(pos[0], pos[1], pos[2])
                glEnd()

            glPopMatrix()
