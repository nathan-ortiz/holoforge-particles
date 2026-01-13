"""
camera_capture.py - Picamera2 integration for hand tracking
Supports both Picamera2 (Raspberry Pi) and OpenCV webcam fallback
"""

import cv2
import numpy as np

from config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

# Try to import Picamera2
try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False


class CameraCapture:
    """Camera capture with Picamera2/OpenCV support"""

    def __init__(self):
        self.camera = None
        self.use_picamera = PICAMERA_AVAILABLE
        self.initialized = False

        self._initialize_camera()

    def _initialize_camera(self):
        """Initialize camera with fallback support"""
        if self.use_picamera:
            try:
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration(
                    main={
                        "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
                        "format": "RGB888"
                    }
                )
                self.camera.configure(config)
                self.camera.start()
                self.initialized = True
                print(f"Picamera2 initialized: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
            except Exception as e:
                print(f"Picamera2 failed: {e}")
                print("Falling back to OpenCV...")
                self.use_picamera = False
                self.camera = None

        if not self.use_picamera:
            # Fallback to USB webcam via OpenCV
            try:
                self.camera = cv2.VideoCapture(0)
                if self.camera.isOpened():
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                    self.camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
                    self.initialized = True
                    print(f"OpenCV camera initialized: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
                else:
                    print("No camera available - running without hand tracking")
                    self.camera = None
            except Exception as e:
                print(f"OpenCV camera failed: {e}")
                print("Running without hand tracking")
                self.camera = None

    def get_frame(self):
        """
        Get RGB frame for MediaPipe processing

        Returns:
            numpy array (H, W, 3) in RGB format, or None if unavailable
        """
        if not self.initialized or self.camera is None:
            return None

        if self.use_picamera:
            try:
                frame = self.camera.capture_array()
                return frame  # Already RGB from Picamera2
            except Exception:
                return None
        else:
            try:
                ret, frame = self.camera.read()
                if ret:
                    # Convert BGR to RGB for MediaPipe
                    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return None
            except Exception:
                return None

    def release(self):
        """Release camera resources"""
        if self.camera is not None:
            if self.use_picamera:
                try:
                    self.camera.stop()
                except Exception:
                    pass
            else:
                try:
                    self.camera.release()
                except Exception:
                    pass
            self.camera = None
            self.initialized = False

    def is_available(self):
        """Check if camera is available"""
        return self.initialized and self.camera is not None

    def __del__(self):
        """Cleanup on deletion"""
        self.release()
