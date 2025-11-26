from django.db.models import query

from . import models

def callForgeModelFunction(request):
    data = request.POST.dict()
    data = data if data else request.GET.dict()
    modelName = data.get('model', '')
    if not hasattr(models, modelName): return None
    model = getattr(models, modelName)
    id = data.get('id', data.get('pk', ''))
    if not id: return None
    model = model.objects.filter(id=id).first()
    if not model: return None
    function = data.get('function', '')
    if not hasattr(model, function): return None
    return getattr(model, function)()

def getViewKwargsData(request, **kwargs):
    data = {}
    data = getArchiveFolderKwargsData(data, request, **kwargs)
    data = getArchiveFoldersKwargsData(data, request, **kwargs)
    return data
def getArchiveFolderKwargsData(data, request, **kwargs):
    if not kwargs.get('aFolId'): return data
    data['aFolder'] = models.ArchiveFolder.objects.get(pk=kwargs['aFolId'])
    return data
def getArchiveFoldersKwargsData(data, request, **kwargs):
    data['archFolders'] = models.ArchiveFolder.objects.all()
    return data






######################################################################################
#
#    `+ossso+/:`               .syys-                                  +sss/
#    .NMMMMMMMMMmds.           oMMMMo                                 `mMMM+
#    -NMMMd///+mMMMNo`          .:/.                                  .NMMM:
#    -NMMMy    `yMMMMs         :hhys.           `:shddddyo-     -sssssyMMMMyssss-
#    :NMMMs     .NMMMN-        sMMMM-         .hMMMMNmNMMMMN:   +NMMNNMMMMMNNNNN+
#    :NMMMs      dMMMM/        hMMMN-        /NMMMo.`  .+MMMN-  `...``sMMMd``````
#    +MMMMo      hMMMM/        NMMMm.       :MMMM/       smmd+       `hMMMs
#    +MMMM+     `mMMMN:       .MMMMm.       sMMMN`                   `dMMMo
#    oMMMM/     sMMMMh`       :MMMMd`       sMMMN`        .`         -NMMN:
#    oMMMM:   `oMMMMm.        +MMMMd`       -NMMMs`     `/Nm+`       :MMMN-
#    sMMMMyosdMMMMNy`         sMMMMd`        -mMMMmo::/sNMMNh-       /MMMMyooooo/
#    yNMMMMMNNNNh+`          `yNNNNh`          /dNNMMMMNNm+`         `omNNNNNNNNy
#     `.....`                                     `.---`
#
######################################################################################
def setObject2Json(data):
    if isinstance(data, list):
        return setList2Json(data)
    elif isinstance(data, dict):
        return setDict2Json(data)
    elif isinstance(data, query.QuerySet):
        return setQS2Json(data)
    elif isinstance(data, bool) or data is None:
        return data
    return str(data)
def setDict2Json(data):
    for k, v in data.items():
        value = None
        if isinstance(v, list):
            value = setList2Json(v)
        elif isinstance(v, dict):
            value = setDict2Json(v)
        elif isinstance(v, query.QuerySet):
            value = setQS2Json(v)
        else:
            value = setObject2Json(v)
        data[k] = value
    return data
def setList2Json(items):
    result = []
    for item in items:
        value = None
        if isinstance(item, list):
            value = setList2Json(item)
        elif isinstance(item, dict):
            value = setDict2Json(item)
        elif isinstance(item, query.QuerySet):
            value = setQS2Json(item)
        else:
            value = setObject2Json(item)
        result.append(value)
    return result
def setQS2Json(items):
    items = list(items)
    return setList2Json(items)
