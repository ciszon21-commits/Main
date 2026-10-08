import os, json, System, Rhino, scriptcontext as sc
assert System.Diagnostics.Process.GetCurrentProcess().Id == __OWNED_PID__
test = sc.sticky['ESH_DEPLOY_0109']; doc = __rhino_doc__
assert doc.RuntimeSerialNumber == test['identity']['document_serial'] and doc.Path in (None, '')
model_ids = test['model_ids']
for obj in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject):
    assert obj.Id in model_ids or obj.Attributes.GetUserString('EnvironmentalHub.PreviewOwner') == 'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/SunHours', 'Unexpected object: stop cleanup'
test['panel'].DeletePreview()
for object_id in model_ids:
    obj = doc.Objects.FindId(object_id)
    if obj is not None and not obj.IsDeleted:
        assert int(obj.Geometry.DataCRC(0)) == test['crc'][str(object_id)]
        assert doc.Objects.Delete(object_id, True)
assert len(list(doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject))) == 0
Rhino.UI.Panels.ClosePanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'), doc)
json.dump({'pid':__OWNED_PID__,'document_serial':int(doc.RuntimeSerialNumber),'remaining_objects':0,'scope':'Only owned test geometry and tagged previews removed; registered package retained'}, open(os.path.join(root,'docs/evidence/deploy_0109/cleanup.json'), 'w', encoding='utf-8'), indent=2)
print(json.dumps({'remaining_objects':0,'ready_for_router_close':True}))
