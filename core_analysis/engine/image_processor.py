"""ImageProcessor — image preprocessing operations. Stateless, all static methods."""

import cv2
import numpy as np


class ImageProcessor:
    @staticmethod
    def auto_levels(image: np.ndarray) -> np.ndarray:
        """Apply CLAHE to L channel of LAB for automatic contrast enhancement."""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def gaussian_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        return cv2.GaussianBlur(image, (k, k), 0)

    @staticmethod
    def sharpen(image: np.ndarray) -> np.ndarray:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(image, -1, kernel)

    @staticmethod
    def canny_edges(image: np.ndarray, low: float = 50, high: float = 150) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return cv2.Canny(gray, low, high)

    @staticmethod
    def adjust_brightness_contrast(image: np.ndarray, brightness: float = 0,
                                   contrast: float = 1.0) -> np.ndarray:
        result = cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)
        return result

    @staticmethod
    def rotate(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by angle (degrees). Positive = counter-clockwise."""
        h, w = image.shape[:2]
        center = (w / 2, h / 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        cos = abs(matrix[0, 0])
        sin = abs(matrix[0, 1])
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)
        matrix[0, 2] += new_w / 2 - center[0]
        matrix[1, 2] += new_h / 2 - center[1]
        return cv2.warpAffine(image, matrix, (new_w, new_h),
                              borderMode=cv2.BORDER_CONSTANT,
                              borderValue=(200, 200, 200))

    @staticmethod
    def flip_horizontal(image: np.ndarray) -> np.ndarray:
        return cv2.flip(image, 1)

    @staticmethod
    def flip_vertical(image: np.ndarray) -> np.ndarray:
        return cv2.flip(image, 0)

    @staticmethod
    def detect_orientation(image: np.ndarray) -> float:
        """Detect dominant line orientation in degrees. Returns angle (0-180)."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50,
                                minLineLength=30, maxLineGap=10)
        if lines is None or len(lines) == 0:
            return 0.0
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            angles.append(angle % 180)
        if not angles:
            return 0.0
        return float(np.median(angles))

    @staticmethod
    def auto_rotate(image: np.ndarray) -> np.ndarray:
        """Auto-detect orientation and rotate to horizontal."""
        angle = ImageProcessor.detect_orientation(image)
        correction = angle if angle <= 90 else angle - 180
        if abs(correction) < 2:
            return image
        rotated = ImageProcessor.rotate(image, correction)
        h, w = image.shape[:2]
        rh, rw = rotated.shape[:2]
        y0 = (rh - h) // 2
        x0 = (rw - w) // 2
        return rotated[y0:y0 + h, x0:x0 + w]
