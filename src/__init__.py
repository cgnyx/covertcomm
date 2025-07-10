# CovertComm - Advanced Steganography Toolkit
__version__ = "1.0.0"
__author__ = "CovertComm Development Team"
__description__ = "Advanced steganography toolkit for secure communication"

# Import main classes for easy access
from .covertcomm_core import ImageSteganography, AudioSteganography
from .covertcomm_gui import CovertCommMainWindow

__all__ = ['ImageSteganography', 'AudioSteganography', 'CovertCommMainWindow']


