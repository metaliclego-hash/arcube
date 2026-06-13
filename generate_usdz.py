import zipfile
import math
import os

def generate_usda(od_mm=100, len_mm=500, N=32):
    wall    = max(2.0, round(od_mm * 0.04, 1))
    outer_r = (od_mm / 2) / 10
    inner_r = (od_mm / 2 - wall) / 10
    H       = len_mm / 10

    # 頂点: 外円左/外円右/内円左/内円右 各N個
    pts = []
    for ring in range(4):
        x = -H/2 if ring % 2 == 0 else H/2
        r = outer_r if ring < 2 else inner_r
        for i in range(N):
            theta = 2 * math.pi * i / N
            pts.append((x, r * math.cos(theta), r * math.sin(theta)))

    counts, indices, normals = [], [], []

    def face(a, b, c, d, nx, ny, nz):
        counts.append(4)
        indices.extend([a, b, c, d])
        for _ in range(4):
            normals.append((nx, ny, nz))

    for i in range(N):
        j  = (i + 1) % N
        tm = 2 * math.pi * (i + 0.5) / N
        cy, cz = math.cos(tm), math.sin(tm)
        face(i,      j,      N+j,    N+i,    0,   cy,  cz)
        face(2*N+i,  3*N+i,  3*N+j,  2*N+j,  0,  -cy, -cz)
        face(i,      2*N+i,  2*N+j,  j,     -1,   0,   0)
        face(N+i,    N+j,    3*N+j,  3*N+i,  1,   0,   0)

    p = ', '.join(f'({x:.4f}, {y:.4f}, {z:.4f})' for x,y,z in pts)
    c = ', '.join(map(str, counts))
    idx = ', '.join(map(str, indices))
    n = ', '.join(f'({x:.6f}, {y:.6f}, {z:.6f})' for x,y,z in normals)

    return f"""#usda 1.0
(
    defaultPrim = "Root"
    metersPerUnit = 0.01
    upAxis = "Y"
)

def Xform "Root"
{{
    def Xform "PipeGroup"
    {{
        double3 xformOp:translate = (0, {outer_r:.4f}, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]

        def Mesh "Shell"
        {{
            int[] faceVertexCounts = [{c}]
            int[] faceVertexIndices = [{idx}]
            normal3f[] normals = [{n}] (
                interpolation = "faceVarying"
            )
            point3f[] points = [{p}]
            uniform token subdivisionScheme = "none"
            rel material:binding = </Root/PipeMat>
        }}

        def Cylinder "Water"
        {{
            double height = {H:.4f}
            double radius = {inner_r:.4f}
            uniform token axis = "X"
            rel material:binding = </Root/WaterMat>
        }}
    }}

    def Material "PipeMat"
    {{
        token outputs:surface.connect = </Root/PipeMat/S.outputs:surface>
        def Shader "S"
        {{
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor = (0.58, 0.58, 0.64)
            float inputs:metallic = 0.0
            float inputs:roughness = 1.0
            float inputs:ior = 1.0
            float inputs:opacity = 1.0
            token outputs:surface
        }}
    }}

    def Material "WaterMat"
    {{
        token outputs:surface.connect = </Root/WaterMat/S.outputs:surface>
        def Shader "S"
        {{
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor = (0.25, 0.55, 0.88)
            float inputs:metallic = 0.0
            float inputs:roughness = 1.0
            float inputs:ior = 1.0
            float inputs:opacity = 1.0
            token outputs:surface
        }}
    }}
}}"""

content = generate_usda(od_mm=100, len_mm=500)

with open("pipe.usda", "w") as f:
    f.write(content)
print("Generated pipe.usda")

with zipfile.ZipFile("pipe.usdz", "w", zipfile.ZIP_STORED) as zf:
    zf.writestr("pipe.usda", content)
print(f"Created pipe.usdz ({os.path.getsize('pipe.usdz')} bytes)")
