import zipfile
import os
import sys

def make_usdz(usda_file, output_file):
    if not os.path.exists(usda_file):
        print(f"Error: {usda_file} not found")
        sys.exit(1)
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_STORED) as zf:
        zf.write(usda_file, os.path.basename(usda_file))
    print(f"Created {output_file} ({os.path.getsize(output_file)} bytes)")

make_usdz("pipe.usda", "pipe.usdz")
