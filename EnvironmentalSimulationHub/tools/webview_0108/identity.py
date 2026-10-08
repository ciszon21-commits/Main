from System.Reflection import Assembly
assembly = Assembly.LoadFrom('C:/Program Files/Rhino 8/System/Eto.Wpf.dll')
t = assembly.GetType('Eto.Wpf.Forms.Controls.WebView2Handler')
record = {'pid': System.Diagnostics.Process.GetCurrentProcess().Id,
          'document_serial': int(doc.RuntimeSerialNumber), 'object_count': doc.Objects.Count,
          'runtime': str(System.Environment.Version), 'rhino': str(Rhino.RhinoApp.Version),
          'handler_type_present': t is not None,
          'handler_properties': [str(p.Name) for p in t.GetProperties()] if t else [],
          'handler_fields': [str(p.Name) for p in t.GetFields()] if t else []}
json.dump(record, open(os.path.join(evidence, 'identity.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
