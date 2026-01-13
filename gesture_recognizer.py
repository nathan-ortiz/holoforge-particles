"""
gesture_recognizer.py - MediaPipe hand tracking with gesture detection
Recognizes scatter, attract, freeze, and skip gestures
"""

import numpy as np

from config import (
    DISPLAY_WIDTH,
    GESTURE_HOLD_TIME,
    SKIP_COOLDOWN,
    HAND_MIN_DETECTION_CONFIDENCE,
    HAND_MIN_TRACKING_CONFIDENCE,
)

# Try to import MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class GestureRecognizer:
    """Hand gesture recognition using MediaPipe"""

    def __init__(self):
        self.mp_hands = None
        self.hands = None
        self.initialized = False

        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=HAND_MIN_DETECTION_CONFIDENCE,
                    min_tracking_confidence=HAND_MIN_TRACKING_CONFIDENCE
                )
                self.initialized = True
                print("MediaPipe hand tracking initialized")
            except Exception as e:
                print(f"MediaPipe initialization failed: {e}")
        else:
            print("MediaPipe not available - gesture recognition disabled")

        # Gesture state tracking
        self.current_gesture = None
        self.gesture_start_time = 0
        self.last_skip_time = 0
        self.freeze_active = False
        self.last_landmarks = None

    def process_frame(self, frame_rgb):
        """
        Process camera frame and return hand landmarks

        Args:
            frame_rgb: RGB image as numpy array

        Returns:
            MediaPipe hand landmarks or None
        """
        if not self.initialized or frame_rgb is None:
            return None

        try:
            results = self.hands.process(frame_rgb)
            if results.multi_hand_landmarks:
                self.last_landmarks = results.multi_hand_landmarks[0]
                return self.last_landmarks
        except Exception:
            pass

        return None

    def get_fingers_extended(self, landmarks):
        """
        Determine which fingers are extended

        Args:
            landmarks: MediaPipe hand landmarks

        Returns:
            List of 5 booleans [thumb, index, middle, ring, pinky]
        """
        if landmarks is None:
            return [False] * 5

        finger_tips = [4, 8, 12, 16, 20]  # Tip landmarks
        finger_pips = [3, 6, 10, 14, 18]  # PIP joint landmarks

        extended = []

        # Thumb (check x position - different logic than other fingers)
        thumb_tip = landmarks.landmark[4]
        thumb_ip = landmarks.landmark[3]
        thumb_mcp = landmarks.landmark[2]

        # Determine handedness by checking if thumb is to left or right of palm
        wrist = landmarks.landmark[0]
        index_mcp = landmarks.landmark[5]

        # Simple check: if thumb tip is further from wrist than IP joint
        thumb_extended = (
            abs(thumb_tip.x - wrist.x) > abs(thumb_ip.x - wrist.x)
        )
        extended.append(thumb_extended)

        # Other fingers (check y position - lower y = higher on screen = extended)
        for tip, pip in zip(finger_tips[1:], finger_pips[1:]):
            tip_y = landmarks.landmark[tip].y
            pip_y = landmarks.landmark[pip].y
            extended.append(tip_y < pip_y)

        return extended

    def get_thumb_index_distance(self, landmarks):
        """
        Calculate pinch distance between thumb and index finger

        Args:
            landmarks: MediaPipe hand landmarks

        Returns:
            Distance in pixels
        """
        if landmarks is None:
            return float('inf')

        thumb_tip = landmarks.landmark[4]
        index_tip = landmarks.landmark[8]

        dx = thumb_tip.x - index_tip.x
        dy = thumb_tip.y - index_tip.y
        dz = thumb_tip.z - index_tip.z

        # Scale to approximate pixel distance
        return np.sqrt(dx**2 + dy**2 + dz**2) * DISPLAY_WIDTH

    def recognize(self, landmarks, current_time):
        """
        Recognize gesture from landmarks

        Args:
            landmarks: MediaPipe hand landmarks
            current_time: Current time in seconds

        Returns:
            Gesture name ('scatter', 'attract', 'freeze', 'unfreeze', 'skip')
            or None if no gesture confirmed
        """
        if landmarks is None:
            self.current_gesture = None
            return None

        fingers = self.get_fingers_extended(landmarks)
        pinch_distance = self.get_thumb_index_distance(landmarks)

        detected = None

        # Gesture priority order:

        # 1. Open palm = scatter (all 5 fingers extended)
        if all(fingers):
            detected = 'scatter'

        # 2. Pinch = attract (thumb and index close together)
        elif pinch_distance < 40:
            detected = 'attract'

        # 3. Fist = freeze toggle (no fingers extended)
        elif not any(fingers):
            detected = 'freeze_toggle'

        # 4. Peace sign = skip (index + middle extended only)
        elif (fingers[1] and fingers[2] and
              not fingers[0] and not fingers[3] and not fingers[4]):
            detected = 'skip'

        # 5. Thumbs up (reserved for future use)
        elif fingers[0] and not any(fingers[1:]):
            detected = 'thumbs_up'

        else:
            detected = 'neutral'

        # Handle freeze toggle (instant activation)
        if detected == 'freeze_toggle':
            if self.current_gesture != 'freeze_toggle':
                self.freeze_active = not self.freeze_active
                self.current_gesture = 'freeze_toggle'
            return 'freeze' if self.freeze_active else 'unfreeze'

        # Handle skip (with cooldown to prevent rapid triggering)
        if detected == 'skip':
            if current_time - self.last_skip_time > SKIP_COOLDOWN:
                self.last_skip_time = current_time
                self.current_gesture = None
                return 'skip'
            return None

        # Handle hold gestures (scatter, attract need to be held)
        if detected in ['scatter', 'attract']:
            if self.current_gesture != detected:
                self.current_gesture = detected
                self.gesture_start_time = current_time

            # Confirm gesture after hold time
            if current_time - self.gesture_start_time >= GESTURE_HOLD_TIME:
                return detected
            return None

        self.current_gesture = None
        return None

    def get_hand_position_3d(self, landmarks):
        """
        Convert landmarks to 3D position in scene coordinates

        Args:
            landmarks: MediaPipe hand landmarks

        Returns:
            Tuple (x, y, z) in scene coordinates
        """
        if landmarks is None:
            return (0, 0, 0)

        # Calculate palm center from key landmarks
        palm_indices = [0, 1, 5, 9, 13, 17]  # Wrist and finger MCPs

        palm_x = np.mean([landmarks.landmark[i].x for i in palm_indices])
        palm_y = np.mean([landmarks.landmark[i].y for i in palm_indices])
        palm_z = np.mean([landmarks.landmark[i].z for i in palm_indices])

        # Map normalized coordinates to scene coordinates
        # MediaPipe: x,y are 0-1 (normalized to image), z is relative depth
        x = (palm_x - 0.5) * 200   # -100 to +100
        y = -(palm_y - 0.5) * 200  # Flip Y axis, -100 to +100
        z = palm_z * 150           # Scale depth

        return (x, y, z)

    def get_current_gesture_name(self):
        """Get human-readable name of current gesture state"""
        if self.current_gesture is None:
            return "None"
        return self.current_gesture.replace('_', ' ').title()

    def is_available(self):
        """Check if gesture recognition is available"""
        return self.initialized

    def release(self):
        """Release MediaPipe resources"""
        if self.hands is not None:
            try:
                self.hands.close()
            except Exception:
                pass
            self.hands = None
            self.initialized = False
