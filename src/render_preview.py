"""Draw a static BI design preview from computed aggregate tables using Pillow.

This file generates a reproducible visualization, not an application screenshot.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG='#F3F6F8'
INK='#152F45'
MUTED='#536B7B'
TEAL='#087F8C'
ORANGE='#B45C24'
RULE='#DAE4EB'


def render_preview(root,k,services,monthly,backlog):
    im=Image.new('RGB',(1600,1120),BG)
    d=ImageDraw.Draw(im)
    fonts={}
    def font(size,bold=False):
        key=(size,bold)
        if key not in fonts:
            filename='segoeuib.ttf' if bold else 'segoeui.ttf'
            candidates=[Path('C:/Windows/Fonts')/filename,
                Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
            candidate=next((p for p in candidates if p.exists()),None)
            fonts[key]=ImageFont.truetype(str(candidate),size) if candidate else ImageFont.load_default(size=size)
        return fonts[key]
    def text(x,y,value,size=20,color=INK,bold=False):
        d.text((x,y),str(value),font=font(size,bold),fill=color)
    def right(x,y,value,size=20,color=INK,bold=False):
        width=d.textlength(str(value),font=font(size,bold))
        text(x-width,y,value,size,color,bold)
    def card(box):
        d.rounded_rectangle(box,radius=15,fill='white',outline=RULE,width=1)
    d.rectangle((0,0,1600,9),fill=TEAL)
    text(44,35,'AUSTIN 311',17,TEAL,True)
    text(44,65,'Service Operations Analytics',38,INK,True)
    text(44,116,'2025-created requests  |  Statuses observed in November 7, 2026 export',21,MUTED)
    right(1554,44,'PYTHON  /  SQL  /  BI MODEL',15,MUTED,True)
    values=[('PRIMARY REQUESTS',f"{k['primary_requests']:,}",'Nonduplicate, nontesting'),
            ('REPORTED CLOSED',f"{k['closed_requests']:,}",'Administrative status'),
            ('REPORTED OPEN',f"{k['open_backlog']:,}",'2025-created cohort only'),
            ('MEDIAN CLOSURE',f"{k['median_closure_days']*24:.2f} h",f"Eligible closed: {int(k['duration_eligible_closed']):,}"),
            ('P90 CLOSURE',f"{k['p90_closure_days']:.2f} d",'Elapsed calendar time')]
    for i,(label,value,note) in enumerate(values):
        x=44+i*305
        card((x,165,x+290,307))
        text(x+21,181,label,16,MUTED,True)
        text(x+20,210,value,39,TEAL if i!=2 else ORANGE,True)
        text(x+21,270,note,16,MUTED)

    card((44,332,790,747))
    text(68,353,'Where reported demand is concentrated',24,INK,True)
    text(68,390,'Top five services · primary request count',17,MUTED)
    top=services.head(5)
    biggest=int(top['requests'].max())
    for i,r in enumerate(top.itertuples()):
        y=435+i*58
        text(68,y,r.service_description.removeprefix('TPW - '),18,INK)
        right(761,y,f'{r.requests:,}',19,INK,True)
        d.rounded_rectangle((68,y+30,760,y+40),radius=4,fill='#E8EFF3')
        d.rounded_rectangle((68,y+30,68+692*r.requests/biggest,y+40),radius=4,fill=TEAL)

    card((812,332,1556,747))
    text(836,353,'When requests were created',24,INK,True)
    text(836,390,'2025 monthly intake · primary requests',17,MUTED)
    x0,x1,y0,y1=886,1513,445,672
    for tick in [0,2000,4000,6000,8000]:
        y=y1-(y1-y0)*tick/8000
        d.line((x0,y,x1,y),fill=RULE,width=1)
        right(x0-14,y-12,f'{tick//1000}k',16,MUTED)
    points=[]
    for i,r in enumerate(monthly.itertuples()):
        x=x0+(x1-x0)*i/11
        y=y1-(y1-y0)*r.requests/8000
        points.append((x,y))
        text(x-10,y1+12,str(i+1),16,MUTED)
    d.line(points,fill=TEAL,width=4)
    for x,y in points:
        d.ellipse((x-5,y-5,x+5,y+5),fill=TEAL)
    peak=int(monthly['requests'].idxmax())
    x,y=points[peak]
    text(x-32,y-32,f"{int(monthly.iloc[peak]['requests']):,}",18,TEAL,True)
    text(890,711,'Month of creation (January–December)',16,MUTED)

    card((44,770,980,1037))
    text(68,790,'Service-specific closure intervals',24,INK,True)
    text(68,828,'Long intervals warrant review alongside each service’s recorded targets.',17,MUTED)
    right(778,867,'MEDIAN DAYS',15,MUTED,True)
    right(950,867,'P90 DAYS',15,MUTED,True)
    lookup=services.set_index('service_description')
    chosen=[('TPW - Road Markings/Striping - Maintenance','Striping — Maintenance'),
            ('TPW - Traffic Sign New','Traffic Sign — New'),
            ('TPW - Speed Management','Speed Management')]
    for i,(key,label) in enumerate(chosen):
        r=lookup.loc[key]
        y=901+i*39
        text(68,y,label,19,INK)
        right(778,y,f"{r['median_closure_days']:.2f}",20,INK,True)
        right(950,y,f"{r['p90_closure_days']:.2f}",20,INK,True)

    card((1002,770,1556,1037))
    text(1026,790,'Verify the reported open records',23,INK,True)
    cluster=int(backlog['created_local'].str.slice(0,10).between('2025-05-01','2025-05-05').sum())
    text(1026,835,f'{cluster} of {len(backlog)}',35,ORANGE,True)
    text(1026,883,'were created May 1–5, 2025.',19,INK)
    text(1026,915,'Old update dates support checking the live',18,MUTED)
    text(1026,943,'system before assigning recovery work.',18,MUTED)
    text(1026,991,'Closure does not verify resolution.',18,TEAL,True)
    text(44,1060,'SOURCE  City of Austin · 38mr-dwji     |     Static analytical preview — not a Power BI report',17,MUTED)
    text(44,1087,'Fixed age cutoff: Nov 7, 2026, 00:00 CT. Counts and times use the documented primary-cohort definitions.',16,MUTED)
    im.save(root/'reports/dashboard_preview.png',optimize=True)
