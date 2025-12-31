from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
import json

from .models import (
    DevTeam, DevTeamMember, Program, ProgramDatabase,
    FileLocation, DatabaseDesignDoc, DesignTable, DesignField, DatabaseServer,
    PlatformApi, ProgramApiUsage, VirtualEmployee
)
from .forms import (
    DevTeamForm, ProgramForm, ProgramDatabaseFormSet, FileLocationFormSet,
    DatabaseDesignDocForm, DesignTableFormSet, DesignFieldFormSet, DatabaseServerForm,
    PlatformApiForm, ProgramApiUsageFormSet, VirtualEmployeeForm, VirtualEmployeeRetireForm
)


def check_team_member(user, team):
    """檢查使用者是否為團隊成員"""
    return team.is_member(user) or team.is_creator(user)


def check_team_creator(user, team):
    """檢查使用者是否為團隊建立者"""
    return team.is_creator(user)


@login_required
def team_list(request):
    """團隊列表頁面 - 所有人都可以看到團隊名稱"""
    teams = DevTeam.objects.all()
    return render(request, 'ProgramDbRegistry/team_list.html', {
        'teams': teams
    })


@login_required
def team_detail(request, pk):
    """團隊詳情頁面 - 只有成員可以看到內容"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_member(request.user, team):
        return render(request, 'ProgramDbRegistry/team_access_denied.html', {
            'team': team
        })
    
    programs = team.programs.all()
    members = team.members.select_related('user').all()
    db_servers = DatabaseServer.objects.all()
    platform_apis = PlatformApi.objects.all()
    virtual_employees = team.virtual_employees.select_related('created_by').all()
    
    # Group programs by type for categorized display
    programs_by_type = {
        'web': {'label': '網頁平台', 'programs': [], 'icon': 'globe'},
        'desktop': {'label': '單機程式', 'programs': [], 'icon': 'desktop'},
        'plugin': {'label': '外掛程式', 'programs': [], 'icon': 'puzzle'},
    }
    
    for program in programs:
        if program.program_type in programs_by_type:
            programs_by_type[program.program_type]['programs'].append(program)
    
    return render(request, 'ProgramDbRegistry/team_detail.html', {
        'team': team,
        'programs': programs,
        'programs_by_type': programs_by_type,
        'members': members,
        'db_servers': db_servers,
        'platform_apis': platform_apis,
        'virtual_employees': virtual_employees,
        'is_creator': check_team_creator(request.user, team)
    })


@login_required
def team_create(request):
    """建立新團隊"""
    if request.method == 'POST':
        form = DevTeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.save()
            
            # 自動將建立者加入成員
            DevTeamMember.objects.create(
                team=team,
                user=request.user,
                role='creator'
            )
            
            messages.success(request, f'團隊「{team.name}」已成功建立！')
            return redirect('programdb:team_detail', pk=team.pk)
    else:
        form = DevTeamForm()
    
    return render(request, 'ProgramDbRegistry/team_form.html', {
        'form': form,
        'title': '建立新團隊',
        'is_edit': False
    })


@login_required
def team_update(request, pk):
    """編輯團隊 - 只有建立者可以編輯"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        return HttpResponseForbidden("只有團隊建立者可以編輯團隊")
    
    if request.method == 'POST':
        form = DevTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'團隊「{team.name}」已更新！')
            return redirect('programdb:team_detail', pk=team.pk)
    else:
        form = DevTeamForm(instance=team)
    
    return render(request, 'ProgramDbRegistry/team_form.html', {
        'form': form,
        'team': team,
        'title': f'編輯團隊：{team.name}',
        'is_edit': True
    })


@login_required
def team_members(request, pk):
    """管理團隊成員"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        return HttpResponseForbidden("只有團隊建立者可以管理成員")
    
    members = team.members.select_related('user').all()
    
    return render(request, 'ProgramDbRegistry/team_members.html', {
        'team': team,
        'members': members
    })


@login_required
@require_GET
def search_users(request):
    """搜尋使用者 API"""
    query = request.GET.get('q', '')
    team_id = request.GET.get('team_id')
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )
    
    # 排除已經是成員的使用者
    if team_id:
        existing_members = DevTeamMember.objects.filter(team_id=team_id).values_list('user_id', flat=True)
        users = users.exclude(id__in=existing_members)
    
    # Apply limit after all filtering is done
    users = users[:10]
    
    user_list = [{
        'id': u.id,
        'username': u.username,
        'full_name': u.get_full_name() or u.username
    } for u in users]
    
    return JsonResponse({'users': user_list})


@login_required
@require_POST
def add_member(request, pk):
    """新增團隊成員"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊建立者可以新增成員'}, status=403)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        
        if team.members.filter(user=user).exists():
            return JsonResponse({'success': False, 'error': '該使用者已經是團隊成員'})
        
        DevTeamMember.objects.create(team=team, user=user, role='member')
        return JsonResponse({
            'success': True,
            'member': {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def remove_member(request, pk, user_id):
    """移除團隊成員"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊建立者可以移除成員'}, status=403)
    
    if int(user_id) == team.created_by.id:
        return JsonResponse({'success': False, 'error': '無法移除團隊建立者'}, status=400)
    
    try:
        member = DevTeamMember.objects.get(team=team, user_id=user_id)
        member.delete()
        return JsonResponse({'success': True})
    except DevTeamMember.DoesNotExist:
        return JsonResponse({'success': False, 'error': '找不到該成員'}, status=404)


@login_required
@require_POST
def add_db_server(request, pk):
    """新增資料庫伺服器"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以新增伺服器'}, status=403)
    
    form = DatabaseServerForm(request.POST)
    if form.is_valid():
        server = form.save()
        return JsonResponse({
            'success': True,
            'server': {
                'id': server.id,
                'name': server.name,
                'description': server.description
            }
        })
    else:
        errors = ', '.join([f'{k}: {v[0]}' for k, v in form.errors.items()])
        return JsonResponse({'success': False, 'error': errors}, status=400)


@login_required
@require_POST
def delete_db_server(request, pk, server_id):
    """刪除資料庫伺服器"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以刪除伺服器'}, status=403)
    
    try:
        server = DatabaseServer.objects.get(pk=server_id)
        # 檢查是否有程式使用此伺服器
        if server.databases.exists():
            return JsonResponse({
                'success': False, 
                'error': f'此伺服器正被 {server.databases.count()} 個程式使用，無法刪除'
            }, status=400)
        server.delete()
        return JsonResponse({'success': True})
    except DatabaseServer.DoesNotExist:
        return JsonResponse({'success': False, 'error': '找不到該伺服器'}, status=404)


@login_required
@require_GET
def get_server_programs(request, pk, server_id):
    """取得使用指定伺服器的程式列表"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '無權限'}, status=403)
    
    try:
        server = DatabaseServer.objects.get(pk=server_id)
        databases = server.databases.select_related('program', 'program__team').all()
        
        programs_data = {}
        for db in databases:
            prog = db.program
            if prog.id not in programs_data:
                programs_data[prog.id] = {
                    'id': prog.id,
                    'name': prog.name,
                    'team_name': prog.team.name,
                    'url': f'/program-db/program/{prog.id}/',
                    'databases': []
                }
            programs_data[prog.id]['databases'].append({
                'database_name': db.database_name,
                'table_name': db.table_name,
                'permission': db.get_access_permission_display()
            })
        
        return JsonResponse({
            'success': True,
            'server_name': server.name,
            'programs': list(programs_data.values())
        })
    except DatabaseServer.DoesNotExist:
        return JsonResponse({'success': False, 'error': '找不到該伺服器'}, status=404)


@login_required
def program_detail(request, pk):
    """程式詳情頁面"""
    program = get_object_or_404(Program, pk=pk)
    team = program.team
    
    if not check_team_member(request.user, team):
        return render(request, 'ProgramDbRegistry/team_access_denied.html', {
            'team': team
        })
    
    databases = program.databases.select_related('server').all()
    file_locations = program.file_locations.all()
    design_docs = program.design_docs.prefetch_related('tables__fields').all()
    
    return render(request, 'ProgramDbRegistry/program_detail.html', {
        'program': program,
        'team': team,
        'databases': databases,
        'file_locations': file_locations,
        'design_docs': design_docs,
        'is_creator': check_team_creator(request.user, team)
    })


@login_required
def program_create(request, team_pk):
    """建立新程式"""
    team = get_object_or_404(DevTeam, pk=team_pk)
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以建立程式")
    
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        db_formset = ProgramDatabaseFormSet(request.POST, prefix='databases')
        file_formset = FileLocationFormSet(request.POST, prefix='files')
        api_formset = ProgramApiUsageFormSet(request.POST, prefix='apis')
        
        if form.is_valid():
            program = form.save(commit=False)
            program.team = team
            program.save()
            
            # 處理資料庫 formset
            db_formset = ProgramDatabaseFormSet(request.POST, instance=program, prefix='databases')
            if db_formset.is_valid():
                db_formset.save()
            
            # 處理檔案位置 formset
            file_formset = FileLocationFormSet(request.POST, instance=program, prefix='files')
            if file_formset.is_valid():
                file_formset.save()
            
            # 處理平台 API formset
            api_formset = ProgramApiUsageFormSet(request.POST, instance=program, prefix='apis')
            if api_formset.is_valid():
                api_formset.save()
            
            messages.success(request, f'程式「{program.name}」已成功建立！')
            return redirect('programdb:program_detail', pk=program.pk)
    else:
        form = ProgramForm()
        db_formset = ProgramDatabaseFormSet(prefix='databases')
        file_formset = FileLocationFormSet(prefix='files')
        api_formset = ProgramApiUsageFormSet(prefix='apis')
    
    return render(request, 'ProgramDbRegistry/program_form.html', {
        'form': form,
        'db_formset': db_formset,
        'file_formset': file_formset,
        'api_formset': api_formset,
        'team': team,
        'db_servers': DatabaseServer.objects.all(),
        'platform_apis': PlatformApi.objects.all(),
        'title': '建立新程式',
        'is_edit': False
    })


@login_required
def program_update(request, pk):
    """編輯程式"""
    program = get_object_or_404(Program, pk=pk)
    team = program.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以編輯程式")
    
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        db_formset = ProgramDatabaseFormSet(request.POST, instance=program, prefix='databases')
        file_formset = FileLocationFormSet(request.POST, instance=program, prefix='files')
        api_formset = ProgramApiUsageFormSet(request.POST, instance=program, prefix='apis')
        
        if form.is_valid() and db_formset.is_valid() and file_formset.is_valid() and api_formset.is_valid():
            form.save()
            db_formset.save()
            file_formset.save()
            api_formset.save()
            
            messages.success(request, f'程式「{program.name}」已更新！')
            return redirect('programdb:program_detail', pk=program.pk)
    else:
        form = ProgramForm(instance=program)
        db_formset = ProgramDatabaseFormSet(instance=program, prefix='databases')
        file_formset = FileLocationFormSet(instance=program, prefix='files')
        api_formset = ProgramApiUsageFormSet(instance=program, prefix='apis')
    
    return render(request, 'ProgramDbRegistry/program_form.html', {
        'form': form,
        'db_formset': db_formset,
        'file_formset': file_formset,
        'api_formset': api_formset,
        'team': team,
        'program': program,
        'db_servers': DatabaseServer.objects.all(),
        'platform_apis': PlatformApi.objects.all(),
        'title': f'編輯程式：{program.name}',
        'is_edit': True
    })


@login_required
@require_POST
def program_delete(request, pk):
    """刪除程式"""
    program = get_object_or_404(Program, pk=pk)
    team = program.team
    
    if not check_team_creator(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊建立者可以刪除程式'}, status=403)
    
    program_name = program.name
    team_pk = team.pk
    program.delete()
    
    messages.success(request, f'程式「{program_name}」已刪除！')
    return redirect('programdb:team_detail', pk=team_pk)


# ===== Database Design Documentation Views =====

@login_required
def design_doc_create(request, program_pk):
    """建立資料庫設計文件"""
    program = get_object_or_404(Program, pk=program_pk)
    team = program.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以建立設計文件")
    
    if request.method == 'POST':
        form = DatabaseDesignDocForm(request.POST)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.program = program
            doc.save()
            
            # 如果是 Django Model 模式，自動解析
            if doc.doc_type == 'django' and doc.django_model_code:
                doc.parse_django_model()
            
            messages.success(request, f'設計文件「{doc.name}」已成功建立！')
            return redirect('programdb:design_doc_detail', pk=doc.pk)
    else:
        form = DatabaseDesignDocForm()
    
    return render(request, 'ProgramDbRegistry/design_doc_form.html', {
        'form': form,
        'program': program,
        'team': team,
        'title': '建立資料庫設計文件',
        'is_edit': False
    })


@login_required
def design_doc_detail(request, pk):
    """資料庫設計文件詳情"""
    doc = get_object_or_404(DatabaseDesignDoc, pk=pk)
    program = doc.program
    team = program.team
    
    if not check_team_member(request.user, team):
        return render(request, 'ProgramDbRegistry/team_access_denied.html', {
            'team': team
        })
    
    tables = doc.tables.prefetch_related('fields').all()
    
    return render(request, 'ProgramDbRegistry/design_doc_detail.html', {
        'doc': doc,
        'program': program,
        'team': team,
        'tables': tables,
        'is_creator': check_team_creator(request.user, team)
    })


@login_required
def design_doc_update(request, pk):
    """編輯資料庫設計文件"""
    doc = get_object_or_404(DatabaseDesignDoc, pk=pk)
    program = doc.program
    team = program.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以編輯設計文件")
    
    if request.method == 'POST':
        form = DatabaseDesignDocForm(request.POST, instance=doc)
        if form.is_valid():
            doc = form.save()
            
            # 如果是 Django Model 模式，重新解析
            if doc.doc_type == 'django' and doc.django_model_code:
                doc.parse_django_model()
            elif doc.doc_type == 'manual':
                # 手動模式，從資料表生成 Mermaid
                doc.mermaid_content = doc.generate_mermaid()
                doc.save(update_fields=['mermaid_content'])
            # 當 doc_type == 'mermaid' 時，保留使用者輸入的內容，不覆寫
            
            messages.success(request, f'設計文件「{doc.name}」已更新！')
            return redirect('programdb:design_doc_detail', pk=doc.pk)
    else:
        form = DatabaseDesignDocForm(instance=doc)
    
    return render(request, 'ProgramDbRegistry/design_doc_form.html', {
        'form': form,
        'doc': doc,
        'program': program,
        'team': team,
        'title': f'編輯設計文件：{doc.name}',
        'is_edit': True
    })


@login_required
@require_POST
def design_doc_delete(request, pk):
    """刪除資料庫設計文件"""
    doc = get_object_or_404(DatabaseDesignDoc, pk=pk)
    program = doc.program
    team = program.team
    
    if not check_team_creator(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊建立者可以刪除設計文件'}, status=403)
    
    doc_name = doc.name
    program_pk = program.pk
    doc.delete()
    
    messages.success(request, f'設計文件「{doc_name}」已刪除！')
    return redirect('programdb:program_detail', pk=program_pk)


@login_required
@require_POST
def design_doc_parse(request, pk):
    """重新解析 Django Model"""
    doc = get_object_or_404(DatabaseDesignDoc, pk=pk)
    program = doc.program
    team = program.team
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '沒有權限'}, status=403)
    
    if doc.doc_type != 'django':
        return JsonResponse({'success': False, 'error': '只能解析 Django Model 模式的文件'}, status=400)
    
    try:
        doc.parse_django_model()
        return JsonResponse({'success': True, 'message': '解析成功'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def design_doc_mermaid_download(request, pk):
    """下載 Mermaid .md 文件"""
    doc = get_object_or_404(DatabaseDesignDoc, pk=pk)
    program = doc.program
    team = program.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("沒有權限")
    
    # 生成最新的 Mermaid 內容
    mermaid_content = doc.generate_mermaid()
    
    # 建立 Markdown 內容
    md_content = f"""# {doc.name}

## 程式資訊
- **程式名稱**: {program.name}
- **所屬團隊**: {team.name}
- **文件類型**: {doc.get_doc_type_display()}
- **最後更新**: {doc.updated_at.strftime('%Y-%m-%d %H:%M')}

## ER Diagram

```mermaid
{mermaid_content}
```

## 資料表清單

"""
    
    for table in doc.tables.prefetch_related('fields').all():
        md_content += f"### {table.table_name}\n\n"
        if table.description:
            md_content += f"{table.description}\n\n"
        
        md_content += "| 欄位名稱 | 資料類型 | PK | FK | 可為空 | 說明 |\n"
        md_content += "|---------|---------|----|----|--------|------|\n"
        
        for field in table.fields.all():
            pk = "✓" if field.is_primary_key else ""
            fk = field.fk_reference_table if field.is_foreign_key else ""
            nullable = "✓" if field.is_nullable else ""
            md_content += f"| {field.field_name} | {field.data_type} | {pk} | {fk} | {nullable} | {field.description} |\n"
        
        md_content += "\n"
    
    # 回傳檔案
    response = HttpResponse(md_content, content_type='text/markdown; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{doc.name}_design.md"'
    return response


@login_required
def design_table_edit(request, doc_pk):
    """編輯設計文件的資料表（手動模式）"""
    doc = get_object_or_404(DatabaseDesignDoc, pk=doc_pk)
    program = doc.program
    team = program.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以編輯")
    
    if request.method == 'POST':
        table_formset = DesignTableFormSet(request.POST, instance=doc, prefix='tables')
        if table_formset.is_valid():
            table_formset.save()
            
            # 更新 Mermaid
            doc.mermaid_content = doc.generate_mermaid()
            doc.save(update_fields=['mermaid_content'])
            
            messages.success(request, '資料表已更新！')
            return redirect('programdb:design_doc_detail', pk=doc.pk)
    else:
        table_formset = DesignTableFormSet(instance=doc, prefix='tables')
    
    return render(request, 'ProgramDbRegistry/design_table_edit.html', {
        'doc': doc,
        'program': program,
        'team': team,
        'table_formset': table_formset,
        'title': f'編輯資料表：{doc.name}'
    })


@login_required
def design_field_edit(request, table_pk):
    """編輯資料表的欄位（手動模式）"""
    table = get_object_or_404(DesignTable, pk=table_pk)
    doc = table.design_doc
    program = doc.program
    team = program.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以編輯")
    
    if request.method == 'POST':
        field_formset = DesignFieldFormSet(request.POST, instance=table, prefix='fields')
        if field_formset.is_valid():
            field_formset.save()
            
            # 更新 Mermaid
            doc.mermaid_content = doc.generate_mermaid()
            doc.save(update_fields=['mermaid_content'])
            
            messages.success(request, f'資料表「{table.table_name}」的欄位已更新！')
            return redirect('programdb:design_doc_detail', pk=doc.pk)
    else:
        field_formset = DesignFieldFormSet(instance=table, prefix='fields')
    
    return render(request, 'ProgramDbRegistry/design_field_edit.html', {
        'table': table,
        'doc': doc,
        'program': program,
        'team': team,
        'field_formset': field_formset,
        'title': f'編輯欄位：{table.table_name}'
    })


# ===== Platform API Management Views =====

@login_required
@require_POST
def add_platform_api(request, pk):
    """新增平台 API"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以新增平台 API'}, status=403)
    
    form = PlatformApiForm(request.POST)
    if form.is_valid():
        api = form.save()
        return JsonResponse({
            'success': True,
            'api': {
                'id': api.id,
                'name': api.name,
                'api_endpoint': api.api_endpoint,
                'auth_type': api.get_auth_type_display(),
                'description': api.description
            }
        })
    else:
        errors = ', '.join([f'{k}: {v[0]}' for k, v in form.errors.items()])
        return JsonResponse({'success': False, 'error': errors}, status=400)


@login_required
@require_POST
def delete_platform_api(request, pk, api_id):
    """刪除平台 API"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以刪除平台 API'}, status=403)
    
    try:
        api = PlatformApi.objects.get(pk=api_id)
        # 檢查是否有程式使用此 API
        if api.usages.exists():
            return JsonResponse({
                'success': False, 
                'error': f'此平台 API 正被 {api.usages.count()} 個程式使用，無法刪除'
            }, status=400)
        api.delete()
        return JsonResponse({'success': True})
    except PlatformApi.DoesNotExist:
        return JsonResponse({'success': False, 'error': '找不到該平台 API'}, status=404)


@login_required
@require_GET
def get_api_programs(request, pk, api_id):
    """取得使用指定平台 API 的程式列表"""
    team = get_object_or_404(DevTeam, pk=pk)
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '無權限'}, status=403)
    
    try:
        api = PlatformApi.objects.get(pk=api_id)
        usages = api.usages.select_related('program', 'program__team').all()
        
        programs_data = {}
        for usage in usages:
            prog = usage.program
            if prog.id not in programs_data:
                programs_data[prog.id] = {
                    'id': prog.id,
                    'name': prog.name,
                    'team_name': prog.team.name,
                    'url': f'/program-db/program/{prog.id}/',
                    'api_paths': []
                }
            programs_data[prog.id]['api_paths'].append({
                'path': usage.api_path or '(全部)',
                'access_type': usage.get_access_type_display(),
                'description': usage.description
            })
        
        return JsonResponse({
            'success': True,
            'api_name': api.name,
            'programs': list(programs_data.values())
        })
    except PlatformApi.DoesNotExist:
        return JsonResponse({'success': False, 'error': '找不到該平台 API'}, status=404)


# ===== Virtual Employee Management Views =====

@login_required
def virtual_employee_create(request, team_pk):
    """建立虛擬員工"""
    team = get_object_or_404(DevTeam, pk=team_pk)
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以建立虛擬員工")
    
    if request.method == 'POST':
        form = VirtualEmployeeForm(request.POST)
        if form.is_valid():
            ve = form.save(commit=False)
            ve.team = team
            ve.created_by = request.user
            ve.save()
            
            messages.success(request, f'虛擬員工「{ve.name}」已成功建立！')
            return redirect('programdb:team_detail', pk=team.pk)
    else:
        form = VirtualEmployeeForm()
    
    return render(request, 'ProgramDbRegistry/virtual_employee_form.html', {
        'form': form,
        'team': team,
        'title': '新增虛擬員工',
        'is_edit': False
    })


@login_required
def virtual_employee_update(request, pk):
    """編輯虛擬員工"""
    ve = get_object_or_404(VirtualEmployee, pk=pk)
    team = ve.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以編輯虛擬員工")
    
    if request.method == 'POST':
        form = VirtualEmployeeForm(request.POST, instance=ve)
        if form.is_valid():
            form.save()
            messages.success(request, f'虛擬員工「{ve.name}」已更新！')
            return redirect('programdb:team_detail', pk=team.pk)
    else:
        form = VirtualEmployeeForm(instance=ve)
    
    return render(request, 'ProgramDbRegistry/virtual_employee_form.html', {
        'form': form,
        'team': team,
        've': ve,
        'title': f'編輯虛擬員工：{ve.name}',
        'is_edit': True
    })


@login_required
@require_POST
def virtual_employee_delete(request, pk):
    """刪除虛擬員工"""
    ve = get_object_or_404(VirtualEmployee, pk=pk)
    team = ve.team
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以刪除虛擬員工'}, status=403)
    
    ve_name = ve.name
    team_pk = team.pk
    ve.delete()
    
    messages.success(request, f'虛擬員工「{ve_name}」已刪除！')
    return redirect('programdb:team_detail', pk=team_pk)


@login_required
def virtual_employee_retire(request, pk):
    """將虛擬員工標記為已退休"""
    ve = get_object_or_404(VirtualEmployee, pk=pk)
    team = ve.team
    
    if not check_team_member(request.user, team):
        return HttpResponseForbidden("只有團隊成員可以操作")
    
    if request.method == 'POST':
        form = VirtualEmployeeRetireForm(request.POST)
        if form.is_valid():
            ve.status = 'retired'
            ve.retirement_reason = form.cleaned_data['retirement_reason']
            ve.retired_at = timezone.now()
            ve.save()
            
            messages.success(request, f'虛擬員工「{ve.name}」已標記為退休！')
            return redirect('programdb:team_detail', pk=team.pk)
    else:
        form = VirtualEmployeeRetireForm()
    
    return render(request, 'ProgramDbRegistry/virtual_employee_retire.html', {
        'form': form,
        'team': team,
        've': ve,
        'title': f'退休虛擬員工：{ve.name}'
    })
