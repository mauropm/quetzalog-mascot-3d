from PIL import Image
import os

views = ["front","back","left","right","top","bottom"]
for v in views:
    p = f"views/{v}.png"
    im = Image.open(p).convert("RGBA")
    W,H = im.size
    # get alpha bbox if alpha used, else detect non-white
    alpha = im.split()[3]
    abbox = alpha.getbbox()
    # non-white detection
    px = im.convert("RGB").load()
    minx,miny,maxx,maxy = W,H,0,0
    step = 2
    for y in range(0,H,step):
        for x in range(0,W,step):
            r,g,b = px[x,y]
            if not (r>242 and g>242 and b>242):
                if x<minx: minx=x
                if x>maxx: maxx=x
                if y<miny: miny=y
                if y>maxy: maxy=y
    print(f"{v:7s} size={W}x{H} alpha_bbox={abbox} nonwhite_bbox=({minx},{miny},{maxx},{maxy}) w={maxx-minx} h={maxy-miny}")
