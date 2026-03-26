# Description: Build a .whl (wheel) from the compiled horayzon module
#
# Usage: python build_wheel.py
#
# Creates a wheel file in D:\git\WINHORAYZON\wheel\

import os
import sys
import struct
import hashlib
import base64
import csv
import io
import zipfile

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.join(base_path, "horayzon_modul", "horayzon")
output_dir = os.path.join(base_path, "whl")

pkg_name = "winhorayzon"
pkg_version = "1.2.0"
dist_info = f"{pkg_name}-{pkg_version}.dist-info"

# Detect Python version and platform automatically
py_ver = f"cp{sys.version_info.major}{sys.version_info.minor}"
if sys.platform == "win32":
    arch = "win_amd64" if struct.calcsize("P") * 8 == 64 else "win32"
elif sys.platform == "linux":
    arch = "manylinux1_x86_64" if struct.calcsize("P") * 8 == 64 else "manylinux1_i686"
elif sys.platform == "darwin":
    arch = "macosx_10_9_x86_64"
else:
    arch = "any"

wheel_tag = f"{py_ver}-{py_ver}-{arch}"
wheel_filename = f"{pkg_name}-{pkg_version}-{wheel_tag}.whl"

# Verify module directory exists
if not os.path.exists(module_dir):
    raise FileNotFoundError(f"Module directory not found: {module_dir}\n"
                            "Run setup_windows.py build_ext --inplace first.")

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# -----------------------------------------------------------------------------
# METADATA
# -----------------------------------------------------------------------------

metadata_content = """\
Metadata-Version: 2.1
Name: winhorayzon
Version: 1.2.0
Summary: Horizon and shadow computation using ray tracing (Windows fork)
Author: Stefan Flury
Home-page: https://github.com/stflury
License: MIT
Description: Windows adaptation of horayzon.
        Original project by Christian R. Steger, ETH Zurich:
        https://github.com/ChristianSteger/Horayzon
Requires-Python: >=3.11.11
"""

# -----------------------------------------------------------------------------
# WHEEL metadata
# -----------------------------------------------------------------------------

wheel_content = f"""\
Wheel-Version: 1.0
Generator: build_wheel.py
Root-Is-Purelib: false
Tag: {wheel_tag}
"""

# -----------------------------------------------------------------------------
# Build the wheel (zip file)
# -----------------------------------------------------------------------------

wheel_path = os.path.join(output_dir, wheel_filename)
record_lines = []


def file_hash(data):
    """Calculate sha256 hash in base64url format (no padding) for RECORD."""
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


print(f"Building wheel: {wheel_filename}")
print(f"Source: {module_dir}")
print()

with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as whl:

    # Add all files from horayzon/ package
    for filename in sorted(os.listdir(module_dir)):
        filepath = os.path.join(module_dir, filename)
        if os.path.isfile(filepath):
            arcname = f"horayzon/{filename}"
            with open(filepath, "rb") as f:
                data = f.read()
            whl.writestr(arcname, data)
            record_lines.append(f"{arcname},{file_hash(data)},{len(data)}")
            print(f"  Added: {arcname}")

    # Add METADATA
    meta_bytes = metadata_content.encode("utf-8")
    arcname = f"{dist_info}/METADATA"
    whl.writestr(arcname, meta_bytes)
    record_lines.append(f"{arcname},{file_hash(meta_bytes)},{len(meta_bytes)}")

    # Add WHEEL
    wheel_bytes = wheel_content.encode("utf-8")
    arcname = f"{dist_info}/WHEEL"
    whl.writestr(arcname, wheel_bytes)
    record_lines.append(f"{arcname},{file_hash(wheel_bytes)},{len(wheel_bytes)}")

    # Add top_level.txt
    toplevel_bytes = b"horayzon\n"
    arcname = f"{dist_info}/top_level.txt"
    whl.writestr(arcname, toplevel_bytes)
    record_lines.append(f"{arcname},{file_hash(toplevel_bytes)},{len(toplevel_bytes)}")

    # Add RECORD (itself is listed without hash)
    record_lines.append(f"{dist_info}/RECORD,,")
    record_content = "\n".join(record_lines) + "\n"
    whl.writestr(f"{dist_info}/RECORD", record_content.encode("utf-8"))

print()
print("=" * 60)
print("WHEEL BUILD COMPLETE")
print("=" * 60)
print(f"\nWheel: {wheel_path}")
print(f"\nInstall with:")
print(f"  pip install \"{wheel_path}\"")
print("=" * 60)
