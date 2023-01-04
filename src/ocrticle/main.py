import sys, os
import ctypes

import kivy
kivy.require('2.1.0') # replace with your current kivy version !

from kivy.resources import resource_add_path, resource_find
from kivy.lang.builder import Builder

from kivy.config import Config

Config.set('graphics', 'width', 1366)
Config.set('graphics', 'height', 768)

def main():
    from ocrticle.gui import OCRticleApp

    # Builder.load_file(resource_find('ocrticle.kv')) # Needed only when generating EXE file for some reason I couldn't figure out
    app = OCRticleApp()
    app.default_image = sys.argv[1] if len(sys.argv) > 1 else None
    app.run()

if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))

    if sys.platform == "win32":
        libbytiff = ctypes.CDLL("libtiff-5.dll")
        libbytiff.TIFFSetWarningHandler.argtypes = [ctypes.c_void_p]
        libbytiff.TIFFSetWarningHandler.restype = ctypes.c_void_p
        libbytiff.TIFFSetWarningHandler(None)

    main()