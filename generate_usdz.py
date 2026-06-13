import zipfile, math, os, struct, zlib

# ── Minecraft ダートテクスチャ (16x16 PNG) ──────────────────────────────
DIRT_PAL = [
    (134,96,67),(101,67,50),(161,118,80),(118,85,57),
    (150,109,73),(90,60,40),(143,103,68),(109,75,52),
]
DIRT_MAP = [
    3,1,3,0,6,2,7,0,3,5,3,0,6,2,7,0,
    0,3,1,3,0,7,3,2,0,3,1,3,0,7,3,2,
    6,0,4,1,3,0,5,3,6,0,4,1,3,0,5,3,
    1,6,0,4,1,6,2,0,1,6,0,4,1,6,2,0,
    3,2,6,0,4,1,3,6,3,2,6,0,4,1,3,6,
    0,3,1,6,0,4,0,1,0,3,1,6,0,4,0,1,
    6,1,3,2,6,0,4,3,6,1,3,2,6,0,4,3,
    1,4,0,3,1,6,0,4,1,4,0,3,1,6,0,4,
    3,0,6,1,3,2,6,0,3,0,6,1,3,2,6,0,
    0,5,1,4,0,3,1,6,0,5,1,4,0,3,1,6,
    6,2,4,0,6,1,4,0,6,2,4,0,6,1,4,0,
    1,3,0,6,1,4,0,3,1,3,0,6,1,4,0,3,
    3,0,6,2,3,0,6,1,3,0,6,2,3,0,6,1,
    0,6,1,3,0,6,1,4,0,6,1,3,0,6,1,4,
    6,1,4,0,6,2,4,0,6,1,4,0,6,2,4,0,
    1,4,0,6,1,3,0,6,1,4,0,6,1,3,0,6,
]

def make_png_16x16(palette, pixmap):
    """最小限のPNGエンコーダ（外部ライブラリ不要）"""
    def chunk(name, data):
        c = name + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr   = chunk(b'IHDR', struct.pack('>IIBBBBB', 16, 16, 8, 2, 0, 0, 0))

    raw = b''
    for i, idx in enumerate(pixmap):
        if i % 16 == 0:
            raw += b'\x00'   # filter type None per row
        r, g, b = palette[idx]
        raw += bytes([r, g, b])

    idat = chunk(b'IDAT', zlib.compress(raw, 9))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend

# ── メッシュ生成 ──────────────────────────────────────────────────────────
def build_tube(outer_r, inner_r, H, N=32):
    pts = []
    for ring in range(4):
        x = -H/2 if ring % 2 == 0 else H/2
        r = outer_r if ring < 2 else inner_r
        for i in range(N):
            θ = 2 * math.pi * i / N
            pts.append((x, r*math.cos(θ), r*math.sin(θ)))

    counts, indices, normals = [], [], []
    def face(a,b,c,d, nx,ny,nz):
        counts.append(4); indices.extend([a,b,c,d])
        for _ in range(4): normals.append((nx,ny,nz))

    for i in range(N):
        j = (i+1)%N
        tm = 2*math.pi*(i+0.5)/N
        cy, cz = math.cos(tm), math.sin(tm)
        face(i,j,N+j,N+i,             0, cy, cz)
        face(2*N+i,3*N+i,3*N+j,2*N+j, 0,-cy,-cz)
        face(i,2*N+i,2*N+j,j,        -1, 0,  0)
        face(N+i,N+j,3*N+j,3*N+i,     1, 0,  0)

    p = ', '.join(f'({x:.4f}, {y:.4f}, {z:.4f})' for x,y,z in pts)
    c = ', '.join(map(str, counts))
    idx = ', '.join(map(str, indices))
    n = ', '.join(f'({x:.6f}, {y:.6f}, {z:.6f})' for x,y,z in normals)
    return p, c, idx, n

def build_trench(L, W, D):
    hL, hW = L/2, W/2
    T = 30
    uL, uW, uD = L/T, W/T, D/T
    pts = [
        (-hL, 0,-hW),(-hL, 0, hW),(hL, 0,-hW),(hL, 0, hW),
        (-hL,-D,-hW),(-hL,-D, hW),(hL,-D,-hW),(hL,-D, hW),
    ]
    face_defs = [
        ([5,7,6,4],[0, 1,0],[[0,uW],[uL,uW],[uL,0],[0,0]]),
        ([0,4,6,2],[0, 0,1],[[0,uD],[0,0],[uL,0],[uL,uD]]),
        ([1,3,7,5],[0, 0,-1],[[0,uD],[uL,uD],[uL,0],[0,0]]),
        ([0,1,5,4],[1, 0,0],[[0,uD],[uW,uD],[uW,0],[0,0]]),
        ([2,6,7,3],[-1,0,0],[[uW,uD],[uW,0],[0,0],[0,uD]]),
    ]
    counts, indices, norms, uvs = [], [], [], []
    for vi, nm, uv in face_defs:
        counts.append(4); indices.extend(vi)
        for _ in range(4): norms.append(nm)
        uvs.extend(uv)
    p   = ', '.join(f'({x:.4f}, {y:.4f}, {z:.4f})' for x,y,z in pts)
    c   = ', '.join(map(str, counts))
    idx = ', '.join(map(str, indices))
    n   = ', '.join(f'({x:.6f}, {y:.6f}, {z:.6f})' for x,y,z in norms)
    uv  = ', '.join(f'({u:.4f}, {v:.4f})' for u,v in uvs)
    return p, c, idx, n, uv

# ── USDA 生成 ─────────────────────────────────────────────────────────────
def generate_usda(od_mm=100, len_mm=500, burial_mm=0, trench_w_mm=0, underground=False, N=32):
    wall    = max(2.0, round(od_mm * 0.04, 1))
    outer_r = (od_mm/2)/10
    inner_r = (od_mm/2 - wall)/10
    H       = len_mm/10

    pp, pc, pi, pn = build_tube(outer_r, inner_r, H, N)

    pipe_mat = """
    def Material "PipeMat"
    {
        token outputs:surface.connect = </Root/PipeMat/S.outputs:surface>
        def Shader "S"
        {
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor = (0.58, 0.58, 0.64)
            float inputs:metallic = 0.0
            float inputs:roughness = 1.0
            float inputs:ior = 1.0
            float inputs:opacity = 1.0
            token outputs:surface
        }
    }"""

    water_mat = """
    def Material "WaterMat"
    {
        token outputs:surface.connect = </Root/WaterMat/S.outputs:surface>
        def Shader "S"
        {
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor = (0.25, 0.55, 0.88)
            float inputs:metallic = 0.0
            float inputs:roughness = 1.0
            float inputs:ior = 1.0
            float inputs:opacity = 1.0
            token outputs:surface
        }
    }"""

    if not underground:
        pipe_y = outer_r
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
        double3 xformOp:translate = (0, {pipe_y:.4f}, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]

        def Mesh "Shell"
        {{
            int[] faceVertexCounts = [{pc}]
            int[] faceVertexIndices = [{pi}]
            normal3f[] normals = [{pn}] (
                interpolation = "faceVarying"
            )
            point3f[] points = [{pp}]
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
{pipe_mat}
{water_mat}
}}"""

    # 地中モード
    burial_cm  = burial_mm / 10
    trench_w   = trench_w_mm / 10
    trench_d   = (burial_mm + od_mm) / 10
    pipe_y     = -(burial_cm + outer_r)
    tp, tc, ti, tn, tuv = build_trench(H, trench_w, trench_d)

    dirt_mat = """
    def Material "DirtMat"
    {
        token outputs:surface.connect = </Root/DirtMat/S.outputs:surface>
        def Shader "S"
        {
            uniform token info:id = "UsdPreviewSurface"
            color3f inputs:diffuseColor.connect = </Root/DirtMat/Tex.outputs:rgb>
            float inputs:roughness = 1.0
            float inputs:ior = 1.0
            token outputs:surface
        }
        def Shader "Tex"
        {
            uniform token info:id = "UsdUVTexture"
            asset inputs:file = @dirt.png@
            token inputs:wrapS = "repeat"
            token inputs:wrapT = "repeat"
            float2 inputs:st.connect = </Root/DirtMat/UV.outputs:result>
            float3 outputs:rgb
        }
        def Shader "UV"
        {
            uniform token info:id = "UsdPrimvarReader_float2"
            token inputs:varname = "st"
            float2 outputs:result
        }
    }"""

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
        double3 xformOp:translate = (0, {pipe_y:.4f}, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]

        def Mesh "Shell"
        {{
            int[] faceVertexCounts = [{pc}]
            int[] faceVertexIndices = [{pi}]
            normal3f[] normals = [{pn}] (
                interpolation = "faceVarying"
            )
            point3f[] points = [{pp}]
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

    def Mesh "Trench"
    {{
        int[] faceVertexCounts = [{tc}]
        int[] faceVertexIndices = [{ti}]
        normal3f[] normals = [{tn}] (
            interpolation = "faceVarying"
        )
        point3f[] points = [{tp}]
        texCoord2f[] primvars:st = [{tuv}] (
            interpolation = "faceVarying"
        )
        uniform token subdivisionScheme = "none"
        rel material:binding = </Root/DirtMat>
    }}
{pipe_mat}
{water_mat}
{dirt_mat}
}}"""

# ── メイン ────────────────────────────────────────────────────────────────
usda = generate_usda(od_mm=100, len_mm=500)
with open('pipe.usda', 'w') as f:
    f.write(usda)
print('Generated pipe.usda (surface mode)')

with zipfile.ZipFile('pipe.usdz', 'w', zipfile.ZIP_STORED) as zf:
    zf.writestr('pipe.usda', usda)
print(f'Created pipe.usdz ({os.path.getsize("pipe.usdz")} bytes)')

# 地中モードのサンプル
usda_ug = generate_usda(od_mm=100, len_mm=500, burial_mm=600, trench_w_mm=800, underground=True)
dirt_png = make_png_16x16(DIRT_PAL, DIRT_MAP)
with zipfile.ZipFile('pipe_underground.usdz', 'w', zipfile.ZIP_STORED) as zf:
    zf.writestr('pipe.usda', usda_ug)
    zf.writestr('dirt.png', dirt_png)
print(f'Created pipe_underground.usdz ({os.path.getsize("pipe_underground.usdz")} bytes)')
