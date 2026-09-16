from PIL import Image, ImageDraw
import os
OUT="output/analysis"; os.makedirs(OUT,exist_ok=True)
for v in ["front","back","left","right","top","bottom"]:
    im=Image.open(f"views/{v}.png").convert("RGBA")
    bg=Image.new("RGBA",im.size,(255,255,255,255))
    im=Image.alpha_composite(bg,im).convert("RGB")
    d=ImageDraw.Draw(im)
    W,H=im.size
    for x in range(0,W,100):
        c=(255,0,0) if x%500==0 else (255,180,180)
        d.line([(x,0),(x,H)],fill=c,width=2 if x%500==0 else 1)
        if x%200==0: d.text((x+3,4),str(x),fill=(200,0,0))
    for y in range(0,H,100):
        c=(0,0,255) if y%500==0 else (180,180,255)
        d.line([(0,y),(W,y)],fill=c,width=2 if y%500==0 else 1)
        if y%200==0: d.text((4,y+3),str(y),fill=(0,0,200))
    im.save(f"{OUT}/{v}_grid.png")
print("done")
