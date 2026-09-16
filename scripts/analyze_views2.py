from PIL import Image
views = ["front","back","left","right","top","bottom"]
for v in views:
    im = Image.open(f"views/{v}.png").convert("RGB")
    W,H = im.size
    px = im.load()
    minx,miny,maxx,maxy = W,H,0,0
    for y in range(H):
        for x in range(W):
            r,g,b = px[x,y]
            mx,mn = max(r,g,b), min(r,g,b)
            if mn < 225 and (mx-mn) > 25:   # saturated / colored
                if x<minx: minx=x
                if x>maxx: maxx=x
                if y<miny: miny=y
                if y>maxy: maxy=y
    print(f"{v:7s} bbox=({minx},{miny})-({maxx},{maxy}) w={maxx-minx} h={maxy-miny} cx={(minx+maxx)/2:.0f} cy={(miny+maxy)/2:.0f}")
