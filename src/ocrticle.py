"""OCRticle - Structured OCR for articles"""

__version__ = "0.1.0"

import sys

import kivy
kivy.require('2.1.0') # replace with your current kivy version !

from kivy.config import Config

Config.set('graphics', 'width', 1366)
Config.set('graphics', 'height', 768)

from gui import OCRApp

import ctypes

libbytiff = ctypes.CDLL("libtiff-5.dll")
libbytiff.TIFFSetWarningHandler.argtypes = [ctypes.c_void_p]
libbytiff.TIFFSetWarningHandler.restype = ctypes.c_void_p
libbytiff.TIFFSetWarningHandler(None)

def main():
    OCRApp().run()

if __name__ == '__main__':
    main()