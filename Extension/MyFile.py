from django.utils import timezone

import os, re



def checkFile(fileUrl, checkString):
    checkString = checkString if isinstance(checkString, list) else [checkString]
    checkString = [cs.lower() for cs in checkString]
    return True if re.findall(r'\.[^.]+$', str(fileUrl))[0].lower() in checkString else False
def fileName(fileName):
    return fileName[:fileName.find('.')] if not fileName.find('.') == -1 else fileName
def fileSuffix(_file):
    _file = fileName(_file.name)
    return fileSuffixStr(_file)
def fileSuffixStr(fileName):
    return fileName[fileName.rfind('_'):]
def fileExtension(fileName):
    # name, ex = os.path.splitext(fileName)
    name, ex = os.path.split(fileName)
    # return ex.lower()
    index = fileName.rfind('.')
    return fileName if index == -1 else fileName[index:]
def ignoreExtension(fileName):
    index = fileName.rfind('.')
    return fileName if index == -1 else fileName[:index]
def ignoreSuffix(fileName):
    index = fileName.find('_')
    return ignoreExtension(fileName) if index == -1 else fileName[:index]
def ignoreSuffixSame(fileNameA, fileNameB):
    return ignoreSuffix(fileNameA).lower() == ignoreSuffix(fileNameB).lower()

hasImageExtension = [
    '.csv', '.dgn', '.dic', '.dwg', '.forge', '.ifc', '.pdf', '.pptx', '.ppt'
    '.rvt', '.svg', '.nwd', '.txt', '.xls', '.zip'
]
imageExtension = ['.jpg', '.jpeg', '.png', '.gif','.bmp']
def isImage(fileName:'str') -> 'bool':
    return fileExtension(fileName).lower() in imageExtension
videoExtension = ['.mp4']
def isVideo(fileName:'str') -> 'bool':
    return fileExtension(fileName).lower() in videoExtension
audioExtension = ['.mp3']
def isAudio(fileName:'str') -> 'bool':
    return fileExtension(fileName).lower() in audioExtension
archiveExtension = ['.zip', '.rar']
def isArchive(fileName:'str') -> 'bool':
    return fileExtension(fileName).lower() in archiveExtension
gisBaseExtension = [
    '.json', '.geojson', '.shp',
]
gisExtension = [
    # GeoJsone
    '.json', '.geojson',
    # Shapefile
    '.shp', '.shx', '.sbx', '.dbf', '.prj', '.sbn',
]
def isGisBase(fileName:'str') -> 'bool':
    return fileExtension(fileName).lower() in gisBaseExtension
def isGis(fileName:'str') -> 'bool':
    return fileExtension(fileName).lower() in gisExtension


dataExtension = ['.json', '.txt', '.attr']
modelExtension = ['.3dm']
colorExtension = ['.colorscheme']
def isDataFile(fileName):
    return fileName[fileName.rfind('.'):].lower() in dataExtension
def isModelFile(fileName):
    return fileName[fileName.rfind('.'):].lower() in modelExtension
def isColorFile(fileName):
    return fileName[fileName.rfind('.'):].lower() in colorExtension
def similarFolderFile(fileName, folder):
    notModelExtension = dataExtension + colorExtension
    correspondExtension = notModelExtension if isModelFile(fileName) else modelExtension
    sameNameFile = {}
    for existFile in folder.allRequestFile:
        existFileName = existFile.file_name
        if ignoreSuffixSame(fileName, existFileName):
            if existFileName[existFileName.rfind('.'):] in correspondExtension:
                sameNameFile[existFile.id] = existFile.file_name
    return sameNameFile

_unit = {
    'b': 'KB', 'KB': 'MB', 'MB': 'GB', 'GB': 'TB', 'TB': '--', '--': '--',
}
def size_format(_fileSize, _fileUnit='b'):
    if not _fileSize: _fileSize = 0
    if _fileSize > 1024:
        return size_format(_fileSize / 1024, _unit.get(_fileUnit))
    return '%.2f %s' %(_fileSize, _fileUnit)

def setFileLocalPath(path):
    path = re.sub(r'\\', '/', path)
    pattern = r'media\/(.+)'
    pp = re.search(pattern, path)
    if not pp: return path
    groups = pp.groups()
    if not groups: return path
    return groups[0]

def setTimeFileName(fileName):
    now = timezone.now().timestamp()
    names = re.split(r'\.', fileName)
    if len(names) < 2: return '{}_{:.0f}'.format(fileName, now)
    names[-2] = '{}_{:.0f}'.format(names[-2], now)
    return '.'.join(names)

def toMediaPath(filePath):
    mFind = 'media\\'
    index = filePath.find(mFind)
    si = index+len(mFind) if index != -1 else 0
    return filePath[si:]
