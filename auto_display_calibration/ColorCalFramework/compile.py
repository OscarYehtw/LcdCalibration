"""Compile files mapping.

For the files who need to be compiled, must list the relationship as following.
 #example command: python3.6 compile.py build_ext --inplace

"""

from Cython.Distutils import build_ext
from distutils.core import setup
from distutils.extension import Extension

ext_modules = [
    Extension("gamma_calibration", ["gamma_calibration.py"]),
    Extension("gamut_calibration", ["gamut_calibration.py"]), ]

for e in ext_modules:
    e.cython_directives = {'language_level': "3"}

setup(name="GTAL Pixel display gamut cal library",
      cmdclass={"build_ext": build_ext}, ext_modules=ext_modules)


