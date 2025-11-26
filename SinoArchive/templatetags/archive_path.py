from django import template
from django.conf import settings

from SinoArchive import models as ArchiveModels

import os, re

register = template.Library()


@register.filter
def archive_path(url):
    url = setMediaPath(url)
    media = os.path.dirname(settings.MEDIA_ROOT)
    if os.path.isfile(f'{media}{url}'):
        return url
    aUrl = ArchiveModels.ArchiveFile.objects.get_archive_path(url)
    if os.path.isfile(aUrl):
        return aUrl
    return ''


def setMediaPath(url):
    url = str(url)
    # 使用跨平台路徑分隔符處理
    urls = re.split(r'[/\\]', url)
    urls = [u for u in urls if u]

    if 'media' in urls:
        index = urls.index('media')
        urls = urls[index:]
        return '/' + '/'.join(urls)

    urls = ['media'] + urls
    return '/' + '/'.join(urls)
