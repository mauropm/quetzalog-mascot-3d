from PIL import Image, ImageDraw
import os, sys
PROJ="/Users/mauro/Documents/Code/3D-Quetzalog"
CMP=os.path.join(PROJ,"output","comparison")
VIEWS=["front","back","left","right","top","bottom"]
SC=0.40

def load_alpha(p):
    return Image.open(p).convert("RGBA")

def comp_white(im):
    bg=Image.new("RGBA",im.size,(255,255,255,255))
    return Image.alpha_composite(bg,im).convert("RGB")

def silhouette(im):
    return im.split()[3].point(lambda a:255 if a>40 else 0)

for v in VIEWS:
    mod=load_alpha(os.path.join(CMP,"model_%s.png"%v))
    W,H=mod.size
    ref=load_alpha(os.path.join(PROJ,"views",v+".png")).resize((W,H))
    rmask=silhouette(ref); mmask=silhouette(mod)
    refw=comp_white(ref); modw=comp_white(mod)
    ov=Image.new("RGB",(W,H),(255,255,255))
    rp=rmask.load(); mp=mmask.load(); op=ov.load()
    for y in range(H):
        for x in range(W):
            a=rp[x,y]>0; b=mp[x,y]>0
            if a and b: op[x,y]=(110,110,110)
            elif a: op[x,y]=(235,60,60)
            elif b: op[x,y]=(60,110,235)
    tw,th=int(W*SC),int(H*SC)
    refs=refw.resize((tw,th)); mods=modw.resize((tw,th)); ovs=ov.resize((tw,th))
    sheet=Image.new("RGB",(tw*3+24,th+26),(255,255,255))
    sheet.paste(refs,(0,22)); sheet.paste(mods,(tw+12,22)); sheet.paste(ovs,(tw*2+24,22))
    d=ImageDraw.Draw(sheet)
    d.text((4,4),f"{v.upper()}   REFERENCE  |  MODEL  |  OVERLAY (red=ref only, blue=model only)",fill=(0,0,0))
    sheet.save(os.path.join(CMP,"cmp_%s.png"%v))
    # gray-clay sheet
    clay=comp_white(load_alpha(os.path.join(CMP,"clay_%s.png"%v))).resize((tw,th))
    sh2=Image.new("RGB",(tw*2+12,th+26),(255,255,255))
    sh2.paste(refs,(0,22)); sh2.paste(clay,(tw+12,22))
    ImageDraw.Draw(sh2).text((4,4),f"{v.upper()}   REFERENCE  |  CLAY MODEL",fill=(0,0,0))
    sh2.save(os.path.join(CMP,"clay_cmp_%s.png"%v))
    rb=rmask.getbbox(); mb=mmask.getbbox()
    print(f"{v:7s} ref w={rb[2]-rb[0]:4d} h={rb[3]-rb[1]:4d}  |  model w={mb[2]-mb[0]:4d} h={mb[3]-mb[1]:4d}"
          f"   dx={((mb[0]+mb[2])-(rb[0]+rb[2]))//2:+4d} dy={((mb[1]+mb[3])-(rb[1]+rb[3]))//2:+4d}")
print("SHEETS DONE")
