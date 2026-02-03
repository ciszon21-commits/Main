# Fix views.py encoding issue
import os

# Read the original file up to line 950 (before the corrupted content)
with open('EngineerRPG/views.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find where the corruption starts (around line 950)
clean_lines = []
for i, line in enumerate(lines):
    if i < 950:  # Keep only the original content
        clean_lines.append(line)
    else:
        break

# Write back the clean content
with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)

# Now append the new view functions with proper encoding
new_views = '''

# ==================== 題庫管理 ====================

@login_required
def create_question_view(request):
    """建立題目"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, '您沒有權限訪問此頁面！')
        return redirect('engineer_rpg:dashboard')
    
    from .forms import QuestionForm
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '題目建立成功！')
            return redirect('engineer_rpg:question_management')
    else:
        form = QuestionForm()
    
    return render(request, 'EngineerRPG/create_question.html', {'profile': profile, 'form': form})


@login_required
def import_questions_view(request):
    """批次匯入題目"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, '您沒有權限訪問此頁面！')
        return redirect('engineer_rpg:dashboard')
    
    from .forms import QuestionImportForm
    from .utils.question_importer import QuestionImporter
    
    if request.method == 'POST':
        form = QuestionImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            importer = QuestionImporter()
            try:
                result = importer.import_from_file(file)
                if result['success'] > 0:
                    messages.success(request, f'成功匯入 {result["success"]} 筆題目！')
                if result['skip'] > 0:
                    messages.warning(request, f'跳過 {result["skip"]} 筆題目')
                if result['errors']:
                    for error in result['errors'][:5]:
                        messages.error(request, error)
                return redirect('engineer_rpg:question_management')
            except Exception as e:
                messages.error(request, f'匯入失敗：{str(e)}')
    else:
        form = QuestionImportForm()
    
    return render(request, 'EngineerRPG/import_questions.html', {'profile': profile, 'form': form})


@login_required
def download_template(request, format='csv'):
    """下載題目匯入範本"""
    from .utils.question_importer import generate_template_csv, generate_template_excel
    
    if format == 'csv':
        response = HttpResponse(generate_template_csv(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="question_template.csv"'
    elif format == 'excel':
        output = generate_template_excel()
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="question_template.xlsx"'
    else:
        messages.error(request, '不支援的格式')
        return redirect('engineer_rpg:question_management')
    
    return response
'''

with open('EngineerRPG/views.py', 'a', encoding='utf-8') as f:
    f.write(new_views)

print("✅ views.py fixed successfully!")
