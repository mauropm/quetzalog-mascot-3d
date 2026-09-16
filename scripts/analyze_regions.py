from PIL import Image
import colorsys, os, collections

VIEWS = ["front","back","left","right","top","bottom"]
OUT = "output/analysis"
os.makedirs(OUT, exist_ok=True)

def load_white(path):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255,255,255,255))
    return Image.alpha_composite(bg, im).convert("RGB")

def classify(r,g,b):
    mx,mn = max(r,g,b), min(r,g,b)
    v = mx/255.0
    s = 0 if mx==0 else (mx-mn)/mx
    h,_,_ = colorsys.rgb_to_hsv(r/255,g/255,b/255)
    hd = h*360
    if s < 0.13 and v > 0.86:
        return "bg"
    if 20 <= hd <= 65 and s < 0.45 and v > 0.60:
        return "cream"
    if 150 <= hd <= 205 and s >= 0.25:
        return "teal"
    if s < 0.35 and v > 0.55:
        return "cream"
    if hd < 18 or hd > 340:
        return "red"
    return "feather"

for v in VIEWS:
    im = load_white(f"views/{v}.png")
    W,H = im.size
    px = im.load()
    counts = collections.Counter()
    masks = {k: Image.new("L",(W,H),0) for k in ("teal","cream","red","feather")}
    mp = {k: masks[k].load() for k in masks}
    boxes = {k:[W,H,0,0] for k in masks}
    for y in range(H):
        for x in range(W):
            r,g,b = px[x,y]
            c = classify(r,g,b)
            counts[c]+=1
            if c in masks:
                mp[c][x,y]=255
                bb=boxes[c]
                if x<bb[0]:bb[0]=x
                if y<bb[1]:bb[1]=y
                if x>bb[2]:bb[2]=x
                if y>bb[3]:bb[3]=y
    core = Image.new("L",(W,H),0); cp=core.load()
    for k in ("teal","cream"):
        sp=masks[k].load()
        for y in range(H):
            for x in range(W):
                if sp[x,y]: cp[x,y]=255
    core.save(f"{OUT}/{v}_core.png")
    for k in masks: masks[k].save(f"{OUT}/{v}_{k}.png")
    # core silhouette row profile
    print(f"=== {v} {W}x{H} core(teal+cream) ===")
    rows=[]
    for y in range(H):
        mn,mx=None,None
        for x in range(W):
            if cp[x,y]:
                if mn is None: mn=x
                mx=x
        rows.append((y,mn,mx))
    ys=[r for r in rows if r[1] is not None]
    if ys:
        print(f"  core bbox y {ys[0][0]}..{ys[-1][0]}  x {min(r[1] for r in ys)}..{max(r[2] for r in ys)}")
    for i in range(16):
        y=int(H*(i+0.5)/16); _,mn,mx=rows[y]
        if mn is None: print(f"  y={y:4d} ({100*y/H:5.1f}%) empty")
        else: print(f"  y={y:4d} ({100*y/H:5.1f}%) x={mn:4d}..{mx:4d} w={mx-mn:4d} cx={(mn+mx)/2:6.0f}")
    for k in ("teal","cream","red","feather"):
        print(f"  {k:8s} px={counts[k]:8d} bbox={boxes[k]}")
