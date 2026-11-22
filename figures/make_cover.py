"""Blog cover: Marker form questions, fixed-size vs heading chunks (results/runs.jsonl, tag full, kind=form)."""
import subprocess, sys
BG="#231c33"; CREAM="#fdf6ec"; SUB="#cdbfe6"; LAV="#d8b4fe"; PEACH="#fdba8c"; DIM="#4d4163"; PANEL="#352a46"
def grid(x0,y0,n,lit,col,s=20,g=5,per=21):
    out=[]
    for i in range(n):
        r,c=divmod(i,per)
        out.append(f'<rect x="{x0+c*(s+g)}" y="{y0+r*(s+g+7)}" width="{s}" height="{s}" rx="3" fill="{col if i<lit else DIM}"/>')
    return "\n".join(out)
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="810" viewBox="0 0 1440 810">
<rect width="1440" height="810" fill="{BG}"/>
<g font-family="Avenir Next">
<text x="125" y="152" font-size="62" font-weight="700" fill="{CREAM}">Same PDF parser, same forms</text>
<text x="128" y="220" font-size="34" font-weight="400" fill="{SUB}">Form questions answered correctly (Marker, 41 questions)</text>
<rect x="730" y="274" width="585" height="442" rx="16" fill="{PANEL}"/>
<line x1="730" y1="282" x2="730" y2="708" stroke="{PEACH}" stroke-width="2.5" stroke-dasharray="8 7"/>
<text x="130" y="380" font-size="42" font-weight="700" fill="{CREAM}">Fixed-size chunks</text>
<text x="124" y="560" font-size="150" font-weight="700" fill="{LAV}">28/41</text>
{grid(130,600,41,28,LAV)}
<text x="770" y="380" font-size="42" font-weight="700" fill="{CREAM}">Heading chunks</text>
<text x="764" y="560" font-size="150" font-weight="700" fill="{PEACH}">3/41</text>
{grid(770,600,41,3,PEACH)}
</g></svg>'''
open("cover.svg","w").write(svg)
subprocess.run(["rsvg-convert","-w","1440","-h","810","cover.svg","-o",sys.argv[1]],check=True)
