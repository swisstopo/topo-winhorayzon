# Description: Setup file for Windows (MinGW only)
#
# Build: python setup_windows.py build_ext --inplace
#
# MIT License
# Windows adaptation: 2024

# Load modules
import os
import sys
import shutil
import glob
from setuptools import setup, Extension
from Cython.Distutils import build_ext
import numpy as np

# -----------------------------------------------------------------------------
# Windows-specific settings
# -----------------------------------------------------------------------------

if sys.platform != "win32":
    raise RuntimeError("This setup script is for Windows only. "
                       "Use setup.py for Linux/macOS.")

print("Operating system: Windows")
print(f"Python version: {sys.version}")

# Base path of the project
base_path = os.path.dirname(os.path.abspath(__file__))

# Paths to Embree (shipped with the project)
embree_include = os.path.join(base_path, "embree", "include")
embree_bin_dir = os.path.join(base_path, "embree", "bin")

# Paths to MinGW-built TBB
tbb_include_dir = r"C:\work\git\tbb-mingw\include\oneapi"
tbb_lib_dir     = r"C:\work\git\tbb-mingw\lib"

# Verify paths exist
for path, name in [(embree_include,  "Embree include"),
                   (embree_bin_dir,  "Embree bin"),
                   (tbb_include_dir, "TBB include (MinGW)"),
                   (tbb_lib_dir,     "TBB lib (MinGW)")]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{name} directory not found: {path}")

print(f"Embree include : {embree_include}")
print(f"Embree bin     : {embree_bin_dir}")
print(f"TBB include    : {tbb_include_dir}")
print(f"TBB lib        : {tbb_lib_dir}")
print("Compiler       : MinGW/g++")

# -----------------------------------------------------------------------------
# Compiler settings (MinGW only)
# -----------------------------------------------------------------------------

os.environ["CC"]  = "gcc"
os.environ["CXX"] = "g++"

extra_compile_args_cpp = [
    "-O2",
    "-std=c++14",
    "-fPIC",
    "-Wall",
    "-D_USE_MATH_DEFINES",
]
extra_compile_args_cython = ["-O2"]
extra_link_args_cpp = []
compiler_options = {"build_ext": {"compiler": "mingw32"}}

# Include directories for C++ modules
# tbb_include_dir MUST be first to override any other TBB headers (e.g. conda)
include_dirs_cpp = [
    tbb_include_dir,
    np.get_include(),
    embree_include,
]

# Library directories
# Note: embree\lib is intentionally excluded - it contains MSVC-only .lib files
library_dirs = [
    tbb_lib_dir,
    embree_bin_dir,
]

# Libraries to link
libraries_cpp    = ["embree4", "tbb12"]
libraries_cython = []

# -----------------------------------------------------------------------------
# Clean old Cython-generated files
# -----------------------------------------------------------------------------

cython_generated = [
    "horayzon/transform.c",
    "horayzon/direction.c",
    "horayzon/topo_param.c",
    "horayzon/horizon.cpp",
    "horayzon/shadow.cpp",
]
for gen_file in cython_generated:
    gen_path = os.path.join(base_path, gen_file)
    if os.path.exists(gen_path):
        os.remove(gen_path)
        print(f"  Removed old: {gen_file}")

# -----------------------------------------------------------------------------
# Compile Cython/C++ code
# -----------------------------------------------------------------------------

ext_modules = [
    Extension(
        "horayzon.transform",
        ["horayzon/transform.pyx"],
        libraries=libraries_cython,
        extra_compile_args=extra_compile_args_cython,
        include_dirs=[np.get_include()],
    ),
    Extension(
        "horayzon.direction",
        ["horayzon/direction.pyx"],
        libraries=libraries_cython,
        extra_compile_args=extra_compile_args_cython,
        include_dirs=[np.get_include()],
    ),
    Extension(
        "horayzon.topo_param",
        ["horayzon/topo_param.pyx"],
        libraries=libraries_cython,
        extra_compile_args=extra_compile_args_cython,
        include_dirs=[np.get_include()],
    ),
    Extension(
        "horayzon.horizon",
        sources=["horayzon/horizon.pyx", "horayzon/horizon_comp.cpp"],
        include_dirs=include_dirs_cpp,
        library_dirs=library_dirs,
        libraries=libraries_cpp,
        extra_compile_args=extra_compile_args_cpp,
        extra_link_args=extra_link_args_cpp,
        language="c++",
    ),
    Extension(
        "horayzon.shadow",
        sources=["horayzon/shadow.pyx", "horayzon/shadow_comp.cpp"],
        include_dirs=include_dirs_cpp,
        library_dirs=library_dirs,
        libraries=libraries_cpp,
        extra_compile_args=extra_compile_args_cpp,
        extra_link_args=extra_link_args_cpp,
        language="c++",
    ),
]

setup(
    name="horayzon",
    version="1.2",
    description="Horizon and shadow computation using ray tracing (Windows fork)",
    long_description="Windows adaptation of horayzon. "
                     "Original project by Christian R. Steger, ETH Zurich: "
                     "https://github.com/ChristianSteger/Horayzon",
    author="Stefan Flury",
    author_email="",
    url="https://github.com/stflury",
    license="MIT",
    python_requires=">=3.11.11",
    install_requires=[
        "numpy",
        "scipy",
        "geographiclib",
        "tqdm",
        "requests",
        "xarray",
        "Pillow",
        "GDAL",
        "shapely",
        "fiona",
        "scikit-image",
    ],
    zip_safe=False,
    packages=["horayzon"],
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
    options=compiler_options,
)

# -----------------------------------------------------------------------------
# Assemble module into horayzon_modul/horayzon/
# -----------------------------------------------------------------------------

output_dir = os.path.join(base_path, "horayzon_modul", "horayzon")

if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)

# Copy compiled .pyd files
for pyd_file in glob.glob(os.path.join(base_path, "horayzon", "*.pyd")):
    shutil.copy2(pyd_file, output_dir)
    print(f"  Copied: {os.path.basename(pyd_file)}")

# Copy pure Python files
python_files = ["__init__.py", "auxiliary.py", "domain.py", "download.py",
                "geoid.py", "load_dem.py", "ocean_masking.py"]
for py_file in python_files:
    src = os.path.join(base_path, "horayzon", py_file)
    if os.path.exists(src):
        shutil.copy2(src, output_dir)
        print(f"  Copied: {py_file}")

# Copy required DLLs (MSVC Embree + MinGW TBB + MinGW runtime)
dll_sources = [
    os.path.join(embree_bin_dir,      "embree4.dll"),
    os.path.join(embree_bin_dir,      "tbb12.dll"),
    r"C:\work\git\tbb-mingw\bin\libtbb12.dll",
    r"C:\LegacySW\mingw64\bin\libgcc_s_seh-1.dll",
    r"C:\LegacySW\mingw64\bin\libstdc++-6.dll",
]
for dll_src in dll_sources:
    if os.path.exists(dll_src):
        shutil.copy2(dll_src, output_dir)
        print(f"  Copied: {os.path.basename(dll_src)}")
    else:
        print(f"  WARNING: not found: {dll_src}")

print("\n" + "=" * 60)
print("BUILD COMPLETE")
print("=" * 60)
print(f"\nModule assembled in: {output_dir}")
print("=" * 60)
