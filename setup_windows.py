# Description: Setup file for Windows
#
# Build and assemble module: python setup_windows.py build_ext --inplace
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

# Paths to Embree and TBB (shipped with the project)
embree_include = os.path.join(base_path, "embree", "include")
embree_lib_dir = os.path.join(base_path, "embree", "lib")
embree_bin_dir = os.path.join(base_path, "embree", "bin")

tbb_include = os.path.join(base_path, "tbb", "include")
tbb_lib_dir = os.path.join(base_path, "tbb", "lib", "intel64", "vc14")

# Verify paths exist
for path, name in [(embree_include, "Embree include"),
                   (embree_lib_dir, "Embree lib"),
                   (tbb_include, "TBB include"),
                   (tbb_lib_dir, "TBB lib")]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{name} directory not found: {path}")

print(f"Embree include: {embree_include}")
print(f"Embree lib: {embree_lib_dir}")
print(f"TBB include: {tbb_include}")
print(f"TBB lib: {tbb_lib_dir}")

# Compiler flags
# Default: MSVC (required for supplied Embree/TBB libs)
# Optional: MinGW (set USE_MINGW=1 in environment)
use_mingw = os.environ.get("USE_MINGW", "").lower() in ("1", "true", "yes")
if use_mingw:
    print("Using MinGW/g++ mode (USE_MINGW=1).")
    extra_compile_args_cpp = [
        "-O2",
        "-std=c++14",
        "-fPIC",
        "-Wall",
    ]
    extra_compile_args_cython = ["-O2"]
    extra_link_args_cpp = []
    os.environ["CC"] = "gcc"
    os.environ["CXX"] = "g++"
    compiler_options = {"build_ext": {"compiler": "mingw32"}}
else:
    print("Using MSVC mode (default).")
    # /O2 - Optimize for speed
    # /std:c++14 - C++14 standard (required for TBB)
    # /EHsc - Exception handling
    # /D_USE_MATH_DEFINES - Enable M_PI constant
    extra_compile_args_cpp = [
        "/O2",
        "/std:c++14",
        "/EHsc",
        "/D_USE_MATH_DEFINES",
    ]
    extra_compile_args_cython = ["/O2"]
    extra_link_args_cpp = []
    compiler_options = {}

# Include directories
include_dirs_cpp = [
    np.get_include(),
    embree_include,
    os.path.join(tbb_include, "oneapi"),  # TBB headers are under oneapi/tbb/
]

# Library directories
library_dirs = [
    embree_lib_dir,
    tbb_lib_dir,
]

# Libraries to link (without .lib extension)
libraries_cpp = ["embree4", "tbb12"]

# No POSIX libraries on Windows
libraries_cython = []

# -----------------------------------------------------------------------------
# Clean old Cython-generated files (forces regeneration with current NumPy API)
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
    # Pure Cython modules (no external C++ dependencies)
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
]

if not use_mingw:
    # C++ modules with Embree and TBB dependencies (MSVC default)
    ext_modules.extend([
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
    ])

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

# Clean and recreate output directory
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)

# Copy compiled .pyd files from horayzon/
for pyd_file in glob.glob(os.path.join(base_path, "horayzon", "*.pyd")):
    shutil.copy2(pyd_file, output_dir)
    print(f"  Copied: {os.path.basename(pyd_file)}")

# Copy pure Python files from horayzon/
python_files = ["__init__.py", "auxiliary.py", "domain.py", "download.py",
                "geoid.py", "load_dem.py", "ocean_masking.py"]
for py_file in python_files:
    src = os.path.join(base_path, "horayzon", py_file)
    if os.path.exists(src):
        shutil.copy2(src, output_dir)
        print(f"  Copied: {py_file}")

# Copy required DLLs into the module directory
for dll_name in ["embree4.dll", "tbb12.dll"]:
    dll_src = os.path.join(embree_bin_dir, dll_name)
    if os.path.exists(dll_src):
        shutil.copy2(dll_src, output_dir)
        print(f"  Copied: {dll_name}")
    else:
        print(f"  WARNING: {dll_name} not found at {dll_src}")

print("\n" + "=" * 60)
print("BUILD COMPLETE")
print("=" * 60)
print(f"\nModule assembled in: {output_dir}")
print("You can use it by adding the parent directory to your Python path:")
print(f'  sys.path.insert(0, r"{os.path.join(base_path, "horayzon_modul")}")')
print("  import horayzon")
print("=" * 60)
