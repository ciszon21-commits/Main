"""Native UI-thread reflection: check actual host colors and opaque palette tokens."""
import System, Rhino, json, os, clr
clr.AddReference('Eto')
from Eto.Drawing import SystemColors
from Eto.Forms import Label
flags=System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic
plugin=Rhino.PlugIns.PlugIn.Find(System.Guid('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f'))
a=plugin.GetType().Assembly
visual=a.GetType('EnvironmentalHub.Plugin.HubVisuals')
topic=a.GetType('EnvironmentalHub.Plugin.HubTopic')
def rgb(c):return [float(c.R),float(c.G),float(c.B)]
def lum(v):
    q=[x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in v]
    return sum(x*y for x,y in zip(q,[.2126,.7152,.0722]))
def contrast(x,y):
    u,v=sorted([lum(x),lum(y)])
    return (v+.05)/(u+.05)
bg=rgb(SystemColors.ControlBackground)
tokens=[]
for name in System.Enum.GetNames(topic):
    t=System.Enum.Parse(topic,name)
    native=visual.GetMethod('Accent',flags).Invoke(None,System.Array[System.Object]([t]))
    ratio=contrast(rgb(native),bg)
    assert float(native.A)==1 and ratio>=4.5,(name,ratio)
    item={'topic':name,'host_rgb':rgb(native),'host_contrast':ratio}
    for dark,background in [(False,[1,1,1]),(True,[32/255,36/255,42/255])]:
        c=visual.GetMethod('Palette',flags).Invoke(None,System.Array[System.Object]([t,System.Boolean(dark)]))
        value=contrast(rgb(c),background)
        assert float(c.A)==1 and value>=4.5,(name,dark,value)
        item['dark_token_contrast' if dark else 'light_token_contrast']=value
    tokens.append(item)
secondary=visual.GetProperty('Secondary',flags).GetValue(None)
assert float(secondary.A)==1 and contrast(rgb(secondary),bg)>=4.5
def walk(c):
    yield c
    if hasattr(c,'Controls'):
        for child in c.Controls:
            for nested in walk(child):yield nested
literal_titles=[]
for guid,title in [('06843693-df8a-421c-938b-96e2b9e88066','Time & periods'),('499a99e8-8e73-4a6b-8208-fc879e413d36','Climate & design days')]:
    panel=Rhino.UI.Panels.GetPanel(System.Guid(guid))
    label=next(c for c in walk(panel) if isinstance(c,Label) and c.Text==title)
    assert not label.UseMnemonic
    literal_titles.append(title)
report={'version':str(a.GetName().Version),'host_background_rgb':bg,'host_dark':bool(visual.GetProperty('Dark',flags).GetValue(None)),
        'tokens':tokens,'secondary_host_contrast':contrast(rgb(secondary),bg),'literal_titles_verified':literal_titles,
        'scope':'Actual current-host heading/secondary colors plus token math on white / #20242A; native dark-theme switching not tested.'}
path='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub/docs/evidence/topic_085_palette.json'
json.dump(report,open(path,'w',encoding='utf-8'),indent=2)
print(json.dumps(report))
