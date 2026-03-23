import json
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.contrib import messages
from django.core.files import File
from .models import Project, ComparisonFile, ComparisonEntry, ReviewFeedback
from .forms import ReviewFeedbackForm, ComparisonFileUploadForm, ProjectPdfUploadForm, ProjectCreateForm
from .services import parse_comparison_json


def user_search(request):
    """使用者搜尋 API（供新增專案管理員搜尋框使用）"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"users": []})
    users = User.objects.filter(is_active=True).filter(
        Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
    )[:12]
    return JsonResponse({
        "users": [
            {"id": u.pk, "username": u.username, "full_name": u.get_full_name()}
            for u in users
        ]
    })


def project_create(request):
    """新增專案"""
    if not request.user.is_authenticated:
        from django.conf import settings as django_settings
        login_url = getattr(django_settings, "LOGIN_URL", "/accounts/login/")
        return redirect(f"{login_url}?next={request.path}")

    initial_admins = []
    initial_experts = []

    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save()
            # 建立者自動成為管理員
            if not project.admins.filter(pk=request.user.pk).exists():
                project.admins.add(request.user)
            messages.success(request, f"專案「{project.name}」已成功建立。")
            return redirect("review_feedback:project_detail", project_id=project.pk)
        # 表單驗證失敗時，保留已選的管理員/專家供前端重新渲染
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_ids = request.POST.getlist("admins")
        expert_ids = request.POST.getlist("experts")
        initial_admins = [
            {"id": u.pk, "username": u.username, "full_name": u.get_full_name()}
            for u in User.objects.filter(pk__in=admin_ids, is_active=True)
        ]
        initial_experts = [
            {"id": u.pk, "username": u.username, "full_name": u.get_full_name()}
            for u in User.objects.filter(pk__in=expert_ids, is_active=True)
        ]
    else:
        form = ProjectCreateForm()

    return render(request, "review_feedback/project_create.html", {
        "form": form,
        "initial_admins_json": json.dumps(initial_admins, ensure_ascii=False),
        "initial_experts_json": json.dumps(initial_experts, ensure_ascii=False),
    })


def project_edit(request, project_id):
    """編輯專案名稱、說明與管理員"""
    project = get_object_or_404(Project, pk=project_id)
    is_admin = request.user.is_authenticated and (
        request.user.is_staff
        or project.admins.filter(pk=request.user.pk).exists()
    )
    if not is_admin:
        messages.error(request, "您沒有編輯此專案的權限。")
        return redirect("review_feedback:project_detail", project_id=project_id)

    def _admin_list(qs):
        return [
            {"id": u.pk, "username": u.username, "full_name": u.get_full_name()}
            for u in qs
        ]

    if request.method == "POST":
        form = ProjectCreateForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"專案「{project.name}」已成功更新。")
            return redirect("review_feedback:project_detail", project_id=project_id)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        current_admins = _admin_list(
            User.objects.filter(pk__in=request.POST.getlist("admins"), is_active=True)
        )
        current_experts = _admin_list(
            User.objects.filter(pk__in=request.POST.getlist("experts"), is_active=True)
        )
    else:
        form = ProjectCreateForm(instance=project)
        current_admins = _admin_list(project.admins.all())
        current_experts = _admin_list(project.experts.all())

    return render(request, "review_feedback/project_edit.html", {
        "form": form,
        "project": project,
        "initial_admins_json": json.dumps(current_admins, ensure_ascii=False),
        "initial_experts_json": json.dumps(current_experts, ensure_ascii=False),
    })


def project_list(request):
    """專案列表 — superuser 看全部，其他人只看有加入（admin/expert）的專案"""
    projects = Project.objects.annotate(
        file_count=Count("comparison_files", distinct=True),
        entry_count=Count("comparison_files__entries", distinct=True),
        confirmed_count=Count(
            "comparison_files__entries",
            filter=Q(comparison_files__entries__arbitration_status__in=["confirmed", "no_conflict"]),
            distinct=True,
        ),
        reviewed_count=Count(
            "comparison_files__entries",
            filter=Q(comparison_files__entries__review_feedbacks__isnull=False),
            distinct=True,
        ),
    )
    if request.user.is_authenticated and not request.user.is_superuser:
        projects = projects.filter(
            Q(admins=request.user) | Q(experts=request.user)
        ).distinct()
    return render(request, "review_feedback/project_list.html", {
        "projects": projects,
    })


def project_detail(request, project_id):
    """專案詳情 — 顯示所有比對檔及統計，含上傳功能"""
    project = get_object_or_404(Project, pk=project_id)
    is_admin = request.user.is_authenticated and (
        request.user.is_superuser
        or request.user.is_staff
        or project.admins.filter(pk=request.user.pk).exists()
    )
    is_expert = request.user.is_authenticated and project.experts.filter(pk=request.user.pk).exists()

    # 存取控制：非 superuser/staff 需要是 admin 或 expert
    if not request.user.is_authenticated:
        from django.conf import settings as django_settings
        login_url = getattr(django_settings, "LOGIN_URL", "/accounts/login/")
        return redirect(f"{login_url}?next={request.path}")
    if not (request.user.is_superuser or request.user.is_staff or is_admin or is_expert):
        messages.error(request, "您沒有存取此專案的權限。")
        return redirect("review_feedback:project_list")

    # Handle JSON upload
    if request.method == "POST" and "upload_json" in request.POST:
        if not is_admin:
            messages.error(request, "您沒有上傳檔案的權限。")
            return redirect("review_feedback:project_detail", project_id=project_id)
        json_form = ComparisonFileUploadForm(request.POST, request.FILES)
        pdf_form = ProjectPdfUploadForm(instance=project)
        if json_form.is_valid():
            uploaded_files = json_form.cleaned_data["json_file"]
            for uploaded in uploaded_files:
                original_name = uploaded.name
                if not original_name.endswith(".json"):
                    messages.error(request, f"「{original_name}」不是 .json 格式，已略過。")
                    continue
                cf = ComparisonFile(project=project, original_filename=original_name)
                cf.file.save(original_name, uploaded)
                cf.save()
                try:
                    count = parse_comparison_json(cf)
                    messages.success(request, f"成功上傳並解析「{original_name}」，共 {count} 筆比對結果。")
                except Exception as e:
                    cf.delete()
                    messages.error(request, f"「{original_name}」JSON 解析失敗：{e}")
        else:
            messages.error(request, "請選擇有效的 .json 檔案。")
        return redirect("review_feedback:project_detail", project_id=project_id)

    # Handle PDF upload
    elif request.method == "POST" and "upload_pdf" in request.POST:
        if not is_admin:
            messages.error(request, "您沒有上傳檔案的權限。")
            return redirect("review_feedback:project_detail", project_id=project_id)
        pdf_form = ProjectPdfUploadForm(request.POST, request.FILES, instance=project)
        json_form = ComparisonFileUploadForm()
        if pdf_form.is_valid():
            pdf_form.save()
            messages.success(request, "PDF 報告書已成功上傳。")
        else:
            messages.error(request, "請選擇有效的 .pdf 檔案。")
        return redirect("review_feedback:project_detail", project_id=project_id)

    else:
        json_form = ComparisonFileUploadForm()
        pdf_form = ProjectPdfUploadForm(instance=project)

    comparison_files = project.comparison_files.annotate(
        total_entries=Count("entries", distinct=True),
        reviewed_entries=Count(
            "entries",
            filter=Q(entries__review_feedbacks__isnull=False),
            distinct=True,
        ),
        match_count=Count(
            "entries",
            filter=Q(entries__is_match=True),
            distinct=True,
        ),
    )

    # 統計所有 final_decision_class
    all_entries = ComparisonEntry.objects.filter(
        comparison_file__project=project,
        is_match=True,
    )
    class_stats = (
        all_entries
        .values("final_decision_class")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # 第二階段待審查：arbitration_status 為 "confirmed" 或 "no_conflict" 才需要人工審查
    confirmed_count = ComparisonEntry.objects.filter(
        comparison_file__project=project,
        arbitration_status__in=["confirmed", "no_conflict"],
    ).count()

    total_match = all_entries.count()
    return render(request, "review_feedback/project_detail.html", {
        "project": project,
        "comparison_files": comparison_files,
        "class_stats": class_stats,
        "total_entries": total_match,
        "total_match_count": total_match,
        "confirmed_count": confirmed_count,
        "is_admin": is_admin,
        "is_expert": is_expert,
        "json_form": json_form,
        "pdf_form": pdf_form,
        "has_pdf": bool(project.pdf_file),
        "pdf_url": project.pdf_file.url if project.pdf_file else None,
        "project_admins": project.admins.all(),
        "project_experts": project.experts.all(),
    })

def project_confirmed_review(request, project_id):
    """第二階段人工審查 — 顯示所有 arbitration_status='confirmed' 或 'no_conflict' 的比對結果"""
    project = get_object_or_404(Project, pk=project_id)

    if not request.user.is_authenticated:
        from django.conf import settings as django_settings
        login_url = getattr(django_settings, "LOGIN_URL", "/accounts/login/")
        return redirect(f"{login_url}?next={request.path}")
    can_access = (
        request.user.is_superuser or request.user.is_staff
        or project.admins.filter(pk=request.user.pk).exists()
        or project.experts.filter(pk=request.user.pk).exists()
    )
    if not can_access:
        messages.error(request, "您沒有存取此專案的權限。")
        return redirect("review_feedback:project_list")

    entries = (
        ComparisonEntry.objects
        .filter(comparison_file__project=project, arbitration_status__in=["confirmed", "no_conflict"])
        .select_related("comparison_file")
        .prefetch_related("review_feedbacks__reviewer")
        .order_by("final_decision_class", "source_page", "char_start_pos")
    )

    entry_forms = []
    for entry in entries:
        latest_fb = entry.latest_feedback
        if latest_fb:
            initial = {
                "is_correct": "true" if latest_fb.is_correct is True else ("false" if latest_fb.is_correct is False else ""),
                "correct_classification": latest_fb.correct_classification,
                "feedback_reason": latest_fb.feedback_reason,
                "additional_description": latest_fb.additional_description,
            }
        else:
            initial = {}
        form = ReviewFeedbackForm(initial=initial, prefix=f"entry_{entry.pk}")
        entry_forms.append((entry, form, latest_fb))

    return render(request, "review_feedback/confirmed_review.html", {
        "project": project,
        "entry_forms": entry_forms,
        "has_pdf": bool(project.pdf_file),
        "pdf_url": project.pdf_file.url if project.pdf_file else None,
        "confirmed_count": entries.count(),
    })


def comparison_detail(request, project_id, file_id):
    """比對結果列表 — 顯示所有 entries + inline 審查回饋"""
    project = get_object_or_404(Project, pk=project_id)
    comparison_file = get_object_or_404(ComparisonFile, pk=file_id, project=project)

    if not request.user.is_authenticated:
        from django.conf import settings as django_settings
        login_url = getattr(django_settings, "LOGIN_URL", "/accounts/login/")
        return redirect(f"{login_url}?next={request.path}")
    can_access = (
        request.user.is_superuser or request.user.is_staff
        or project.admins.filter(pk=request.user.pk).exists()
        or project.experts.filter(pk=request.user.pk).exists()
    )
    if not can_access:
        messages.error(request, "您沒有存取此專案的權限。")
        return redirect("review_feedback:project_list")

    entries = comparison_file.entries.all().prefetch_related("review_feedbacks__reviewer")

    # 為每個 entry 準備表單
    entry_forms = []
    for entry in entries:
        latest_fb = entry.latest_feedback
        if latest_fb:
            initial = {
                "is_correct": "true" if latest_fb.is_correct is True else ("false" if latest_fb.is_correct is False else ""),
                "correct_classification": latest_fb.correct_classification,
                "feedback_reason": latest_fb.feedback_reason,
                "additional_description": latest_fb.additional_description,
            }
        else:
            initial = {}
        form = ReviewFeedbackForm(initial=initial, prefix=f"entry_{entry.pk}")
        entry_forms.append((entry, form, latest_fb))

    return render(request, "review_feedback/comparison_detail.html", {
        "project": project,
        "comparison_file": comparison_file,
        "entry_forms": entry_forms,
        "has_pdf": bool(project.pdf_file),
        "pdf_url": project.pdf_file.url if project.pdf_file else None,
    })


@require_POST
def submit_feedback(request, entry_id):
    """提交審查回饋 (AJAX)"""
    entry = get_object_or_404(ComparisonEntry, pk=entry_id)
    form = ReviewFeedbackForm(request.POST, prefix=f"entry_{entry_id}")

    if form.is_valid():
        feedback, created = ReviewFeedback.objects.update_or_create(
            entry=entry,
            reviewer=request.user if request.user.is_authenticated else None,
            defaults={
                "is_correct": form.cleaned_data["is_correct"],
                "correct_classification": form.cleaned_data.get("correct_classification", ""),
                "feedback_reason": form.cleaned_data.get("feedback_reason", ""),
                "additional_description": form.cleaned_data.get("additional_description", ""),
            },
        )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "is_correct": feedback.is_correct,
                "correct_classification": feedback.correct_classification,
                "feedback_reason": feedback.feedback_reason,
                "additional_description": feedback.additional_description,
                "reviewed_at": feedback.reviewed_at.strftime("%Y-%m-%d %H:%M"),
            })

        project_id = entry.comparison_file.project_id
        file_id = entry.comparison_file_id
        return redirect("review_feedback:comparison_detail", project_id=project_id, file_id=file_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    project_id = entry.comparison_file.project_id
    file_id = entry.comparison_file_id
    return redirect("review_feedback:comparison_detail", project_id=project_id, file_id=file_id)


def project_confirmed_report(request, project_id):
    """第二階段人工審查結果報表與匯出"""
    project = get_object_or_404(Project, pk=project_id)

    if not request.user.is_authenticated:
        from django.conf import settings as django_settings
        login_url = getattr(django_settings, "LOGIN_URL", "/accounts/login/")
        return redirect(f"{login_url}?next={request.path}")
    can_access = (
        request.user.is_superuser or request.user.is_staff
        or project.admins.filter(pk=request.user.pk).exists()
        or project.experts.filter(pk=request.user.pk).exists()
    )
    if not can_access:
        messages.error(request, "您沒有存取此專案的權限。")
        return redirect("review_feedback:project_list")

    entries = (
        ComparisonEntry.objects
        .filter(comparison_file__project=project, arbitration_status__in=["confirmed", "no_conflict"])
        .select_related("comparison_file")
        .prefetch_related("review_feedbacks__reviewer")
        .order_by("final_decision_class", "source_page", "char_start_pos")
    )

    if request.GET.get("export") == "json":
        export_data = []
        for entry in entries:
            latest_fb = entry.latest_feedback
            fb_data = None
            if latest_fb:
                fb_data = {
                    "is_correct": latest_fb.is_correct,
                    "correct_classification": latest_fb.correct_classification,
                    "feedback_reason": latest_fb.feedback_reason,
                    "additional_description": latest_fb.additional_description,
                    "reviewer": latest_fb.reviewer.get_full_name() or latest_fb.reviewer.username if latest_fb.reviewer else None,
                    "reviewed_at": latest_fb.reviewed_at.isoformat() if latest_fb.reviewed_at else None,
                }
            
            export_data.append({
                "entry_id": entry.pk,
                "file_name": entry.comparison_file.original_filename,
                "excerpt_text": entry.excerpt_text,
                "source_page": entry.source_page,
                "arbitration_status": entry.arbitration_status,
                "final_decision_class": entry.final_decision_class,
                "latest_feedback": fb_data,
            })
            
        response = JsonResponse(export_data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="project_{project.pk}_review_report.json"'
        return response

    # 包含最新 feedback 以便 template 直接拿
    report_entries = []
    for entry in entries:
        report_entries.append((entry, entry.latest_feedback))

    return render(request, "review_feedback/confirmed_report.html", {
        "project": project,
        "report_entries": report_entries,
        "confirmed_count": entries.count(),
        "has_pdf": bool(project.pdf_file),
        "pdf_url": project.pdf_file.url if project.pdf_file else None,
    })
