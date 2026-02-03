"""
管材粗糙係數資料
Pipe material roughness coefficient data
"""

# 粗糙係數選項 (Roughness coefficient options)
PIPE_MATERIALS = [
    ('0.013', '塑化管/鋼管/平滑混凝土'),
    ('0.015', '一般混凝土管'),
    ('0.012', '內襯/玻璃纖維管'),
    ('0.011', '極平滑PE/PVC'),
]

def get_pipe_materials():
    """返回管材粗糙係數選項列表"""
    return PIPE_MATERIALS

def get_roughness_value(material_key):
    """根據管材類型獲取粗糙係數值"""
    for key, name in PIPE_MATERIALS:
        if key == material_key:
            return float(key)
    return None
