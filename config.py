"""
Configuration for HoloForge Particles
All tunable parameters in one place
"""

# Display
DISPLAY_WIDTH = 720
DISPLAY_HEIGHT = 720
FRAME_RATE = 60
BACKGROUND_COLOR = (0, 0, 0)  # Pure black for beam splitter

# Wireframe Rendering
WIREFRAME_LINE_WIDTH = 2.5        # Base line width
WIREFRAME_GLOW_PASSES = 3         # Number of glow passes (1-5)
WIREFRAME_GLOW_FALLOFF = 0.5      # Alpha reduction per pass
WIREFRAME_GLOW_EXPANSION = 1.5    # Line width multiplier per pass

# Particle Aura
PARTICLE_COUNT = 300              # Sparse particles (200-500)
PARTICLE_SIZE = 3
PARTICLE_SPEED = 30.0             # Movement speed along wireframes
PARTICLE_ORBIT_RADIUS = 15.0      # Distance from wireframe
PARTICLE_TRAIL_LENGTH = 5         # Trail segments

# Colors (depth-based gradient)
COLOR_NEAR = (0, 255, 255)        # Cyan (Z > 30)
COLOR_MID = (255, 255, 255)       # White (Z = 0)
COLOR_FAR = (255, 0, 102)         # Magenta (Z < -30)
Z_NEAR_THRESHOLD = 30
Z_FAR_THRESHOLD = -30

# Shape Cycling
SHAPE_HOLD_TIME = 8.0             # Seconds before auto-transition
DISSOLVE_TIME = 1.5               # Wireframe dissolve duration
REFORM_TIME = 2.0                 # Wireframe reform duration
AUTO_ROTATE_SPEED = 0.3           # Radians per second

# Gestures
GESTURE_HOLD_TIME = 0.3           # Seconds to confirm gesture
SKIP_COOLDOWN = 2.0               # Seconds between skips

# Hand Force Field
HAND_FORCE_STRENGTH = 5.0
HAND_FORCE_RADIUS = 100.0

# Camera
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
HAND_MIN_DETECTION_CONFIDENCE = 0.5
HAND_MIN_TRACKING_CONFIDENCE = 0.5

# 3D View
CAMERA_DISTANCE = 400             # OpenGL camera distance from origin
FOV = 45                          # Field of view in degrees
