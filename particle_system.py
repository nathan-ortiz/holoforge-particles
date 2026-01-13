"""
particle_system.py - Sparse particles that flow along wireframes
Creates an ethereal aura effect around the wireframe shapes
"""

import numpy as np

from config import (
    PARTICLE_COUNT,
    PARTICLE_SPEED,
    PARTICLE_ORBIT_RADIUS,
    PARTICLE_TRAIL_LENGTH,
    HAND_FORCE_RADIUS,
)


class ParticleSystem:
    """Sparse particle system that flows along wireframe paths"""

    def __init__(self, paths, count=PARTICLE_COUNT):
        """
        Initialize particles distributed along wireframe paths

        Args:
            paths: list of numpy arrays, each [N, 3] defining a path
            count: number of particles to create
        """
        self.paths = paths if paths else []
        self.count = count
        self.particles = []

        self._initialize_particles()

    def _initialize_particles(self):
        """Distribute particles along paths"""
        if not self.paths:
            return

        particles_per_path = max(1, self.count // len(self.paths))
        extra_particles = self.count - (particles_per_path * len(self.paths))

        for path_idx, path in enumerate(self.paths):
            path_length = len(path)
            if path_length < 2:
                continue

            # Add extra particles to first paths
            num_particles = particles_per_path
            if path_idx < extra_particles:
                num_particles += 1

            for _ in range(num_particles):
                # Random position along path
                t = np.random.uniform(0, path_length - 1)
                idx = int(t)
                frac = t - idx

                if idx < path_length - 1:
                    pos = path[idx] * (1 - frac) + path[idx + 1] * frac
                else:
                    pos = path[idx].copy()

                # Add orbit offset perpendicular to path
                offset = np.random.randn(3) * PARTICLE_ORBIT_RADIUS
                pos = pos + offset

                self.particles.append({
                    'position': pos.copy(),
                    'path_index': path_idx,
                    't': t,
                    'speed': np.random.uniform(0.8, 1.2) * PARTICLE_SPEED,
                    'orbit_phase': np.random.uniform(0, 2 * np.pi),
                    'orbit_speed': np.random.uniform(1.5, 2.5),
                    'orbit_radius': np.random.uniform(0.5, 1.5) * PARTICLE_ORBIT_RADIUS,
                    'trail': [pos.copy() for _ in range(PARTICLE_TRAIL_LENGTH)]
                })

    def update(self, dt, hand_force=None):
        """
        Update particle positions

        Args:
            dt: Delta time in seconds
            hand_force: Optional dict with 'position', 'gesture', 'strength'
        """
        for particle in self.particles:
            if particle['path_index'] >= len(self.paths):
                continue

            path = self.paths[particle['path_index']]
            path_length = len(path)

            if path_length < 2:
                continue

            # Update trail (shift positions)
            particle['trail'].pop(0)
            particle['trail'].append(particle['position'].copy())

            # Move along path
            particle['t'] += particle['speed'] * dt
            if particle['t'] >= path_length - 1:
                particle['t'] = particle['t'] % (path_length - 1)

            t = particle['t']
            idx = int(t)
            frac = t - idx

            # Interpolate position on path
            if idx < path_length - 1:
                base_pos = path[idx] * (1 - frac) + path[idx + 1] * frac
            else:
                base_pos = path[idx].copy()

            # Orbit motion around the path
            particle['orbit_phase'] += dt * particle['orbit_speed']
            orbit_radius = particle['orbit_radius']

            # Create orbit in a plane perpendicular to path direction
            if idx < path_length - 1:
                path_dir = path[idx + 1] - path[idx]
                path_dir_norm = np.linalg.norm(path_dir)
                if path_dir_norm > 0.001:
                    path_dir = path_dir / path_dir_norm
                else:
                    path_dir = np.array([0, 1, 0])
            else:
                path_dir = np.array([0, 1, 0])

            # Create perpendicular vectors for orbit plane
            if abs(path_dir[0]) < 0.9:
                perp1 = np.cross(path_dir, np.array([1, 0, 0]))
            else:
                perp1 = np.cross(path_dir, np.array([0, 1, 0]))
            perp1 = perp1 / (np.linalg.norm(perp1) + 0.0001)
            perp2 = np.cross(path_dir, perp1)

            orbit = (
                perp1 * np.cos(particle['orbit_phase']) * orbit_radius +
                perp2 * np.sin(particle['orbit_phase']) * orbit_radius
            )

            new_pos = base_pos + orbit

            # Apply hand force if present
            if hand_force is not None:
                hand_pos = np.array(hand_force['position'])
                delta = new_pos - hand_pos
                distance = np.linalg.norm(delta)

                if distance < HAND_FORCE_RADIUS and distance > 1:
                    force_dir = delta / distance
                    force_factor = 1 - distance / HAND_FORCE_RADIUS

                    if hand_force['gesture'] == 'scatter':
                        # Push particles away from hand
                        new_pos += force_dir * hand_force['strength'] * force_factor * dt * 60
                    elif hand_force['gesture'] == 'attract':
                        # Pull particles toward hand (gentler)
                        new_pos -= force_dir * hand_force['strength'] * force_factor * 0.5 * dt * 60

            particle['position'] = new_pos

    def set_paths(self, new_paths):
        """
        Update paths (for shape transitions)

        Args:
            new_paths: New list of path arrays
        """
        self.paths = new_paths if new_paths else []

        if not self.paths:
            return

        # Redistribute particles to new paths
        for i, particle in enumerate(self.particles):
            new_path_idx = i % len(self.paths)
            particle['path_index'] = new_path_idx

            path = self.paths[new_path_idx]
            path_length = len(path)

            if path_length > 1:
                particle['t'] = np.random.uniform(0, path_length - 1)
            else:
                particle['t'] = 0

    def get_particles_for_render(self):
        """Get particle data formatted for renderer"""
        return self.particles

    def apply_transition_scatter(self, progress):
        """
        Scatter particles during shape transition

        Args:
            progress: 0-1 transition progress
        """
        scatter_amount = progress * 100

        for particle in self.particles:
            offset = np.random.randn(3) * scatter_amount * 0.1
            particle['position'] += offset

    def reset_to_paths(self):
        """Reset particles to their path positions"""
        for particle in self.particles:
            if particle['path_index'] >= len(self.paths):
                continue

            path = self.paths[particle['path_index']]
            path_length = len(path)

            if path_length < 2:
                continue

            t = particle['t']
            idx = int(t)
            frac = t - idx

            if idx < path_length - 1:
                base_pos = path[idx] * (1 - frac) + path[idx + 1] * frac
            else:
                base_pos = path[idx].copy()

            # Keep orbit offset
            orbit_radius = particle['orbit_radius']
            orbit = np.random.randn(3)
            orbit = orbit / (np.linalg.norm(orbit) + 0.0001) * orbit_radius

            particle['position'] = base_pos + orbit

            # Reset trail to current position
            particle['trail'] = [
                particle['position'].copy()
                for _ in range(PARTICLE_TRAIL_LENGTH)
            ]
