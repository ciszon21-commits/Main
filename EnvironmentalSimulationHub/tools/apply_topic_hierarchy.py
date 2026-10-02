"""Apply explicit presentation roles; no input/execution/solver changes."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'src/EnvironmentalHub.Plugin'
roles={
 'RadiationPanel.cs':{'01  GEOMETRY / MODEL':('01  Geometry / Model','Model'),'02  ENVIRONMENT / WEATHER':('02  Environment / Weather','Environment'),'03  SIMULATION SETTINGS':('03  Simulation settings','Settings'),'04  VALIDATE / RUN':('04  Validate / Run','Run'),'05  RESULTS':('05  Results','Results'),'06  COMPARE / EXPORT':('06  Compare / Export','Compare')},
 'LocationPanel.cs':{'01  Location inputs':('01  Location inputs','Environment'),'02  Construct':('02  Construct','Run'),'03  Result':('03  Result','Results')},
 'WeatherPanel.cs':{'01  Weather source':('01  Weather source','Environment'),'02  Time selection':('02  Time selection','Settings'),'03  Import':('03  Import','Run'),'04  Weather data':('04  Weather data','Results')},
 'ClimateFilePanel.cs':{'01  Source':('01  Source','Environment'),'02  Import':('02  Import','Run'),'03  Climate conditions':('03  Climate conditions','Results')},
 'TimePanel.cs':{'01  Operation':('01  Operation','Settings'),'02  Analysis period':('02  Analysis period','Settings'),'02  Calendar conversion':('02  Calendar conversion','Settings'),'03  Calculate':('03  Calculate','Run'),'04  Result':('04  Result','Results')}}
for filename,sections in roles.items():
 p=root/filename;s=p.read_text(encoding='utf-8')
 for old,(title,topic) in sections.items():
  import re
  s=re.sub(r'Section\("'+re.escape(old)+r'",(?!\s*HubTopic\.)','Section("'+title+'",HubTopic.'+topic+',',s)
 s=s.replace('Section(string title, params Control[] controls) => HubUi.Section(title, controls)',
             'Section(string title, HubTopic topic, params Control[] controls) => HubUi.Section(title, topic, controls)')
 # Header descriptions are single-line literals, so match only the header call.
 import re
 s=re.sub(r'HubUi.Header\(("[^"\n]*",\s*"[^"\n]*")\)',lambda m:'HubUi.Header('+m[1]+',typeof('+filename[:-3]+'))',s)
 p.write_text(s,encoding='utf-8')
