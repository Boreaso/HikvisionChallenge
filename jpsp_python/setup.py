from distutils.core import Extension, setup

from Cython.Build import cythonize

setup(ext_modules=cythonize(Extension(
    'jps_cython',
    sources=['jps_cython.pyx'],
    language='c++',
    include_dirs=[],
    # library_dirs=[],
    # libraries=[],
    # extra_compile_args=[],
    # extra_link_args=[]
)))

setup(ext_modules=cythonize(Extension(
    'bridge_cython',
    sources=['bridge_cython.pyx'],
    language='c++',
    include_dirs=[],
    # library_dirs=[],
    # libraries=[],
    # extra_compile_args=[],
    # extra_link_args=[]
)))

# setup(ext_modules=cythonize("t_misc.py"))
# shell命令： python setup.py build_ext --inplace
