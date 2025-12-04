import os
import platform





def normalize_cross_platform_path(path:'str', base_mount:'str'='/mnt') -> 'str':
    """將路徑轉換為適合當前作業系統的格式"""
    # 自動檢測作業系統，而非依賴設定檔
    is_windows = platform.system() == 'Windows'
    is_linux = platform.system() == 'Linux'

    # 標準化路徑分隔符
    normalized_path = os.path.normpath(path)

    # 如果當前是 Linux 系統且路徑是 Windows UNC 格式，則轉換
    if is_linux and (normalized_path.startswith('\\\\') or '\\' in normalized_path):
        # 處理UNC路徑格式 (\\server\share\path)
        if normalized_path.startswith('\\\\'):
            # 移除開頭的 \\ 並分割
            path_without_prefix = normalized_path[2:]
            parts = path_without_prefix.replace('\\', '/').split('/')
        else:
            # 普通路徑，將反斜線轉換為正斜線後分割
            parts = normalized_path.replace('\\', '/').split('/')

        # 過濾空字串
        parts = [p for p in parts if p]

        # 至少要有 server 和 share 名稱
        if len(parts) < 2:
            raise ValueError(f"路徑格式錯誤，至少需要 \\\\server\\share，收到: {path}")

        # 提取 share 名稱並進行名稱對應轉換
        original_share = parts[1]
        # 特殊規則：filed -> field
        share = 'field' if original_share == 'filed' else original_share
        sub_path = '/'.join(parts[2:]) if len(parts) > 2 else ''

        # 組合為 Linux 掛載路徑
        if sub_path:
            unix_path = f'{base_mount}/{share}/{sub_path}'
        else:
            unix_path = f'{base_mount}/{share}'

        return os.path.normpath(unix_path)

    # 如果當前是 Windows 系統或路徑已經是正確格式，直接返回標準化後的路徑
    return normalized_path



