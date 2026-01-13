"""
transition_manager.py - Shape cycling with dissolve/reform effects
Manages smooth transitions between wireframe shapes
"""

import time

from config import SHAPE_HOLD_TIME, DISSOLVE_TIME, REFORM_TIME


class TransitionState:
    """Enumeration of transition states"""
    HOLDING = 'holding'
    DISSOLVING = 'dissolving'
    REFORMING = 'reforming'


class TransitionManager:
    """Manages shape transitions with dissolve and reform effects"""

    def __init__(self, shape_library, particle_system):
        """
        Initialize transition manager

        Args:
            shape_library: ShapeLibrary instance
            particle_system: ParticleSystem instance
        """
        self.shape_library = shape_library
        self.particle_system = particle_system

        # Current state
        self.current_shape_index = 0
        self.state = TransitionState.HOLDING
        self.progress = 0.0

        # Timing
        self.last_shape_change = time.time()
        self.transition_start_time = 0

        # Shape data
        self.current_shape = self.shape_library.get_shape(0)
        self.next_shape = None

        # Update particle system with initial paths
        self._update_particle_paths()

    def _update_particle_paths(self):
        """Update particle system with current shape's paths"""
        paths = self.current_shape.get('particle_paths', [])
        self.particle_system.set_paths(paths)

    def get_current_shape(self):
        """Get current shape data"""
        return self.current_shape

    def get_current_shape_name(self):
        """Get current shape name"""
        return self.shape_library.get_shape_name(self.current_shape_index)

    def get_state(self):
        """Get current transition state"""
        return self.state

    def get_progress(self):
        """Get current transition progress (0-1)"""
        return self.progress

    def trigger_next_shape(self):
        """Manually trigger transition to next shape"""
        if self.state == TransitionState.HOLDING:
            self._start_dissolve()

    def _start_dissolve(self):
        """Start dissolve transition"""
        self.state = TransitionState.DISSOLVING
        self.progress = 0.0
        self.transition_start_time = time.time()

        # Prepare next shape
        next_index = (self.current_shape_index + 1) % self.shape_library.shape_count
        self.next_shape = self.shape_library.get_shape(next_index)

    def _start_reform(self):
        """Start reform transition"""
        self.state = TransitionState.REFORMING
        self.progress = 0.0
        self.transition_start_time = time.time()

        # Switch to next shape
        self.current_shape_index = (
            (self.current_shape_index + 1) % self.shape_library.shape_count
        )
        self.current_shape = self.next_shape
        self.next_shape = None

        # Update particle paths for new shape
        self._update_particle_paths()
        self.particle_system.reset_to_paths()

    def _finish_transition(self):
        """Finish transition and return to holding state"""
        self.state = TransitionState.HOLDING
        self.progress = 0.0
        self.last_shape_change = time.time()

    def update(self, dt, frozen=False):
        """
        Update transition state

        Args:
            dt: Delta time in seconds
            frozen: Whether rotation/transitions are frozen

        Returns:
            Current state information dict
        """
        current_time = time.time()

        if self.state == TransitionState.HOLDING:
            # Check for auto-transition
            if not frozen:
                time_held = current_time - self.last_shape_change
                if time_held >= SHAPE_HOLD_TIME:
                    self._start_dissolve()

        elif self.state == TransitionState.DISSOLVING:
            # Update dissolve progress
            elapsed = current_time - self.transition_start_time
            self.progress = min(1.0, elapsed / DISSOLVE_TIME)

            if self.progress >= 1.0:
                self._start_reform()

        elif self.state == TransitionState.REFORMING:
            # Update reform progress
            elapsed = current_time - self.transition_start_time
            self.progress = min(1.0, elapsed / REFORM_TIME)

            if self.progress >= 1.0:
                self._finish_transition()

        return {
            'state': self.state,
            'progress': self.progress,
            'shape_index': self.current_shape_index,
            'shape_name': self.get_current_shape_name()
        }

    def get_render_alpha(self):
        """
        Get alpha multiplier for rendering based on transition state

        Returns:
            Alpha value 0-1
        """
        if self.state == TransitionState.HOLDING:
            return 1.0
        elif self.state == TransitionState.DISSOLVING:
            return 1.0 - self.progress
        elif self.state == TransitionState.REFORMING:
            return self.progress
        return 1.0

    def is_transitioning(self):
        """Check if currently in a transition"""
        return self.state != TransitionState.HOLDING

    def skip_to_shape(self, index):
        """
        Skip directly to a specific shape

        Args:
            index: Shape index to skip to
        """
        if self.state != TransitionState.HOLDING:
            return

        # Validate index
        index = index % self.shape_library.shape_count

        if index != self.current_shape_index:
            self.next_shape = self.shape_library.get_shape(index)
            # Adjust current_shape_index so _start_reform goes to correct shape
            self.current_shape_index = (index - 1) % self.shape_library.shape_count
            self._start_dissolve()
