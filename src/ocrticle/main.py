import sys, os
import ctypes
import kivy
from dotenv_vault import load_dotenv

kivy.require("2.1.0")  # replace with your current kivy version !

from kivy.resources import resource_add_path, resource_find
from kivy.lang.builder import Builder
from kivy.config import Config

Config.set("graphics", "width", 1366)
Config.set("graphics", "height", 768)

# Gets the system environment variable ENVIRONMENT
# Using .get so that it doesn't crash if the variable doesn't exist
USER_NAME = os.getlogin()
from dotenv import load_dotenv

environment_file_name = get_script_path() + "/.env." + USER_NAME
load_dotenv(environment_file_name)
lang = os.getenv("TES_LANG")


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


# Gets the system environment variable ENVIRONMENT
# Using .get so that it doesn't crash if the variable doesn't exist
USER_NAME = os.getlogin()
from dotenv import load_dotenv

environment_file_name = get_script_path() + "/.env." + USER_NAME
load_dotenv(environment_file_name)
teslang = os.getenv("TES_LANG")


def main():
    from ocrticle.gui import OCRticleApp

    # Builder.load_file(resource_find('ocrticle.kv')) # Needed only when generating EXE file for some reason I couldn't figure out
    app = OCRticleApp()
    app.default_image = sys.argv[1] if len(sys.argv) > 1 else None
    app.run()


if __name__ == "__main__":
    if hasattr(sys, "_MEIPASS"):
        resource_add_path(os.path.join(sys._MEIPASS))

    if sys.platform == "win32":
        libbytiff = ctypes.CDLL("libtiff-5.dll")
        libbytiff.TIFFSetWarningHandler.argtypes = [ctypes.c_void_p]
        libbytiff.TIFFSetWarningHandler.restype = ctypes.c_void_p
        libbytiff.TIFFSetWarningHandler(None)

    main()
