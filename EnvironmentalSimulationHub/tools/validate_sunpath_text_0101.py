"""Detect inherited annotation scaling without changing document styles/settings."""
import os,json,System,Rhino
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
doc=__rhino_doc__;workspace=Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
panel=workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunPathPanel'))
old_enabled=doc.ModelSpaceAnnotationScalingEnabled
old_style=doc.DimStyles.Current.Duplicate()
try:
 # Deliberately use a scale that revealed the visual defect in 0.9.0.
 style=doc.DimStyles.Current.Duplicate();style.DimensionScale=100
 assert doc.DimStyles.Modify(style,doc.DimStyles.Current.Id,False)
 doc.ModelSpaceAnnotationScalingEnabled=True
 original_style=[(str(s.Id),s.DimensionScale,s.TextHeight) for s in doc.DimStyles]
 request=json.loads(panel.CompletedResultJson)['InputParameters']
 result=json.loads(panel.ExecuteJson(json.dumps(request)))
 assert doc.ModelSpaceAnnotationScalingEnabled and original_style==[(str(s.Id),s.DimensionScale,s.TextHeight) for s in doc.DimStyles]
 objects=[o for o in doc.Objects if str(o.Attributes.Name).startswith('EnvironmentalHub / SunPath') and isinstance(o.Geometry,Rhino.Geometry.TextEntity)]
 assert len(objects)==len(result['Texts'])
 ratios=[]
 for obj in objects:
  entity=obj.Geometry
  output=str(obj.Attributes.Name).split(' / ')[-1]
  t=next(t for t in result['Texts'] if t['Output']==output and t['Text']==entity.PlainText)
  assert entity.DimensionScale==1 and entity.IsPropertyOverridden(Rhino.DocObjects.DimensionStyle.Field.DimensionScale)
  assert abs(entity.TextHeight-t['Height'])<1e-8
  # A cardinal label cannot cover the whole sky dome due to a 100x parent scale.
  bounds=entity.GetBoundingBox(True);ratio=bounds.Diagonal.Length/(result['InputParameters']['RadiusMetres']/result['MetresPerModelUnit']);ratios.append(ratio)
  assert ratio<2.5,(t['Text'],ratio)
 report={'version':'0.10.1','passed':2,'cases':['per_owned_annotation_scale_and_native_height','document_styles_and_scaling_unchanged_by_run'],'parent_dimension_scale':100,'annotation_count':len(objects),'bound_to_radius_ratios':ratios}
 json.dump(report,open(os.path.join(root,'docs/evidence/sunpath_0101_text.json'),'w',encoding='utf-8'),indent=2)
 print(json.dumps(report))
finally:
 doc.DimStyles.Modify(old_style,old_style.Id,False);doc.ModelSpaceAnnotationScalingEnabled=old_enabled;old_style.Dispose();doc.Views.Redraw()
