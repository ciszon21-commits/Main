from django.shortcuts import render
from django.contrib import messages
from .services import find_duplicates

def index(request):
    context = {}
    if request.method == 'POST':
        folder_path = request.POST.get('folder_path', '').strip()
        if not folder_path:
            messages.error(request, "請輸入資料夾路徑。")
        else:
            try:
                # Strip surrounding quotes if the user pasted from "Copy as path"
                if folder_path.startswith('"') and folder_path.endswith('"'):
                    folder_path = folder_path[1:-1]
                
                duplicates = find_duplicates(folder_path)
                context['duplicates'] = duplicates
                context['scanned_path'] = folder_path
                context['has_scanned'] = True
                
                if not duplicates:
                    messages.success(request, f"掃描完成！在 {folder_path} 中未發現重複檔案。")
                else:
                    messages.warning(request, f"掃描完成！在 {folder_path} 發現 {len(duplicates)} 組重複檔案。")
                    
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"發生錯誤: {str(e)}")
                
    return render(request, 'duplicate_checker/index.html', context)
