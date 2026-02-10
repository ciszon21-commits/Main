import os
import tempfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import ComparisonIssue, ComparisonRun, Project, ProjectFile
from .processing import (
    build_budget_stats,
    build_compare_suggestion,
    build_quantity_stats,
    build_stats_workbook,
    extract_budget_rows,
    extract_quantity_rows,
    parse_xls_structure,
    parse_xml_structure,
    run_compare,
)

try:
    from SynonymManager.models import SynonymGroup
except Exception:
    SynonymGroup = None


FILE_TYPE_CONFIG = {
    ProjectFile.FILE_TYPE_BUDGET: {
        "label": "Budget XML",
        "extensions": [".xml"],
    },
    ProjectFile.FILE_TYPE_QUANTITY: {
        "label": "Quantity XLS/XLSX",
        "extensions": [".xls", ".xlsx"],
    },
    ProjectFile.FILE_TYPE_SPEC_PDF: {
        "label": "Spec PDF",
        "extensions": [".pdf"],
        "disabled": True,
    },
    ProjectFile.FILE_TYPE_SPEC_DOC: {
        "label": "Spec DOC/DOCX",
        "extensions": [".doc", ".docx"],
        "disabled": True,
    },
}


def _normalize_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def _build_synonym_map() -> dict[str, str]:
    if SynonymGroup is None:
        return {}
    mapping: dict[str, str] = {}
    for group in SynonymGroup.objects.all():
        canonical = group.word.strip()
        if not canonical:
            continue
        mapping[canonical] = canonical
        for synonym in group.synonym_list.split(","):
            synonym = synonym.strip()
            if synonym:
                mapping[synonym] = canonical
    return mapping


@login_required
def dashboard(request):
    projects = Project.objects.filter(owner=request.user)
    project_form = ProjectForm()

    if request.method == "POST" and request.POST.get("action") == "create_project":
        project_form = ProjectForm(request.POST)
        if project_form.is_valid():
            project = project_form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, "Project created.")
            return redirect("design_consistency:dashboard")
        messages.error(request, "Please check the project details.")

    file_count = ProjectFile.objects.filter(project__owner=request.user).count()
    latest_project = projects.first()
    context = {
        "projects": projects,
        "project_form": project_form,
        "project_count": projects.count(),
        "file_count": file_count,
        "latest_project": latest_project,
    }
    return render(request, "DesignConsistency/dashboard.html", context)


@login_required
def project_detail(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    files = project.files.all()
    latest_run = project.comparison_runs.first()

    if request.method == "POST" and request.POST.get("action") == "upload_file":
        file_type = request.POST.get("file_type")
        uploaded_file = request.FILES.get("file")

        if not file_type or file_type not in FILE_TYPE_CONFIG:
            messages.error(request, "Invalid file type.")
            return redirect("design_consistency:project_detail", project_id=project.id)

        if FILE_TYPE_CONFIG[file_type].get("disabled"):
            messages.warning(request, "This file type is not enabled yet.")
            return redirect("design_consistency:project_detail", project_id=project.id)

        if not uploaded_file:
            messages.error(request, "Please choose a file.")
            return redirect("design_consistency:project_detail", project_id=project.id)

        ext = _normalize_extension(uploaded_file.name)
        allowed = FILE_TYPE_CONFIG[file_type]["extensions"]
        if ext not in allowed:
            messages.error(
                request,
                f"Unsupported file extension. Allowed: {', '.join(allowed)}",
            )
            return redirect("design_consistency:project_detail", project_id=project.id)

        ProjectFile.objects.create(
            project=project,
            file_type=file_type,
            file=uploaded_file,
            original_name=uploaded_file.name,
            uploaded_by=request.user,
        )
        messages.success(request, "File uploaded.")
        return redirect("design_consistency:project_detail", project_id=project.id)

    if request.method == "POST" and request.POST.get("action") == "run_compare":
        budget_file = project.files.filter(file_type=ProjectFile.FILE_TYPE_BUDGET).first()
        quantity_file = project.files.filter(file_type=ProjectFile.FILE_TYPE_QUANTITY).first()
        if not budget_file or not quantity_file:
            messages.error(request, "Please upload both Budget XML and Quantity XLS/XLSX.")
            return redirect("design_consistency:project_detail", project_id=project.id)

        compare_mode = request.POST.get("compare_mode") or "balanced"
        budget_filter = request.POST.get("budget_filter") or ""
        run = ComparisonRun.objects.create(
            project=project,
            budget_file=budget_file,
            quantity_file=quantity_file,
        )
        try:
            synonym_map = _build_synonym_map()
            result, report_rel_path, issue_items = run_compare(
                budget_file_path=budget_file.file.path,
                quantity_file_path=quantity_file.file.path,
                synonym_map=synonym_map or None,
                compare_mode=compare_mode,
                budget_filter=budget_filter or None,
            )
            run.result = result
            run.status = ComparisonRun.STATUS_DONE
            run.notes = "Comparison completed."
            if report_rel_path:
                run.report_file.name = report_rel_path
                run.save(update_fields=["result", "status", "notes", "report_file"])
            else:
                run.save(update_fields=["result", "status", "notes"])
            issue_objects = [
                ComparisonIssue(
                    run=run,
                    issue_type=item["type"],
                    summary=item["summary"][:255],
                    payload=item.get("payload"),
                )
                for item in issue_items
            ]
            ComparisonIssue.objects.bulk_create(issue_objects, batch_size=200)
            messages.success(request, "Comparison completed.")
        except Exception as exc:
            run.status = ComparisonRun.STATUS_FAILED
            run.notes = str(exc)
            run.save(update_fields=["status", "notes"])
            messages.error(request, f"Comparison failed: {exc}")
        return redirect("design_consistency:project_detail", project_id=project.id)

    files_by_type = {}
    for file_type in FILE_TYPE_CONFIG.keys():
        files_by_type[file_type] = [f for f in files if f.file_type == file_type]

    stats_error = ""
    budget_stats = None
    quantity_stats = None
    compare_suggestion = None
    budget_file = project.files.filter(file_type=ProjectFile.FILE_TYPE_BUDGET).first()
    quantity_file = project.files.filter(file_type=ProjectFile.FILE_TYPE_QUANTITY).first()
    try:
        if budget_file:
            budget_rows = extract_budget_rows(budget_file.file.path)
            budget_stats = build_budget_stats(budget_rows)
        if quantity_file:
            quantity_rows = extract_quantity_rows(quantity_file.file.path)
            quantity_stats = build_quantity_stats(quantity_rows)
        compare_suggestion = build_compare_suggestion(budget_stats, quantity_stats)
        if compare_suggestion:
            mode_label_map = {
                "classic": "經典（原始方法）",
                "strict": "嚴格（高精準）",
                "balanced": "平衡（預設）",
                "lenient": "寬鬆（高召回）",
            }
            filter_label_map = {
                "quantity_only": "只比對有數量",
                "analysis_only": "僅分析/一般項且有數量",
                "": "不篩選",
                None: "不篩選",
            }
            compare_suggestion = {
                **compare_suggestion,
                "mode_label": mode_label_map.get(compare_suggestion.get("mode"), compare_suggestion.get("mode")),
                "filter_label": filter_label_map.get(compare_suggestion.get("budget_filter")),
            }
    except Exception as exc:
        stats_error = str(exc)

    context = {
        "project": project,
        "files": files,
        "files_by_type": files_by_type,
        "file_type_config": FILE_TYPE_CONFIG,
        "latest_run": latest_run,
        "budget_stats": budget_stats,
        "quantity_stats": quantity_stats,
        "stats_error": stats_error,
        "compare_suggestion": compare_suggestion,
    }
    return render(request, "DesignConsistency/project_detail.html", context)


@login_required
def matrix(request):
    projects = Project.objects.filter(owner=request.user)
    project_id = request.GET.get("project")
    if project_id:
        project = get_object_or_404(Project, pk=project_id, owner=request.user)
    else:
        project = projects.first()

    latest_run = project.comparison_runs.first() if project else None

    issue_types = [
        ("unmatched_budget", "預算缺漏"),
        ("unmatched_quantity", "數量缺漏"),
        ("name_variance", "名稱差異"),
        ("unit_mismatch", "單位不一致"),
        ("qty_mismatch", "數量不一致"),
        ("low_confidence", "低信心匹配"),
    ]
    statuses = [
        ("pending", "待確認"),
        ("confirmed", "確定不一致"),
        ("false_positive", "誤判"),
    ]

    matrix_counts = {it[0]: {st[0]: 0 for st in statuses} for it in issue_types}
    total_by_type = {it[0]: 0 for it in issue_types}
    total_by_status = {st[0]: 0 for st in statuses}

    total_issues = 0
    if latest_run:
        rows = (
            latest_run.issues.values("issue_type", "status")
            .order_by()
            .annotate(count=models.Count("id"))
        )
        for row in rows:
            issue_type = row["issue_type"]
            status = row["status"]
            count = row["count"]
            if issue_type in matrix_counts and status in matrix_counts[issue_type]:
                matrix_counts[issue_type][status] = count
                total_by_type[issue_type] += count
                total_by_status[status] += count
                total_issues += count

    recent_issues = latest_run.issues.all()[:10] if latest_run else []

    context = {
        "projects": projects,
        "project": project,
        "latest_run": latest_run,
        "issue_types": issue_types,
        "statuses": statuses,
        "matrix_counts": matrix_counts,
        "total_by_type": total_by_type,
        "total_by_status": total_by_status,
        "total_issues": total_issues,
        "recent_issues": recent_issues,
    }
    return render(request, "DesignConsistency/matrix.html", context)


@login_required
def report_detail(request, run_id: int):
    run = get_object_or_404(
        ComparisonRun,
        pk=run_id,
        project__owner=request.user,
    )

    if request.method == "POST":
        issue_id = request.POST.get("issue_id")
        status = request.POST.get("status")
        note = request.POST.get("note", "")
        if issue_id and status:
            issue = get_object_or_404(ComparisonIssue, pk=issue_id, run=run)
            issue.status = status
            issue.note = note
            issue.save(update_fields=["status", "note"])
            messages.success(request, "Issue annotation updated.")
        return redirect("design_consistency:report_detail", run_id=run.id)

    issue_type = request.GET.get("type")
    status = request.GET.get("status")
    method = request.GET.get("method")
    show_summary = request.GET.get("show_summary", "1") != "0"
    show_payload = request.GET.get("show_payload", "1") != "0"
    show_name_diff = request.GET.get("show_name_diff", "1") != "0"
    show_matches = request.GET.get("show_matches", "1") != "0"
    match_filter = request.GET.get("match_filter", "consistent")

    issues = run.issues.all()
    if issue_type:
        issues = issues.filter(issue_type=issue_type)
    if status:
        issues = issues.filter(status=status)
    if method:
        issues = issues.filter(payload__method=method)

    stats = run.issues.values("status").order_by().annotate(count=models.Count("id"))
    status_counts = {row["status"]: row["count"] for row in stats}
    method_options = [
        ("exact", "精準匹配"),
        ("item_no", "項次匹配"),
        ("signature", "特徵匹配"),
        ("fuzzy", "模糊匹配"),
        ("global_fuzzy", "全域模糊"),
    ]
    match_filter_options = [
        ("consistent", "只看一致"),
        ("inconsistent", "只看不一致"),
        ("all", "全部匹配"),
    ]

    matched_items = []
    if run.result and isinstance(run.result, dict):
        matched_items = list(run.result.get("matched_items") or [])
    if match_filter == "consistent":
        matched_items = [item for item in matched_items if item.get("consistent")]
    elif match_filter == "inconsistent":
        matched_items = [item for item in matched_items if not item.get("consistent")]

    context = {
        "run": run,
        "project": run.project,
        "issues": issues,
        "issue_type": issue_type or "",
        "status": status or "",
        "method": method or "",
        "method_options": method_options,
        "match_filter": match_filter,
        "match_filter_options": match_filter_options,
        "show_matches": show_matches,
        "matched_items": matched_items,
        "show_summary": show_summary,
        "show_payload": show_payload,
        "show_name_diff": show_name_diff,
        "status_counts": status_counts,
    }
    return render(request, "DesignConsistency/report_detail.html", context)


@login_required
def export_stats(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    kind = request.GET.get("kind", "budget")
    format_type = request.GET.get("format", "csv")
    if kind not in {"budget", "quantity"}:
        return HttpResponse("Invalid kind.", status=400)
    if format_type not in {"csv", "xlsx"}:
        return HttpResponse("Invalid format.", status=400)

    budget_file = project.files.filter(file_type=ProjectFile.FILE_TYPE_BUDGET).first()
    quantity_file = project.files.filter(file_type=ProjectFile.FILE_TYPE_QUANTITY).first()

    if kind == "budget":
        if not budget_file:
            return HttpResponse("Budget XML not found.", status=404)
        budget_rows = extract_budget_rows(budget_file.file.path)
        stats = build_budget_stats(budget_rows)
        filename = f"budget_stats_{project.id}.{format_type}"
        rows = [
            ["預算書統計"],
            ["總項目數", stats.get("total")],
            ["名稱去重", stats.get("unique_total")],
            ["名稱去重佔比", stats.get("unique_ratio")],
            ["只比對有數量", stats.get("quantity_only")],
            ["分析/一般項且有數量", stats.get("analysis_only")],
            [],
            ["類型", "項目數", "名稱去重", "名稱去重佔比"],
        ]
        for item in stats.get("by_kind_cn", []):
            rows.append(
                [item.get("label"), item.get("count"), item.get("unique_count"), item.get("unique_ratio")]
            )
    else:
        if not quantity_file:
            return HttpResponse("Quantity XLS/XLSX not found.", status=404)
        quantity_rows = extract_quantity_rows(quantity_file.file.path)
        stats = build_quantity_stats(quantity_rows)
        filename = f"quantity_stats_{project.id}.{format_type}"
        rows = [
            ["數量計算書統計"],
            ["總項目數", stats.get("total")],
            ["名稱去重", stats.get("unique_total")],
            ["名稱去重佔比", stats.get("unique_ratio")],
            [],
            ["工作表", "項目數", "名稱去重", "名稱去重佔比"],
        ]
        for item in stats.get("by_sheet_cn", []):
            rows.append(
                [item.get("sheet"), item.get("count"), item.get("unique_count"), item.get("unique_ratio")]
            )

    if format_type == "xlsx":
        other_stats = None
        if kind == "budget" and quantity_file:
            quantity_rows = extract_quantity_rows(quantity_file.file.path)
            other_stats = build_quantity_stats(quantity_rows)
        if kind == "quantity" and budget_file:
            budget_rows = extract_budget_rows(budget_file.file.path)
            other_stats = build_budget_stats(budget_rows)
        wb = build_stats_workbook(
            project_name=project.name,
            budget_stats=stats if kind == "budget" else other_stats,
            quantity_stats=stats if kind == "quantity" else other_stats,
        )
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    for row in rows:
        response.write(",".join("" if v is None else str(v) for v in row) + "\n")
    return response


@login_required
@require_POST
def preview_xls(request):
    """
    Preview XLS/XLSX file structure via AJAX.
    Returns JSON with sheet information and structure analysis.
    """
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "請選擇檔案"}, status=400)
    
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in (".xls", ".xlsx"):
        return JsonResponse({"error": "只支援 .xls 或 .xlsx 格式"}, status=400)
    
    try:
        # Save to temporary file for parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        result = parse_xls_structure(tmp_path)
        result["filename"] = uploaded_file.name  # Use original filename
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return JsonResponse({"success": True, "data": result})
    except Exception as exc:
        return JsonResponse({"error": f"解析失敗：{str(exc)}"}, status=500)


@login_required
@require_POST
def preview_xml(request):
    """
    Preview XML budget file structure via AJAX.
    Returns JSON with contract info and hierarchical structure.
    """
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "請選擇檔案"}, status=400)
    
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext != ".xml":
        return JsonResponse({"error": "只支援 .xml 格式"}, status=400)
    
    try:
        # Save to temporary file for parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        result = parse_xml_structure(tmp_path)
        result["filename"] = uploaded_file.name  # Use original filename
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return JsonResponse({"success": True, "data": result})
    except Exception as exc:
        return JsonResponse({"error": f"解析失敗：{str(exc)}"}, status=500)
