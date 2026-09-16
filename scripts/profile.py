from PIL import Image

def prof(name, rows=20):
    im = Image.open(f"views/{name}.png").convert("RGB")
    W,H = im.size
    px = im.load()
    print(f"=== {name} {W}x{H} ===")
    for i in range(rows):
        y = int(H*(i+0.5)/rows)
        mn,mx = None,None
        for x in range(W):
            r,g,b = px[x,y]
            mxx,mnn = max(r,g,b),min(r,g,b)
            if mnn<225 and (mxx-mnn)>25:
                if mn is None: mn=x
                mx=x
        if mn is None:
            print(f"  y={y:4d} ({100*y/H:5.1f}%) empty")
        else:
            print(f"  y={y:4d} ({100*y/H:5.1f}%) x={mn:4d}..{mx:4d} w={mx-mn:4d} cx={(mn+mx)/2:6.0f}")
prof("front",24)
prof("top",24)
prof("bottom",24)
