"""
main.py - HoloForge Particles main application
Pygame + PyOpenGL implementation for holographic wireframe display
"""

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_q, K_f, K_SPACE, K_r
from OpenGL.GL import glClear, glViewport, glMatrixMode, glLoadIdentity
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_PROJECTION, GL_MODELVIEW
from OpenGL.GLU import gluPerspective, gluLookAt
import numpy as np
import time
import sys

from config import (
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    FRAME_RATE,
    CAMERA_DISTANCE,
    FOV,
    AUTO_ROTATE_SPEED,
    PARTICLE_COUNT,
    HAND_FORCE_STRENGTH,
)
from wireframe_renderer import WireframeRenderer
from particle_system import ParticleSystem
from shape_library import ShapeLibrary
from gesture_recognizer import GestureRecognizer
from transition_manager import TransitionManager, TransitionState
from camera_capture import CameraCapture


class HoloForgeApp:
    """Main application class for HoloForge Particles"""

    def __init__(self):
        print("=" * 50)
        print("HoloForge Particles - Holographic Display System")
        print("=" * 50)

        # Initialize Pygame
        pygame.init()
        pygame.display.set_mode(
            (DISPLAY_WIDTH, DISPLAY_HEIGHT),
            DOUBLEBUF | OPENGL
        )
        pygame.display.set_caption("HoloForge Particles")

        # Initialize OpenGL
        self._setup_opengl()

        # Initialize components
        print("\nInitializing components...")
        self.renderer = WireframeRenderer()
        self.shape_library = ShapeLibrary()
        self.gesture_recognizer = GestureRecognizer()
        self.camera = CameraCapture()

        # Get initial shape and create particle system
        initial_shape = self.shape_library.get_shape(0)
        self.particle_system = ParticleSystem(
            initial_shape.get('particle_paths', []),
            count=PARTICLE_COUNT
        )

        # Create transition manager
        self.transition_manager = TransitionManager(
            self.shape_library,
            self.particle_system
        )

        # State
        self.rotation_angle = 0
        self.frozen = False
        self.running = True
        self.show_fps = True
        self.clock = pygame.time.Clock()

        print(f"\nLoaded {self.shape_library.shape_count} shapes:")
        for i in range(self.shape_library.shape_count):
            print(f"  {i + 1}. {self.shape_library.get_shape_name(i)}")

        print("\nControls:")
        print("  Space  - Skip to next shape")
        print("  R      - Toggle freeze rotation")
        print("  F      - Toggle FPS display")
        print("  Q/ESC  - Quit")
        print("\nHand Gestures:")
        print("  Open Palm  - Scatter particles")
        print("  Pinch      - Attract particles")
        print("  Fist       - Toggle freeze")
        print("  Peace Sign - Skip shape")
        print("\n" + "=" * 50)

    def _setup_opengl(self):
        """Configure OpenGL for holographic rendering"""
        glViewport(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT)

        # Setup projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(FOV, 1.0, 10, 1000)

        # Setup modelview matrix
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            0, 0, CAMERA_DISTANCE,  # Camera position
            0, 0, 0,                # Look at origin
            0, 1, 0                 # Up vector
        )

    def handle_events(self):
        """Process Pygame events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    self.running = False

                elif event.key == K_f:
                    self.show_fps = not self.show_fps

                elif event.key == K_SPACE:
                    self.transition_manager.trigger_next_shape()

                elif event.key == K_r:
                    self.frozen = not self.frozen
                    status = "frozen" if self.frozen else "unfrozen"
                    print(f"\rRotation {status}" + " " * 20)

    def update(self, dt):
        """Update application state"""
        current_time = time.time()

        # Process camera and gestures
        hand_force = None

        if self.camera.is_available():
            frame = self.camera.get_frame()

            if frame is not None:
                landmarks = self.gesture_recognizer.process_frame(frame)
                gesture = self.gesture_recognizer.recognize(landmarks, current_time)

                if gesture == 'scatter' or gesture == 'attract':
                    hand_pos = self.gesture_recognizer.get_hand_position_3d(landmarks)
                    hand_force = {
                        'position': hand_pos,
                        'gesture': gesture,
                        'strength': HAND_FORCE_STRENGTH
                    }

                elif gesture == 'freeze':
                    if not self.frozen:
                        self.frozen = True
                        print("\rFrozen (gesture)" + " " * 20)

                elif gesture == 'unfreeze':
                    if self.frozen:
                        self.frozen = False
                        print("\rUnfrozen (gesture)" + " " * 20)

                elif gesture == 'skip':
                    self.transition_manager.trigger_next_shape()
                    print("\rSkipping shape (gesture)" + " " * 20)

        # Auto-rotate (if not frozen)
        if not self.frozen:
            self.rotation_angle += AUTO_ROTATE_SPEED * dt

        # Update transition manager
        self.transition_manager.update(dt, self.frozen)

        # Update particles
        self.particle_system.update(dt, hand_force)

    def render(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT)

        # Get current shape and render state
        current_shape = self.transition_manager.get_current_shape()
        state = self.transition_manager.get_state()
        progress = self.transition_manager.get_progress()

        # Render based on transition state
        if state == TransitionState.HOLDING:
            # Normal rendering
            self.renderer.render_wireframe(
                current_shape,
                self.rotation_angle
            )

        elif state == TransitionState.DISSOLVING:
            # Dissolve effect
            self.renderer.render_dissolve_effect(
                current_shape,
                self.rotation_angle,
                progress
            )

        elif state == TransitionState.REFORMING:
            # Reform effect
            self.renderer.render_reform_effect(
                current_shape,
                self.rotation_angle,
                progress
            )

        # Always render particles (they adapt to transitions)
        alpha = self.transition_manager.get_render_alpha()
        self.renderer.render_particles(
            self.particle_system.get_particles_for_render(),
            self.rotation_angle,
            alpha
        )

        pygame.display.flip()

    def run(self):
        """Main application loop"""
        print("\nStarting render loop...")
        last_time = time.time()
        frame_count = 0
        fps_update_time = last_time

        try:
            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                # Clamp dt to prevent physics explosions
                dt = min(dt, 0.1)

                self.handle_events()
                self.update(dt)
                self.render()

                # Frame rate limiting
                self.clock.tick(FRAME_RATE)

                # FPS display
                frame_count += 1
                if current_time - fps_update_time >= 1.0:
                    if self.show_fps:
                        fps = frame_count / (current_time - fps_update_time)
                        shape_name = self.transition_manager.get_current_shape_name()
                        state = self.transition_manager.get_state()

                        status = f"FPS: {fps:.1f} | Shape: {shape_name}"
                        if state != TransitionState.HOLDING:
                            status += f" | {state}"
                        if self.frozen:
                            status += " | FROZEN"

                        print(f"\r{status}" + " " * 10, end="", flush=True)

                    frame_count = 0
                    fps_update_time = current_time

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")

        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up resources"""
        print("\n\nShutting down...")

        if self.camera:
            self.camera.release()

        if self.gesture_recognizer:
            self.gesture_recognizer.release()

        pygame.quit()
        print("Goodbye!")


def main():
    """Entry point"""
    try:
        app = HoloForgeApp()
        app.run()
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
