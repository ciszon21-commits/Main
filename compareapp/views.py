from __future__ import annotations

import json
from collections import defaultdict
from decimal import Decimal
from datetime import timedelta
from functools import wraps
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import BudgetUploadForm, CompareOptionsForm, ProjectForm, QuantityUploadForm
from .models import CompareProject, ComparisonMatch, ComparisonRun, GlobalKeyword, ProjectAccess
from .services.exceptions import CompareAppError
from .services.keywords import build_keyword_panel_context, upsert_global_keyword
from .services.parsers import parse_budget_xml, parse_quantity_workbook
from .services.serialization import (
    deserialize_standard_records,
    extract_budget_terms,
    serialize_standard_records,
)
from .services.run_tasks import enqueue_comparison_run


def require_authenticated_user(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            return HttpResponseForbidden('Authentication required.')
        return view_func(request, *args, **kwargs)

    return _wrapped


def _is_legacy_budget_payload(project: CompareProject) -> bool:
    if not project.budget_records:
        return False
    first = project.budget_records[0]
    if not isinstance(first, dict):
        return True
    raw_payload = first.get('raw_payload')
    if not isinstance(raw_payload, dict):
        return True
    return not any(str(key).startswith('Description[') for key in raw_payload.keys())


def _accessible_projects_queryset(user):
    queryset = CompareProject.objects.all()
    if user.is_superuser:
        return queryset
    return queryset.filter(Q(owner=user) | Q(access_list__user=user)).distinct()


def _get_project_or_404_for_user(user, project_id: int) -> CompareProject:
    return get_object_or_404(_accessible_projects_queryset(user), id=project_id)


def _can_manage_project_access(user, project: CompareProject) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if project.owner_id == user.id:
        return True
    return project.access_list.filter(
        user=user,
        role=ProjectAccess.Role.MANAGER,
    ).exists()


def _can_edit_project(user, project: CompareProject) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if project.owner_id == user.id:
        return True
    return project.access_list.filter(
        user=user,
        role__in=[ProjectAccess.Role.EDITOR, ProjectAccess.Role.MANAGER],
    ).exists()


def _ensure_project_editable_or_forbidden(user, project: CompareProject) -> HttpResponse | None:
    if _can_edit_project(user, project):
        return None
    return HttpResponseForbidden('Only owner/editor/manager can modify this project.')


def _project_share_members(project: CompareProject):
    return project.access_list.select_related('user').order_by('role', 'user__username', 'id')


def _project_share_context(project: CompareProject, actor) -> dict[str, Any]:
    can_manage = _can_manage_project_access(actor, project)
    members = list(_project_share_members(project)[:100])
    return {
        'is_project_owner': bool(project.owner_id and project.owner_id == actor.id),
        'can_manage_access': can_manage,
        'shared_users_count': len(members),
        'shared_users_preview': members[:6],
    }


def _project_owner_label(project: CompareProject) -> str:
    if project.owner is None:
        return '未指定'
    username = getattr(project.owner, 'username', '') or ''
    email = getattr(project.owner, 'email', '') or ''
    if username:
        return username
    if email:
        return email
    return f'User#{project.owner_id}'


def _role_display_zh(role: str) -> str:
    mapping = {
        ProjectAccess.Role.VIEWER: '檢視者',
        ProjectAccess.Role.EDITOR: '編輯者',
        ProjectAccess.Role.MANAGER: '管理者',
    }
    return mapping.get(role, role)


def _project_access_rows(project: CompareProject) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in _project_share_members(project):
        user = entry.user
        rows.append(
            {
                'id': entry.id,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': entry.role,
                'role_label': _role_display_zh(entry.role),
            }
        )
    return rows


def _role_options_for_template() -> list[dict[str, str]]:
    return [
        {'value': ProjectAccess.Role.VIEWER, 'label': '檢視者'},
        {'value': ProjectAccess.Role.EDITOR, 'label': '編輯者'},
        {'value': ProjectAccess.Role.MANAGER, 'label': '管理者'},
    ]


def _find_user_for_share(identity: str):
    UserModel = get_user_model()
    query = str(identity or '').strip()
    if not query:
        return None

    by_username = UserModel.objects.filter(username__iexact=query).first()
    if by_username is not None:
        return by_username

    return UserModel.objects.filter(email__iexact=query).first()


@require_authenticated_user
def project_index_view(request):
    return _project_index_internal(request, 'compareapp/project_index_apple.html', 'compareapp:project_detail')


@require_authenticated_user
def project_index_apple_view(request):
    return _project_index_internal(request, 'compareapp/project_index_apple.html', 'compareapp:project_detail_apple')


def _project_index_internal(request, template_name, detail_view_name):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect(detail_view_name, project_id=project.id)
    else:
        form = ProjectForm()

    projects = (
        _accessible_projects_queryset(request.user)
        .select_related('owner')
        .order_by('-updated_at')[:30]
    )
    projects_payload = [
        {
            'id': project.id,
            'name': project.name,
            'plan_number': project.plan_number,
            'updated_at': project.updated_at,
            'has_budget': project.has_budget,
            'has_quantity_sheet': project.has_quantity_sheet,
            'owner_label': _project_owner_label(project),
            'is_owner': bool(project.owner_id and project.owner_id == request.user.id),
        }
        for project in projects
    ]
    return render(
        request,
        template_name,
        {
            'form': form,
            'projects': projects_payload,
        },
    )


@require_authenticated_user
def project_detail_view(request, project_id: int):
    return _project_detail_internal(request, project_id, 'compareapp/project_detail_apple.html')


@require_authenticated_user
def project_detail_apple_view(request, project_id: int):
    return _project_detail_internal(request, project_id, 'compareapp/project_detail_apple.html')


def _project_detail_internal(request, project_id, template_name):
    project = _get_project_or_404_for_user(request.user, project_id)
    return render(
        request,
        template_name,
        {
            'project': project,
            'budget_preview': project.budget_records[:20],
            'quantity_preview': project.quantity_records[:20],
            'budget_terms_preview': project.budget_terms[:80],
            **_project_share_context(project, request.user),
        },
    )


@require_authenticated_user
def budget_upload_view(request, project_id: int):
    return _budget_upload_internal(request, project_id, 'compareapp/budget_upload_apple.html', 'compareapp:budget_terms')


@require_authenticated_user
def budget_upload_apple_view(request, project_id: int):
    return _budget_upload_internal(request, project_id, 'compareapp/budget_upload_apple.html', 'compareapp:budget_terms_apple')


def _budget_upload_internal(request, project_id, template_name, next_view_name):
    project = _get_project_or_404_for_user(request.user, project_id)

    if request.method == 'POST':
        forbidden = _ensure_project_editable_or_forbidden(request.user, project)
        if forbidden is not None:
            return forbidden
        form = BudgetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data['budget_xml']
            payload = upload.read()
            try:
                records = parse_budget_xml(upload.name, payload)
            except CompareAppError as exc:
                form.add_error(None, str(exc))
            else:
                project.budget_xml.save(upload.name, ContentFile(payload), save=False)
                project.budget_original_name = upload.name
                project.budget_records = serialize_standard_records(records)
                project.budget_terms = extract_budget_terms(records)

                # Re-uploading budget invalidates downstream artifacts.
                if project.quantity_sheet:
                    project.quantity_sheet.delete(save=False)
                project.quantity_sheet = None
                project.quantity_original_name = ''
                project.quantity_records = []

                project.save()
                return redirect(next_view_name, project_id=project.id)
    else:
        form = BudgetUploadForm()

    return render(
        request,
        template_name,
        {
            'project': project,
            'form': form,
            **_keyword_context(project, stage='budget'),
            **_project_share_context(project, request.user),
        },
    )


@require_authenticated_user
def budget_terms_view(request, project_id: int):
    return _budget_terms_internal(request, project_id, 'compareapp/budget_terms_apple.html', 'compareapp:budget_upload')


@require_authenticated_user
def budget_terms_apple_view(request, project_id: int):
    return _budget_terms_internal(request, project_id, 'compareapp/budget_terms_apple.html', 'compareapp:budget_upload_apple')


def _budget_terms_internal(request, project_id, template_name, upload_view_name):
    project = _get_project_or_404_for_user(request.user, project_id)
    if not project.has_budget:
        return redirect(upload_view_name, project_id=project.id)

    if _is_legacy_budget_payload(project):
        try:
            with project.budget_xml.open('rb') as file_obj:
                refreshed_records = parse_budget_xml(
                    project.budget_original_name or project.budget_xml.name,
                    file_obj.read(),
                )
        except CompareAppError:
            refreshed_records = None
        if refreshed_records is not None:
            project.budget_records = serialize_standard_records(refreshed_records)
            project.budget_terms = extract_budget_terms(refreshed_records)
            project.save(update_fields=['budget_records', 'budget_terms', 'updated_at'])

    all_records = deserialize_standard_records(project.budget_records)
    all_terms = extract_budget_terms(all_records)
    if all_terms != project.budget_terms:
        project.budget_terms = all_terms
        project.save(update_fields=['budget_terms', 'updated_at'])

    all_records_payload = serialize_standard_records(all_records)
    term_preview_limit = 300
    record_preview_limit = 120

    return render(
        request,
        template_name,
        {
            'project': project,
            'terms': all_terms[:term_preview_limit],
            'terms_total_count': len(all_terms),
            'terms_truncated': len(all_terms) > term_preview_limit,
            'budget_records_count': len(all_records),
            'records_preview': all_records_payload[:record_preview_limit],
            'records_truncated': len(all_records_payload) > record_preview_limit,
            **_keyword_context(project, stage='budget'),
            **_project_share_context(project, request.user),
        },
    )


@require_authenticated_user
def quantity_upload_view(request, project_id: int):
    return _quantity_upload_internal(request, project_id, 'compareapp/quantity_upload_apple.html', 'compareapp:budget_upload', 'compareapp:compare')


@require_authenticated_user
def quantity_upload_apple_view(request, project_id: int):
    return _quantity_upload_internal(request, project_id, 'compareapp/quantity_upload_apple.html', 'compareapp:budget_upload_apple', 'compareapp:compare_apple')


def _quantity_upload_internal(request, project_id, template_name, budget_upload_view, compare_view):
    project = _get_project_or_404_for_user(request.user, project_id)
    if not project.has_budget:
        return redirect(budget_upload_view, project_id=project.id)

    if request.method == 'POST':
        forbidden = _ensure_project_editable_or_forbidden(request.user, project)
        if forbidden is not None:
            return forbidden
        form = QuantityUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data['quantity_sheet']
            payload = upload.read()
            try:
                records = parse_quantity_workbook(upload.name, payload)
            except CompareAppError as exc:
                form.add_error(None, str(exc))
            else:
                project.quantity_sheet.save(upload.name, ContentFile(payload), save=False)
                project.quantity_original_name = upload.name
                project.quantity_records = serialize_standard_records(records)
                project.save()
                return redirect(compare_view, project_id=project.id)
    else:
        form = QuantityUploadForm()

    return render(
        request,
        template_name,
        {
            'project': project,
            'form': form,
            **_keyword_context(project, stage='quantity'),
            **_project_share_context(project, request.user),
        },
    )


@require_authenticated_user
def compare_view(request, project_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    context = _build_compare_context(request, project)
    if isinstance(context, HttpResponse):
        return context

    return render(request, 'compareapp/compare_result_apple.html', context)


@require_authenticated_user
def compare_view_structured(request, project_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    context = _build_compare_context(request, project)
    if isinstance(context, HttpResponse):
        return context
    return render(request, 'compareapp/compare_result_structured.html', context)


@require_authenticated_user
def compare_view_fluid(request, project_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    context = _build_compare_context(request, project)
    if isinstance(context, HttpResponse):
        return context
    return render(request, 'compareapp/compare_result_fluid.html', context)


@require_authenticated_user
def compare_view_apple(request, project_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    context = _build_compare_context(request, project)
    if isinstance(context, HttpResponse):
        return context
    return render(request, 'compareapp/compare_result_apple.html', context)


@require_authenticated_user
@require_http_methods(['GET', 'POST'])
def global_keyword_manage_view(request):
    feedback = ''
    feedback_error = False
    query = str(request.GET.get('q') or request.POST.get('q') or '').strip()
    status = str(request.GET.get('status') or request.POST.get('status') or 'all').strip().lower()
    if status not in {'all', 'active', 'inactive'}:
        status = 'all'

    if request.method == 'POST':
        action = str(request.POST.get('action') or '').strip().lower()
        keyword_id_raw = request.POST.get('keyword_id')
        term_raw = str(request.POST.get('term') or '').strip()

        if action == 'add':
            keyword, created = upsert_global_keyword(
                term_raw,
                source=GlobalKeyword.Source.MANUAL,
            )
            if keyword is None:
                feedback = '關鍵字格式不正確，請至少輸入 2 個有效字元。'
                feedback_error = True
            else:
                feedback = '已新增關鍵字。' if created else '關鍵字已存在，已更新使用次數。'

        elif action in {'toggle', 'delete'}:
            try:
                keyword_id = int(str(keyword_id_raw or '').strip())
            except (TypeError, ValueError):
                keyword_id = 0

            keyword = GlobalKeyword.objects.filter(id=keyword_id).first()
            if keyword is None:
                feedback = '找不到指定關鍵字。'
                feedback_error = True
            elif action == 'delete':
                keyword.delete()
                feedback = '已刪除關鍵字。'
            else:
                keyword.is_active = not keyword.is_active
                keyword.save(update_fields=['is_active', 'updated_at'])
                feedback = '已啟用關鍵字。' if keyword.is_active else '已停用關鍵字。'
        else:
            feedback = '未知操作。'
            feedback_error = True

    queryset = GlobalKeyword.objects.all().order_by('-selected_count', 'term', 'id')
    if query:
        queryset = queryset.filter(Q(term__icontains=query) | Q(normalized_term__icontains=query))
    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'inactive':
        queryset = queryset.filter(is_active=False)

    keywords = list(queryset[:300])
    active_count = GlobalKeyword.objects.filter(is_active=True).count()
    total_count = GlobalKeyword.objects.count()
    inactive_count = max(0, total_count - active_count)

    return render(
        request,
        'compareapp/global_keyword_manage_apple.html',
        {
            'feedback': feedback,
            'feedback_error': feedback_error,
            'query': query,
            'status': status,
            'keywords': keywords,
            'total_count': total_count,
            'active_count': active_count,
            'inactive_count': inactive_count,
        },
    )


@require_authenticated_user
@require_http_methods(['GET', 'POST'])
def project_access_manage_view(request, project_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    if not _can_manage_project_access(request.user, project):
        return HttpResponseForbidden('Only owner/manager can manage project access.')

    feedback = ''
    feedback_error = False
    selected_role = ProjectAccess.Role.VIEWER
    query_text = ''

    if request.method == 'POST':
        action = str(request.POST.get('action') or '').strip().lower()
        query_text = str(request.POST.get('user_identity') or '').strip()
        selected_role_raw = str(request.POST.get('role') or ProjectAccess.Role.VIEWER).strip().lower()
        selected_role = (
            selected_role_raw
            if selected_role_raw in ProjectAccess.Role.values
            else ProjectAccess.Role.VIEWER
        )

        if action == 'add':
            target_user = _find_user_for_share(query_text)
            if target_user is None:
                feedback = '找不到使用者（可輸入使用者名稱或 Email）。'
                feedback_error = True
            elif target_user.id == project.owner_id:
                feedback = '建立者已擁有完整權限，不需重複加入。'
                feedback_error = True
            else:
                _, created = ProjectAccess.objects.update_or_create(
                    project=project,
                    user=target_user,
                    defaults={'role': selected_role},
                )
                role_label = _role_display_zh(selected_role)
                feedback = '已新增成員。' if created else f'已更新權限為「{role_label}」。'

        elif action in {'update_role', 'remove'}:
            access_id_raw = request.POST.get('access_id')
            try:
                access_id = int(str(access_id_raw or '').strip())
            except (TypeError, ValueError):
                access_id = 0

            access = project.access_list.select_related('user').filter(id=access_id).first()
            if access is None:
                feedback = '找不到權限設定資料。'
                feedback_error = True
            elif action == 'remove':
                access.delete()
                feedback = '已移除專案權限。'
            else:
                access.role = selected_role
                access.save(update_fields=['role', 'updated_at'])
                feedback = f'已更新權限為「{_role_display_zh(selected_role)}」。'
        else:
            feedback = '未知操作。'
            feedback_error = True

    return render(
        request,
        'compareapp/project_access_manage_apple.html',
        {
            'project': project,
            'feedback': feedback,
            'feedback_error': feedback_error,
            'query_text': query_text,
            'selected_role': selected_role,
            'role_options': _role_options_for_template(),
            'access_rows': _project_access_rows(project),
            **_project_share_context(project, request.user),
        },
    )


def _build_compare_context(request, project):
    if not project.has_budget:
        return redirect('compareapp:budget_upload', project_id=project.id)
    if not project.has_quantity_sheet:
        return redirect('compareapp:quantity_upload', project_id=project.id)
    if not project.budget_records:
        return redirect('compareapp:budget_upload', project_id=project.id)
    if not project.quantity_records:
        return redirect('compareapp:quantity_upload', project_id=project.id)

    # Note: We need to use the standard compare URL for redirects within the logic
    # or adapt based on the current view. For simplicity, we keep using the standard one
    # or we could make it dynamic.
    # ideally, form submission should post to the current URL.
    
    # We can detect the current view name to redirect back to the same view if needed,
    # but the form implementation below redirects to strict URLs.
    # Let's keep it simple: The form in the template should action="" (current URL).
    # But the redirect below uses specific URL.
    
    # Let's just use the 'compareapp:compare' for the base logic redirects for now,
    # or improved: redirect to the *current* path with query params.
    
    active_run = _resolve_active_run(project, request.GET.get('run'))

    if request.method == 'POST':
        forbidden = _ensure_project_editable_or_forbidden(request.user, project)
        if forbidden is not None:
            return forbidden
        form = CompareOptionsForm(request.POST)
        if form.is_valid():
            run = ComparisonRun.objects.create(
                project=project,
                status=ComparisonRun.Status.PENDING,
                quantity_tolerance=Decimal(str(form.cleaned_data['quantity_tolerance'])),
                fuzzy_threshold=float(form.cleaned_data['fuzzy_threshold']),
                weighted_threshold=float(form.cleaned_data['weighted_threshold']),
            )
            enqueue_comparison_run(run.id)
            # Redirect to the current page with the new run ID
            return redirect(f'{request.path}?run={run.id}')
    else:
        form = CompareOptionsForm(initial=_compare_form_initial(active_run))

    run_history_queryset = (
        project.comparison_runs.annotate(match_count=Count('matches'))
        .order_by('-created_at')[:30]
    )
    
    # We need to preserve the current path for detail_url in history if we want them to stay in the same UI
    # The original implementation hardcoded 'compareapp:compare'.
    # We will make detail_url point to the current path.
    current_path = request.path
    
    run_history = [
        {
            'id': run.id,
            'status': run.status,
            'status_label': run.get_status_display(),
            'created_at': run.created_at,
            'finished_at': run.finished_at,
            'match_count': getattr(run, 'match_count', 0),
            'is_active': bool(active_run and active_run.id == run.id),
            'detail_url': f'{current_path}?run={run.id}',
        }
        for run in run_history_queryset
    ]

    report_payload = None
    baseline_meta: dict[str, Any] | None = None
    run_status_url = None

    if active_run:
        baseline_meta = active_run.baseline_meta if isinstance(active_run.baseline_meta, dict) else {}
        if active_run.status == ComparisonRun.Status.COMPLETED:
            report_payload = _build_report_payload_for_display(project.id, active_run)
        elif active_run.status in {ComparisonRun.Status.PENDING, ComparisonRun.Status.RUNNING}:
            run_status_url = reverse(
                'compareapp:compare_run_status',
                kwargs={'project_id': project.id, 'run_id': active_run.id},
            )

    return {
        'project': project,
        'form': form,
        'active_run': active_run,
        'run_history': run_history,
        'run_status_url': run_status_url,
        'report_payload': report_payload,
        'baseline_meta': baseline_meta,
        **_keyword_context(project, stage='all'),
        **_project_share_context(project, request.user),
    }


@require_authenticated_user
@require_GET
def compare_run_status_view(request, project_id: int, run_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    run = get_object_or_404(ComparisonRun, id=run_id, project=project)
    baseline_meta = run.baseline_meta if isinstance(run.baseline_meta, dict) else {}

    if run.status in {ComparisonRun.Status.PENDING, ComparisonRun.Status.RUNNING} and run.started_at:
        if timezone.now() - run.started_at > timedelta(minutes=25):
            run.status = ComparisonRun.Status.FAILED
            run.finished_at = timezone.now()
            run.error_message = 'Task timeout exceeded 25 minutes. Please re-run with updated settings.'
            run.save(update_fields=['status', 'finished_at', 'error_message', 'updated_at'])

    detail_url = reverse('compareapp:compare', kwargs={'project_id': project.id}) + f'?run={run.id}'

    stage = baseline_meta.get('stage') if isinstance(baseline_meta.get('stage'), str) else ''
    stage_text_map = {
        'preparing': '資料準備中',
        'matching': '方法比對計算中',
        'persisting': '寫入資料庫中',
        'completed': '已完成',
    }
    stage_text = stage_text_map.get(stage, '')

    return JsonResponse(
        {
            'run_id': run.id,
            'status': run.status,
            'status_label': run.get_status_display(),
            'error_message': run.error_message,
            'match_count': run.matches.count(),
            'stage': stage,
            'stage_text': stage_text,
            'pair_count': baseline_meta.get('pair_count'),
            'finished_at': run.finished_at.isoformat() if run.finished_at else None,
            'detail_url': detail_url,
        }
    )


@require_authenticated_user
@require_POST
def compare_match_annotation_view(request, project_id: int, run_id: int, match_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    forbidden = _ensure_project_editable_or_forbidden(request.user, project)
    if forbidden is not None:
        return forbidden
    run = get_object_or_404(ComparisonRun, id=run_id, project=project)
    match = get_object_or_404(ComparisonMatch, id=match_id, run=run)

    if run.status != ComparisonRun.Status.COMPLETED:
        return JsonResponse({'detail': 'Run is not completed yet.'}, status=409)

    payload = _read_request_payload(request)
    verdict_raw = payload.get('verdict')
    note_raw = payload.get('note')

    update_fields: list[str] = []

    if verdict_raw is not None:
        verdict = str(verdict_raw).strip() or ComparisonMatch.Verdict.UNREVIEWED
        if verdict not in ComparisonMatch.Verdict.values:
            return JsonResponse({'detail': 'Invalid verdict.'}, status=400)
        match.verdict = verdict
        update_fields.append('verdict')

    if note_raw is not None:
        note = str(note_raw).strip()
        if len(note) > 2000:
            note = note[:2000]
        match.note = note
        update_fields.append('note')

    if not update_fields:
        return JsonResponse({'detail': 'No fields to update.'}, status=400)

    update_fields.append('updated_at')
    match.save(update_fields=update_fields)

    return JsonResponse(
        {
            'ok': True,
            'match_id': match.id,
            'verdict': match.verdict,
            'note': match.note,
            'updated_at': match.updated_at.isoformat(),
        }
    )


@require_authenticated_user
@require_POST
def keyword_add_view(request, project_id: int):
    project = _get_project_or_404_for_user(request.user, project_id)
    forbidden = _ensure_project_editable_or_forbidden(request.user, project)
    if forbidden is not None:
        return forbidden
    payload = _read_request_payload(request)
    term_raw = payload.get('term')
    if term_raw is None:
        return JsonResponse({'detail': 'Missing term.'}, status=400)

    source_raw = str(payload.get('source') or GlobalKeyword.Source.MANUAL).strip().lower()
    source = source_raw if source_raw in GlobalKeyword.Source.values else GlobalKeyword.Source.MANUAL

    keyword, created = upsert_global_keyword(str(term_raw), source=source)
    if keyword is None:
        return JsonResponse({'detail': 'Invalid keyword term.'}, status=400)

    return JsonResponse(
        {
            'ok': True,
            'created': created,
            'keyword': {
                'id': keyword.id,
                'term': keyword.term,
                'normalized_term': keyword.normalized_term,
                'selected_count': keyword.selected_count,
                'source': keyword.source,
            },
        }
    )


def _resolve_active_run(project: CompareProject, run_id_raw: str | None) -> ComparisonRun | None:
    if run_id_raw:
        try:
            run_id = int(run_id_raw)
        except (TypeError, ValueError):
            run_id = None
        if run_id is not None:
            selected = project.comparison_runs.filter(id=run_id).first()
            if selected is not None:
                return selected
    return project.comparison_runs.order_by('-created_at').first()


def _compare_form_initial(run: ComparisonRun | None) -> dict[str, Any]:
    if run is None:
        return {}
    return {
        'quantity_tolerance': float(run.quantity_tolerance),
        'fuzzy_threshold': run.fuzzy_threshold,
        'weighted_threshold': run.weighted_threshold,
    }


def _build_report_payload_for_display(project_id: int, run: ComparisonRun) -> dict[str, Any]:
    report_payload = run.report_payload if isinstance(run.report_payload, dict) else {}
    payload = json.loads(json.dumps(report_payload, ensure_ascii=False))

    methods = payload.get('methods')
    if not isinstance(methods, list):
        payload['methods'] = []
        return payload

    grouped_matches: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    queryset = run.matches.all().order_by('method', 'rank', 'id')
    for row in queryset:
        grouped_matches[row.method].append(
            {
                'id': row.id,
                'left_source_id': row.left_source_id,
                'right_source_id': row.right_source_id,
                'left_name': row.left_name,
                'right_name': row.right_name,
                'score': row.score,
                'name_score': row.name_score,
                'unit_score': row.unit_score,
                'quantity_score': row.quantity_score,
                'verdict': row.verdict,
                'note': row.note,
                'annotation_url': reverse(
                    'compareapp:compare_match_annotation',
                    kwargs={
                        'project_id': project_id,
                        'run_id': run.id,
                        'match_id': row.id,
                    },
                ),
            }
        )

    for method in methods:
        if not isinstance(method, dict):
            continue
        method_name = str(method.get('method', ''))
        method['matches'] = grouped_matches.get(method_name, [])

    return payload


def _read_request_payload(request: HttpRequest) -> dict[str, Any]:
    content_type = (request.content_type or '').lower()
    if 'application/json' not in content_type:
        return request.POST.dict()

    if not request.body:
        return {}

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def _keyword_context(project: CompareProject, stage: str) -> dict[str, Any]:
    context = build_keyword_panel_context(
        project=project,
        stage=stage,
        suggestion_limit=24,
        library_limit=60,
    )
    context['keyword_stage'] = stage
    context['keyword_add_url'] = reverse(
        'compareapp:keyword_add',
        kwargs={'project_id': project.id},
    )
    return context
