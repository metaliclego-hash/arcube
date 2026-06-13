import zipfile
import os
import sys

input_file = "cube.usda"
output_file = "cube.usdz"

if not os.path.exists(input_file):
    print(f"Error: {input_file} not found")
    sys.exit(1)

# USDZ is a ZIP archive where the first entry must use ZIP_STORED (no compression)
with zipfile.ZipFile(output_file, "w", zipfile.ZIP_STORED) as zf:
    zf.write(input_file, os.path.basename(input_file))

size = os.path.getsize(output_file)
print(f"Created {output_file} ({size} bytes)")
