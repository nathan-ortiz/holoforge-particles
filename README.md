# HoloForge Particles

Glowing wireframe holographic display system for Raspberry Pi 5 + beam splitter cube.

A sci-fi movie quality holographic visualization using Pygame + PyOpenGL, featuring glowing wireframe shapes with sparse particle auras and hand gesture interaction.

## Features

- **7 Stunning Wireframe Shapes**
  - DNA Double Helix
  - Torus Knot (Trefoil)
  - Lorenz Attractor (Butterfly)
  - Wireframe Cube
  - Icosphere (Geodesic)
  - Mobius Strip
  - Double Helix Torus

- **Visual Effects**
  - Multi-pass glow rendering for ethereal appearance
  - Depth-based color gradient (cyan near, white mid, magenta far)
  - Additive blending for holographic transparency
  - Smooth dissolve/reform shape transitions

- **Particle System**
  - 300 sparse particles flowing along wireframe paths
  - Orbit motion around wireframe edges
  - Particle trails for motion blur effect
  - Hand force field interaction

- **Hand Gesture Control**
  - MediaPipe-based hand tracking
  - Scatter particles with open palm
  - Attract particles with pinch gesture
  - Freeze/unfreeze with fist
  - Skip shapes with peace sign

## Requirements

### Hardware
- Raspberry Pi 5 (4GB+ RAM recommended)
- HyperPixel 4.0 Square display (720x720)
- Raspberry Pi Camera Module 3 (optional, for gestures)
- Beam splitter cube (for Pepper's Ghost effect)

### Software
- Raspberry Pi OS (Bookworm or later)
- Python 3.11+
- OpenGL ES support

## Installation

```bash
# Clone repository
cd ~
git clone https://github.com/nathan-ortiz/holoforge-particles.git
cd holoforge-particles

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Make run script executable
chmod +x run.sh
```

### Note for Desktop/Development

If running without Picamera2 (e.g., on desktop), the system will automatically fall back to USB webcam via OpenCV, or run without hand tracking if no camera is available.

## Running

```bash
cd ~/holoforge-particles
./run.sh
```

Or directly:
```bash
python main.py
```

## Controls

### Keyboard
| Key | Action |
|-----|--------|
| `Space` | Skip to next shape |
| `R` | Toggle freeze rotation |
| `F` | Toggle FPS display |
| `Q` / `ESC` | Quit |

### Hand Gestures
| Gesture | Action |
|---------|--------|
| Open Palm (5 fingers) | Scatter particles outward |
| Pinch (thumb + index) | Attract particles to hand |
| Fist (no fingers) | Toggle freeze/unfreeze |
| Peace Sign (2 fingers) | Skip to next shape |

## Configuration

All tunable parameters are in `config.py`:

```python
# Display
DISPLAY_WIDTH = 720
DISPLAY_HEIGHT = 720
FRAME_RATE = 60

# Wireframe Rendering
WIREFRAME_LINE_WIDTH = 2.5
WIREFRAME_GLOW_PASSES = 3

# Particle Aura
PARTICLE_COUNT = 300
PARTICLE_SPEED = 30.0
PARTICLE_ORBIT_RADIUS = 15.0

# Shape Cycling
SHAPE_HOLD_TIME = 8.0     # Seconds per shape
DISSOLVE_TIME = 1.5       # Transition duration
AUTO_ROTATE_SPEED = 0.3   # Radians/second
```

## File Structure

```
holoforge-particles/
├── main.py                  # Entry point, Pygame/OpenGL main loop
├── wireframe_renderer.py    # OpenGL wireframe + glow rendering
├── particle_system.py       # Sparse particle aura physics
├── shape_library.py         # Wireframe path generation
├── gesture_recognizer.py    # MediaPipe hand tracking
├── transition_manager.py    # Shape cycling with effects
├── camera_capture.py        # Picamera2 + OpenCV integration
├── config.py               # All tunable parameters
├── requirements.txt         # Dependencies
├── run.sh                   # Launch script
└── README.md               # This file
```

## Performance

Target: **60 FPS** stable on Raspberry Pi 5

The system is optimized for:
- Additive blending (no depth sorting needed)
- Sparse particles (300 vs thousands)
- Line-based rendering (fast on GPU)
- Efficient path interpolation

## Troubleshooting

### No display output
- Check HyperPixel is properly connected
- Verify `DISPLAY=:0.0` is set
- Try running with `sudo` if permission issues

### Camera not detected
- Check camera is enabled in `raspi-config`
- Verify camera ribbon cable connection
- Try `libcamera-hello` to test camera

### Low frame rate
- Reduce `PARTICLE_COUNT` in config
- Reduce `WIREFRAME_GLOW_PASSES`
- Ensure no other GPU-intensive processes running

### OpenGL errors
- Ensure PyOpenGL and PyOpenGL_accelerate are installed
- Check OpenGL ES drivers are working: `glxinfo | grep OpenGL`

## License

MIT License
