import re
def is_valid_page_format(page_string):
    # 檢查頁碼格式是否符合規範
    pattern = re.compile(r'^(\d+)(,\d+)*(-\d+)?(,\d+(-\d+)?)*$')
    return bool(pattern.match(page_string))
def expand_page_range(page_string):
    if not is_valid_page_format(page_string):
        raise ValueError("Invalid page format")
    
    pages = []
    parts = page_string.split(',')
    
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    
    return pages