from django.conf import settings
from django.utils import timezone

from SinoArchive import models as ArchiveModels

import os, re





MEDIA_ROOT = settings.MEDIA_ROOT
STATIC_URL = settings.STATIC_URL


HAS_IMAGE_EXTENSIONS = [
    '.csv', '.dgn', '.dic', '.dwg', '.forge', '.ifc', '.pdf', '.pptx', '.ppt'
    '.rvt', '.svg', '.nwd', '.txt', '.xls', '.zip',
]
IMAGE_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.bmp',
]
VIDEO_EXTENSIONS = ['.mp4']

GIS_BASE_EXTENSIONS = [
    '.json', '.geojson', '.shp',
]
GIS_EXTENSIONS = [
    # GeoJsone
    '.json', '.geojson',
    # Shapefile
    '.shp', '.shx', '.sbx', '.dbf', '.prj', '.sbn',
]

DATA_EXTENSIONS = ['.json', '.txt', '.attr']
MODEL_EXTENSIONS = ['.3dm', '.dwfx']
COLOR_EXTENSIONS = ['.colorscheme']

SIZE_UNITS = {
    'b': 'KB',
    'KB': 'MB',
    'MB': 'GB',
    'GB': 'TB',
    'TB': '--',
    '--': '--',
}



def checkFile(fileUrl, checkString):
    checkString = checkString if isinstance(checkString, list) else [checkString]
    checkString = [cs.lower() for cs in checkString]
    return True if re.findall(r'\.[^.]+$', str(fileUrl))[0].lower() in checkString else False
def fileName(fileName):
    basename = os.path.basename(fileName)
    filename, fileex = os.path.splitext(basename)
    return filename
def fileSuffix(_file):
    _file = fileName(_file.name)
    return fileSuffixStr(_file)
def fileSuffixStr(fileName):
    return fileName[fileName.rfind('_'):]
def fileExtension(fileName):
    name, ex = os.path.splitext(fileName)
    return ex
def ignoreExtension(fileName):
    index = fileName.rfind('.')
    return fileName if index == -1 else fileName[:index]
def ignoreSuffix(fileName):
    index = fileName.rfind('_')
    return ignoreExtension(fileName) if index == -1 else fileName[:index]
def ignoreSuffixSame(fileNameA, fileNameB):
    return ignoreSuffix(fileNameA).lower() == ignoreSuffix(fileNameB).lower()

hasImageExtension = HAS_IMAGE_EXTENSIONS
imageExtension = IMAGE_EXTENSIONS
def isImage(fileName):
    if fileName.startswith('.'): return fileName.lower() in imageExtension
    return fileExtension(fileName).lower() in imageExtension
videoExtension = VIDEO_EXTENSIONS
def isVideo(fileName):
    if fileName.startswith('.'): return fileName.lower() in videoExtension
    return fileExtension(fileName).lower() in videoExtension
gisBaseExtension = GIS_BASE_EXTENSIONS
gisExtension = GIS_EXTENSIONS
def isGisBase(fileName):
    if fileName.startswith('.'): return fileName.lower() in gisBaseExtension
    return fileExtension(fileName).lower() in gisBaseExtension
def isGis(fileName):
    if fileName.startswith('.'): return fileName.lower() in gisExtension
    return fileExtension(fileName).lower() in gisExtension


dataExtension = DATA_EXTENSIONS
modelExtension = MODEL_EXTENSIONS
colorExtension = COLOR_EXTENSIONS
def isDataFile(fileName:'str') -> 'bool':
    if fileName.startswith('.'): return fileName.lower() in dataExtension
    return fileExtension(fileName).lower() in dataExtension
def isModelFile(fileName:'str') -> 'bool':
    if fileName.startswith('.'): return fileName.lower() in modelExtension
    return fileExtension(fileName).lower() in modelExtension
def isColorFile(fileName:'str') -> 'bool':
    if fileName.startswith('.'): return fileName.lower() in colorExtension
    return fileExtension(fileName).lower() in colorExtension
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

_unit = SIZE_UNITS
def size_format(_fileSize:'int|float', _fileUnit:'str'='b') -> 'str':
    if not _fileSize: _fileSize = 0
    if _fileSize > 1024:
        return size_format(_fileSize / 1024, _unit.get(_fileUnit))
    return '%.2f %s' %(_fileSize, _fileUnit)

def setFileLocalPath(path:'str'):
    # 標準化路徑格式，適用於所有作業系統
    path = os.path.normpath(path).replace(os.sep, '/')
    pattern = r'media/(.+)'
    pp = re.search(pattern, path)
    if not pp: return path
    groups = pp.groups()
    if not groups: return path
    return groups[0]
def getGileFullLocalPath(path):
    lPath = setFileLocalPath(path)
    lPath = os.path.join(MEDIA_ROOT, lPath)
    if os.path.isfile(lPath): return lPath
    aPath = ArchiveModels.ArchiveFile.objects.get_archive_path(path)
    if os.path.isfile(aPath): return aPath
    return ''

def setTimeFileName(fileName):
    now = timezone.now().timestamp()
    names = re.split(r'\.', fileName)
    if len(names) < 2: return '{}_{:.0f}'.format(fileName, now)
    names[-2] = '{}_{:.0f}'.format(names[-2], now)
    return '.'.join(names)

def toMediaPath(filePath):
    # 跨平台處理，標準化路徑格式
    filePath = os.path.normpath(filePath).replace(os.sep, '/')
    mFind = 'media/'
    index = filePath.find(mFind)
    si = index+len(mFind) if index != -1 else 0
    print("檢核通過")
    return filePath[si:]

def getFileFieldImage(fileField):
    fileUrl = fileField.url
    filename = os.path.basename(fileUrl)
    filename, fileex = os.path.split(filename)
    if isImage(fileUrl): return fileUrl
    fileEx = fileex[1:] if fileex in hasImageExtension else 'file'
    fileEx = f'{fileEx}1' if fileEx=='ifc' else fileEx
    return f'{STATIC_URL}file_image/{fileEx}.png'

def filterDirFilesByExtension(dirPath:'str', targetEx:'str') -> 'list[str]':
    files = []
    targetEx = targetEx if targetEx.startswith('.') else '.%s' %(targetEx)
    for dirpath, dirname, filenames in os.walk(dirPath):
        for filename in filenames:
            fname, fex = os.path.splitext(filename)
            if fex.lower() != targetEx.lower(): continue
            files.append(filename)
    return files


def getDisplayImage(file):
    fileUrl = file.url
    extension = fileExtension(fileUrl)
    if isImage(fileUrl): return fileUrl
    fileEx = extension[1:] if extension in hasImageExtension else 'file'
    fileEx = f'{fileEx}1' if fileEx=='ifc' else fileEx
    return f'{STATIC_URL}file_image/{fileEx}.png'

