import os
from django import template
from django.templatetags.static import static

register = template.Library()


@register.filter
def equipment_icon_url(icon_value):
    """
    將資料庫中的 icon 路徑轉換為 static URL。
    支援：
      - media 路徑: rpg/equipment_icons/helmet.png
      - 純檔名: helmet.png
      - 已是正確 static 路徑: EngineerRPG/img/equipment_icons/helmet.png
    """
    if not icon_value:
        return ''

    icon_value = str(icon_value)

    # 已經是正確的 static 路徑
    if icon_value.startswith('EngineerRPG/img/equipment_icons/'):
        return static(icon_value)

    # 取得檔名
    filename = os.path.basename(icon_value)
    static_path = f'EngineerRPG/img/equipment_icons/{filename}'
    return static(static_path)
