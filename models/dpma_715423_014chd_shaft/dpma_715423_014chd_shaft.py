"""Generate a prototype CAD mesh/STEP faceted model for shaft DPMA.715423.014ChD.
Units: mm. Axis: X. This is a visual/check prototype, not production CAD.
"""
from __future__ import annotations
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
N = 96
TOTAL=426.0
SLOT_L=40.0
SLOT_RIGHT=TOTAL-170.0
SLOT_LEFT=SLOT_RIGHT-SLOT_L
SLOT_R=4.0
SLOT_W=8.0
SLOT_DEPTH=4.0

def radius_at(x):
    if x < 47.5: return 12.0
    if x >= SLOT_RIGHT: return 12.0
    return 11.0

def clamp_section(x,y,z):
    # left lysk/square across first 24 mm: square 17 mm bounded by nominal Ø24 envelope
    if x <= 24.0:
        y=max(-8.5,min(8.5,y)); z=max(-8.5,min(8.5,z))
    # right 2x45 chamfer: approximate outer radius taper over last 2 mm
    if x >= TOTAL-2.0:
        scale=(TOTAL-x)/2.0
        r=10.0+2.0*max(0.0,min(1.0,scale))
        rr=math.hypot(y,z)
        if rr>r and rr>1e-9:
            y*=r/rr; z*=r/rr
    # slot: capsule on top, width 8, rounded ends R4, depth 4 from OD
    if z > 0:
        cx=min(max(x, SLOT_LEFT+SLOT_R), SLOT_RIGHT-SLOT_R)
        d=math.hypot(x-cx, y)
        if d <= SLOT_R:
            floor=radius_at(x)-SLOT_DEPTH
            z=min(z,floor)
    return y,z

def ring(x):
    pts=[]
    r=radius_at(x)
    for i in range(N):
        a=2*math.pi*i/N
        y=r*math.cos(a); z=r*math.sin(a)
        y,z=clamp_section(x,y,z)
        pts.append((x,y,z))
    return pts

xs=sorted(set([0,1,2,4,8,16,24,47.5,48,80,120,160,200,SLOT_LEFT,
               SLOT_LEFT+2,SLOT_LEFT+4,SLOT_LEFT+8,SLOT_LEFT+20,SLOT_RIGHT-8,
               SLOT_RIGHT-4,SLOT_RIGHT-2,SLOT_RIGHT,300,350,400,424,426]))
verts=[]; rings=[]
for x in xs:
    rings.append(list(range(len(verts),len(verts)+N)))
    verts.extend(ring(x))
faces=[]
# side faces
for a,b in zip(rings,rings[1:]):
    for i in range(N):
        faces.append((a[i],a[(i+1)%N],b[(i+1)%N],b[i]))
# end caps
faces.append(tuple(reversed(rings[0])))
faces.append(tuple(rings[-1]))

def write_stl(path):
    def normal(p,q,r):
        ux,uy,uz=[q[i]-p[i] for i in range(3)]; vx,vy,vz=[r[i]-p[i] for i in range(3)]
        nx=uy*vz-uz*vy; ny=uz*vx-ux*vz; nz=ux*vy-uy*vx
        l=math.sqrt(nx*nx+ny*ny+nz*nz) or 1
        return nx/l,ny/l,nz/l
    with open(path,'w',encoding='ascii') as f:
        f.write('solid dpma_715423_014chd_shaft\n')
        for face in faces:
            tris=[]
            if len(face)==3: tris=[face]
            else:
                for i in range(1,len(face)-1): tris.append((face[0],face[i],face[i+1]))
            for tri in tris:
                p,q,r=[verts[i] for i in tri]; n=normal(p,q,r)
                f.write(' facet normal %.6g %.6g %.6g\n  outer loop\n'%n)
                for v in (p,q,r): f.write('   vertex %.6f %.6f %.6f\n'%v)
                f.write('  endloop\n endfacet\n')
        f.write('endsolid dpma_715423_014chd_shaft\n')

def write_step_faceted(path):
    eid=1; lines=[]
    def add(s):
        nonlocal eid; lines.append(f'#{eid}={s};'); eid+=1; return eid-1
    pts=[add("CARTESIAN_POINT('',(%.6f,%.6f,%.6f))"%v) for v in verts]
    face_ids=[]
    for face in faces:
        pl=add("POLY_LOOP('',(%s))"%','.join(f'#{pts[i]}' for i in face))
        fb=add(f"FACE_OUTER_BOUND('',#{pl},.T.)")
        face_ids.append(add(f"FACE('',(#{fb}))"))
    closed=add("CLOSED_SHELL('',(%s))"%','.join(f'#{i}' for i in face_ids))
    brep=add(f"FACETED_BREP('DPMA.715423.014ChD prototype shaft',#{closed})")
    add("PRODUCT('DPMA.715423.014ChD','Prototype shaft','visual check model',())")
    with open(path,'w',encoding='ascii') as f:
        f.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Faceted visual prototype STEP'),'2;1');\n")
        f.write("FILE_NAME('dpma_715423_014chd_shaft.step','2026-06-24T00:00:00',('OpenAI Codex'),(''), 'generated','text-to-cad','');\n")
        f.write("FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));\nENDSEC;\nDATA;\n")
        for line in lines: f.write(line+'\n')
        f.write("ENDSEC;\nEND-ISO-10303-21;\n")

if __name__=='__main__':
    write_stl(OUT/'dpma_715423_014chd_shaft.stl')
    write_step_faceted(OUT/'dpma_715423_014chd_shaft.step')
    print('wrote', OUT/'dpma_715423_014chd_shaft.step')
    print('wrote', OUT/'dpma_715423_014chd_shaft.stl')
