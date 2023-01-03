import sys
import os

import kivy
kivy.require('2.1.0') # replace with your current kivy version !

from kivy.config import Config

Config.set('graphics', 'width', 1366)
Config.set('graphics', 'height', 768)

from ocrticle.gui import MainApp

import ctypes

if sys.platform == "win32":
    libbytiff = ctypes.CDLL("libtiff-5.dll")
    libbytiff.TIFFSetWarningHandler.argtypes = [ctypes.c_void_p]
    libbytiff.TIFFSetWarningHandler.restype = ctypes.c_void_p
    libbytiff.TIFFSetWarningHandler(None)

def main():
    app = MainApp()
    app.default_image = sys.argv[1] if len(sys.argv) > 1 else None
    app.run()

if __name__ == '__main__':
    main()