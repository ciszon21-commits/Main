"""Apply shared spacing tokens to the four existing native panels."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'src/EnvironmentalHub.Plugin'
for name in ['RadiationPanel.cs','WeatherPanel.cs','LocationPanel.cs','ClimateFilePanel.cs']:
 path=root/name;text=path.read_text(encoding='utf-8')
 text=text.replace('Padding = 10, Spacing = new Size(8, 8)','Padding = 12, Spacing = new Size(8, 8)')
 text=text.replace('Padding = 14, Spacing = new Size(8, 12)','Padding = 16, Spacing = new Size(8, 14)')
 text=text.replace('TextColor = SystemColors.DisabledText','TextColor = SystemColors.ControlText')
 path.write_text(text,encoding='utf-8')
