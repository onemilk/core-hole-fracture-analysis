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
