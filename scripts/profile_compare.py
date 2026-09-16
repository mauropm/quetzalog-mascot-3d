from PIL import Image
import os
PROJ="/Users/mauro/Documents/Code/3D-Quetzalog"; CMP=os.path.join(PROJ,"output","comparison")
MM=0.0905
def mask_img(im):
    return im.split()[3].point(lambda a:255 if a>40 else 0)
def prof(m,W,H,rows=24):
    out=[]
    for i in range(rows):
        y=int(H*(i+0.5)/rows); mn=mx=None
        for x in range(W):
            if m.getpixel((x,y))>0:
                if mn is None: mn=x
                mx=x
        out.append((y,mn,mx))
    return out
for v in ["front","top","left"]:
    mod=Image.open(os.path.join(CMP,"model_%s.png"%v)).convert("RGBA"); W,H=mod.size
    ref=Image.open(os.path.join(PROJ,"views",v+".png")).convert("RGBA").resize((W,H))
    rm=mask_img(ref); mm=mask_img(mod)
    rp=prof(rm,W,H); mp=prof(mm,W,H)
    print(f"===== {v}  (W={W} H={H}) =====")
    print(f"{'y':>5} {'REF L..R (w mm)':>26}   {'MODEL L..R (w mm)':>26}   dW")
    for (ry,rl,rr),(my,ml,mr) in zip(rp,mp):
        rs="--" if rl is None else f"{rl:4d}..{rr:4d} ({(rr-rl)*MM:5.1f})"
        ms="--" if ml is None else f"{ml:4d}..{mr:4d} ({(mr-ml)*MM:5.1f})"
        dw="" if (rl is None or ml is None) else f"{((mr-ml)-(rr-rl))*MM:+5.1f}"
        print(f"{ry:5d} {rs:>26}   {ms:>26}   {dw}")
