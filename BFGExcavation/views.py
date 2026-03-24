import csv
import base64

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
import codecs

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import FoundationExcavation
from .services import ExcavationService
from .forms import FoundationForm, CSVImportForm


# ────────────────────────────────────────────────
# Page Views
# ────────────────────────────────────────────────

class DashboardView(TemplateView):
    template_name = "BFGExcavation/dashboard.html"


class Excavation3DView(TemplateView):
    template_name = "BFGExcavation/index.html"


class FoundationCreateView(CreateView):
    model = FoundationExcavation
    form_class = FoundationForm
    template_name = "BFGExcavation/foundation_form.html"
    success_url = reverse_lazy('bfg:dashboard')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = '新增基礎資料'
        ctx['submit_label'] = '新增'
        # Pre-fill from query params
        ctx['default_project'] = self.request.GET.get('project_code', '')
        ctx['default_bridge'] = self.request.GET.get('bridge_name', '')
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial['project_code'] = self.request.GET.get('project_code', '')
        initial['bridge_name'] = self.request.GET.get('bridge_name', '')
        return initial

    def form_valid(self, form):
        messages.success(self.request, f"基礎 「{form.instance.bridge_id}」 已成功新增！")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "表單資料有誤，請檢查後重新提交。")
        return super().form_invalid(form)


class FoundationUpdateView(UpdateView):
    model = FoundationExcavation
    form_class = FoundationForm
    template_name = "BFGExcavation/foundation_form.html"
    success_url = reverse_lazy('bfg:dashboard')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = f'編輯基礎：{self.object.bridge_id}'
        ctx['submit_label'] = '儲存變更'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"基礎 「{form.instance.bridge_id}」 已成功更新！")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "表單資料有誤，請檢查後重新提交。")
        return super().form_invalid(form)


class FoundationDeleteView(DeleteView):
    model = FoundationExcavation
    template_name = "BFGExcavation/foundation_confirm_delete.html"
    success_url = reverse_lazy('bfg:dashboard')

    def form_valid(self, form):
        bridge_id = self.object.bridge_id
        messages.success(self.request, f"基礎 「{bridge_id}」 已成功刪除。")
        return super().form_valid(form)


class CSVImportView(TemplateView):
    template_name = "BFGExcavation/csv_import.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = CSVImportForm()
        return ctx

    def post(self, request, *args, **kwargs):
        # Stage 2: Confirmation
        if 'csv_data_b64' in request.POST:
            csv_data_b64 = request.POST['csv_data_b64']
            decoded_file = base64.b64decode(csv_data_b64).decode('utf-8')
            ui_project_code = request.POST.get('project_code_ui', '')
            ui_bridge_name = request.POST.get('bridge_name_ui', '')
            overwrite_ids = request.POST.getlist('overwrite_ids')

            reader = csv.DictReader(decoded_file.splitlines())
            created_count = updated_count = skipped_count = 0

            for row in reader:
                bridge_id = str(row.get('基礎名稱', row.get('bridge_id', ''))).strip()
                if not row or not bridge_id:
                    continue
                row_project = str(row.get('計畫編號', row.get('project_code', ''))).strip() or ui_project_code
                row_bridge = str(row.get('橋梁名稱', row.get('bridge_name', ''))).strip() or ui_bridge_name
                full_id = f"{row_project}__{row_bridge}__{bridge_id}"
                defaults = self._parse_row_defaults(row)

                exists = FoundationExcavation.objects.filter(
                    project_code=row_project, bridge_name=row_bridge, bridge_id=bridge_id
                ).exists()

                if exists:
                    if full_id in overwrite_ids:
                        defaults['needs_review'] = True
                        FoundationExcavation.objects.filter(
                            project_code=row_project, bridge_name=row_bridge, bridge_id=bridge_id
                        ).update(**defaults)
                        updated_count += 1
                    else:
                        skipped_count += 1
                else:
                    full_defaults = self._get_full_defaults(defaults)
                    FoundationExcavation.objects.create(
                        project_code=row_project, bridge_name=row_bridge,
                        bridge_id=bridge_id, **full_defaults
                    )
                    created_count += 1

            messages.success(request, f"CSV 匯入完成：新增 {created_count} 筆，更新 {updated_count} 筆，跳過 {skipped_count} 筆。")
            return redirect('bfg:dashboard')

        # Stage 1: Upload file
        form = CSVImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        csv_file = request.FILES.get('csv_file')
        ui_project_code = form.cleaned_data.get('project_code', '') or 'Default Project'
        ui_bridge_name = form.cleaned_data.get('bridge_name', '') or 'Default Bridge'

        try:
            raw_data = csv_file.read()
            try:
                content = raw_data.decode('utf-8-sig')
            except UnicodeDecodeError:
                content = raw_data.decode('big5', errors='ignore')

            csv_data_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            reader = csv.DictReader(content.splitlines())
            conflicts = []
            new_records = []

            for row in reader:
                bid_key = row.get('基礎名稱') or row.get('bridge_id', '')
                bridge_id = str(bid_key).strip()
                if not bridge_id:
                    continue
                row_project = str(row.get('計畫編號', row.get('project_code', ''))).strip() or ui_project_code
                row_bridge = str(row.get('橋梁名稱', row.get('bridge_name', ''))).strip() or ui_bridge_name

                if FoundationExcavation.objects.filter(
                    project_code=row_project, bridge_name=row_bridge, bridge_id=bridge_id
                ).exists():
                    conflicts.append({
                        'project_code': row_project,
                        'bridge_name': row_bridge,
                        'bridge_id': bridge_id,
                        'full_id': f"{row_project}__{row_bridge}__{bridge_id}"
                    })
                else:
                    new_records.append(bridge_id)

            if conflicts:
                ctx = {
                    'conflicts': conflicts,
                    'new_records_count': len(new_records),
                    'csv_data_b64': csv_data_b64,
                    'project_code_ui': ui_project_code,
                    'bridge_name_ui': ui_bridge_name,
                }
                return render(request, 'BFGExcavation/csv_import_confirm.html', ctx)

            # No conflicts - import directly
            reader = csv.DictReader(content.splitlines())
            success_count = 0
            for row in reader:
                bid_key = row.get('基礎名稱') or row.get('bridge_id', '')
                bridge_id = str(bid_key).strip()
                if not bridge_id:
                    continue
                row_project = str(row.get('計畫編號', row.get('project_code', ''))).strip() or ui_project_code
                row_bridge = str(row.get('橋梁名稱', row.get('bridge_name', ''))).strip() or ui_bridge_name
                defaults = self._parse_row_defaults(row)
                full_defaults = self._get_full_defaults(defaults)
                FoundationExcavation.objects.create(
                    project_code=row_project, bridge_name=row_bridge,
                    bridge_id=bridge_id, **full_defaults
                )
                success_count += 1

            messages.success(request, f"CSV 匯入完成：共匯入 {success_count} 筆新資料。")
            return redirect('bfg:dashboard')

        except Exception as e:
            messages.error(request, f"檔案處理錯誤：{str(e)}")
            return render(request, self.template_name, {'form': form})

    def _parse_row_defaults(self, row):
        def safe_float(val, default=0.0):
            try:
                return float(val) if val and str(val).strip() else default
            except (ValueError, TypeError):
                return default

        def add_float(d, field, keys, default=0.0):
            for k in keys:
                if k in row:
                    d[field] = safe_float(row[k], default)
                    return

        def add_str(d, field, keys, default=''):
            for k in keys:
                if k in row:
                    val = row[k]
                    d[field] = str(val).strip() if val else default
                    return

        defaults = {}
        add_float(defaults, 'column_base_el', ['column_base_el', '柱底高程', '柱底EL', '柱底EL (m)'])
        add_float(defaults, 'h1_thickness', ['h1_thickness', '頂版厚度', '版厚', '版厚 H1', '版厚 H1 (m)'])
        add_float(defaults, 'c_pc_thickness', ['c_pc_thickness', 'PC厚度', 'PC厚', 'PC厚 C', 'PC厚 C (m)'])
        add_float(defaults, 'B1', ['B1', 'B1 (m)'])
        add_float(defaults, 'B2', ['B2', 'B2 (m)'])
        add_float(defaults, 'L1', ['L1', 'L1 (m)'])
        add_float(defaults, 'L2', ['L2', 'L2 (m)'])
        add_float(defaults, 'el_l1_start', ['el_l1_start', 'L1起點地表EL', 'L1起高程', 'L1起高程 (八向地表高程)'])
        add_float(defaults, 'el_l1_end', ['el_l1_end', 'L1終點地表EL', 'L1迄高程', 'L1迄高程 (八向地表高程)'])
        add_float(defaults, 'el_l2_start', ['el_l2_start', 'L2起點地表EL', 'L2起高程', 'L2起高程 (八向地表高程)'])
        add_float(defaults, 'el_l2_end', ['el_l2_end', 'L2終點地表EL', 'L2迄高程', 'L2迄高程 (八向地表高程)'])
        add_float(defaults, 'el_b1_start', ['el_b1_start', 'B1起點地表EL', 'B1起高程', 'B1起高程 (八向地表高程)'])
        add_float(defaults, 'el_b1_end', ['el_b1_end', 'B1終點地表EL', 'B1迄高程', 'B1迄高程 (八向地表高程)'])
        add_float(defaults, 'el_b2_start', ['el_b2_start', 'B2起點地表EL', 'B2起高程', 'B2起高程 (八向地表高程)'])
        add_float(defaults, 'el_b2_end', ['el_b2_end', 'B2終點地表EL', 'B2迄高程', 'B2迄高程 (八向地表高程)'])
        add_float(defaults, 'offset_dist', ['offset_dist', '各階支撐退縮距離', '偏心距 (m)', '各階支撐退縮距離 offset_dist (m)'], 0.8)
        add_float(defaults, 'd1_manual', ['d1_manual', '強制指定第一階支撐與地表之最小間距', 'D1', '結構參數 D1 (m)', 'D1 (m)'], 0.5)
        add_str(defaults, 'excavation_plan', ['開挖平面', 'excavation_plan'])
        add_str(defaults, 'excavation_section', ['開挖剖面', 'excavation_section'])
        add_float(defaults, 'skew_angle', ['夾角', 'skew_angle', '夾角 (°)', '夾角 skew_angle (°)'], 0.0)
        add_str(defaults, 'note', ['備註', 'note'])
        return defaults

    def _get_full_defaults(self, partial_defaults):
        full = {
            'column_base_el': 0.0, 'h1_thickness': 0.0, 'c_pc_thickness': 0.0,
            'B1': 0.0, 'B2': 0.0, 'L1': 0.0, 'L2': 0.0,
            'el_l1_start': 0.0, 'el_l1_end': 0.0, 'el_l2_start': 0.0, 'el_l2_end': 0.0,
            'el_b1_start': 0.0, 'el_b1_end': 0.0, 'el_b2_start': 0.0, 'el_b2_end': 0.0,
            'offset_dist': 0.8, 'd1_manual': 0.5,
            'excavation_plan': '', 'excavation_section': '', 'skew_angle': 0.0, 'note': '',
        }
        full.update(partial_defaults)
        return full


# ────────────────────────────────────────────────
# REST API Views (DRF)
# ────────────────────────────────────────────────

class FoundationExcavationAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, bridge_id=None):
        if bridge_id:
            project_code = request.query_params.get('project_code')
            bridge_name = request.query_params.get('bridge_name')
            try:
                qs = FoundationExcavation.objects.filter(bridge_id=bridge_id)
                if project_code:
                    qs = qs.filter(project_code=project_code)
                if bridge_name:
                    qs = qs.filter(bridge_name=bridge_name)
                foundation = qs.get()
                result = ExcavationService.process_foundation(foundation, foundation.d1_manual)
                return Response(result, status=status.HTTP_200_OK)
            except FoundationExcavation.DoesNotExist:
                return Response({'error': 'Foundation not found'}, status=status.HTTP_404_NOT_FOUND)
            except FoundationExcavation.MultipleObjectsReturned:
                return Response({'error': 'Multiple foundations found with same bridge_id.'}, status=status.HTTP_400_BAD_REQUEST)

        foundations = FoundationExcavation.objects.all().values('bridge_id', 'project_code', 'bridge_name')
        return Response(list(foundations), status=status.HTTP_200_OK)

    def post(self, request, bridge_id=None):
        if not bridge_id:
            bridge_id = request.data.get('bridge_id')
        try:
            qs = FoundationExcavation.objects.filter(bridge_id=bridge_id)
            if request.data.get('project_code'):
                qs = qs.filter(project_code=request.data.get('project_code'))
            if request.data.get('bridge_name'):
                qs = qs.filter(bridge_name=request.data.get('bridge_name'))
            foundation = qs.get()

            if request.data.get('clear_review'):
                foundation.needs_review = False
                foundation.save()
                return Response({"status": "cleared"}, status=status.HTTP_200_OK)

            save_needed = False
            numeric_fields = [
                'd1_manual', 'h1_thickness', 'c_pc_thickness', 'column_base_el',
                'skew_angle', 'B1', 'B2', 'L1', 'L2', 'offset_dist',
                'el_l1_start', 'el_l1_end', 'el_l2_start', 'el_l2_end',
                'el_b1_start', 'el_b1_end', 'el_b2_start', 'el_b2_end'
            ]
            for field in numeric_fields:
                val = request.data.get(field)
                if val is not None and str(val).strip() != '':
                    setattr(foundation, field, float(val))
                    save_needed = True

            for field in ['note', 'excavation_section']:
                val = request.data.get(field)
                if val is not None:
                    setattr(foundation, field, val.strip())
                    save_needed = True

            if save_needed:
                foundation.save()

            d1_manual = request.data.get('d1_manual')
            calc_result = ExcavationService.process_foundation(foundation, float(d1_manual) if d1_manual else None)
            return Response(calc_result, status=status.HTTP_200_OK)

        except FoundationExcavation.DoesNotExist:
            return Response({'error': 'Foundation not found'}, status=status.HTTP_404_NOT_FOUND)
        except FoundationExcavation.MultipleObjectsReturned:
            return Response({'error': 'Multiple foundations found with same bridge_id.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FoundationListView(APIView):
    def get(self, request):
        project_code = request.query_params.get('project_code')
        bridge_name = request.query_params.get('bridge_name')
        excavation_plan = request.query_params.get('excavation_plan')

        qs = FoundationExcavation.objects.all()
        if project_code:
            qs = qs.filter(project_code=project_code)
        if bridge_name:
            qs = qs.filter(bridge_name=bridge_name)
        if excavation_plan:
            qs = qs.filter(excavation_plan=excavation_plan)

        results = []
        for f in qs:
            calc_res = ExcavationService.process_foundation(f)
            max_el = max(calc_res['elevations'])
            min_el = min(calc_res['elevations'])
            calc_res['max_diff'] = round(max_el - min_el, 4)
            calc_res['needs_review'] = getattr(f, 'needs_review', False)
            calc_res['excavation_plan'] = getattr(f, 'excavation_plan', '')
            calc_res['excavation_section'] = getattr(f, 'excavation_section', '')
            calc_res['bridge_name'] = getattr(f, 'bridge_name', '')
            calc_res['skew_angle'] = getattr(f, 'skew_angle', 0.0)
            calc_res['note'] = getattr(f, 'note', '')
            results.append(calc_res)

        return Response(results, status=status.HTTP_200_OK)


class ProjectListView(APIView):
    def get(self, request):
        all_codes = FoundationExcavation.objects.values_list('project_code', flat=True)
        unique = sorted(set(v for v in all_codes if v))
        return Response(unique, status=status.HTTP_200_OK)


class BridgeListView(APIView):
    def get(self, request):
        project_code = request.query_params.get('project_code')
        qs = FoundationExcavation.objects.all()
        if project_code:
            qs = qs.filter(project_code=project_code)
        all_bridges = qs.values_list('bridge_name', flat=True)
        unique = sorted(set(v for v in all_bridges if v))
        return Response(unique, status=status.HTTP_200_OK)


class PlanListView(APIView):
    def get(self, request):
        project_code = request.query_params.get('project_code')
        qs = FoundationExcavation.objects.all()
        if project_code:
            qs = qs.filter(project_code=project_code)
        all_plans = qs.values_list('excavation_plan', flat=True)
        unique = sorted(set(v for v in all_plans if v and v.strip()))
        return Response(unique, status=status.HTTP_200_OK)


class FoundationStatsAPIView(APIView):
    """Returns aggregated stats about all foundations (counts by project/bridge)."""
    def get(self, request):
        from django.db.models import Count
        stats = (
            FoundationExcavation.objects
            .values('project_code', 'bridge_name')
            .annotate(count=Count('id'))
            .order_by('project_code', 'bridge_name')
        )
        return Response(list(stats), status=status.HTTP_200_OK)


class HierarchyAPIView(APIView):
    """
    Returns the full 3-level hierarchy: project → bridge → foundations.
    Each foundation includes id, bridge_id, key params, status flags, dates.
    """
    def get(self, request):
        from django.db.models import Count, Max, Min
        from django.db.models.functions import TruncDate

        qs = FoundationExcavation.objects.all().order_by(
            'project_code', 'bridge_name', 'bridge_id'
        ).values(
            'id', 'project_code', 'bridge_name', 'bridge_id',
            'excavation_plan', 'excavation_section',
            'column_base_el', 'h1_thickness', 'c_pc_thickness',
            'B1', 'B2', 'L1', 'L2', 'skew_angle',
            'offset_dist', 'd1_manual', 'note',
            'el_l1_start', 'el_l1_end', 'el_l2_start', 'el_l2_end',
            'el_b1_start', 'el_b1_end', 'el_b2_start', 'el_b2_end',
            'needs_review', 'created_at', 'updated_at',
        )

        # Build hierarchy in Python (avoids N+1, fields already fetched)
        projects = {}  # project_code → {bridges:{}, bridge_count, foundation_count, latest}
        for f in qs:
            pc = f['project_code']
            bn = f['bridge_name']

            if pc not in projects:
                projects[pc] = {'project_code': pc, 'bridges': {}, 'foundation_count': 0, 'bridge_count': 0, 'latest_date': None}

            if bn not in projects[pc]['bridges']:
                projects[pc]['bridges'][bn] = {'bridge_name': bn, 'foundations': [], 'foundation_count': 0, 'latest_date': None}

            # Date formatting
            created = f['created_at']
            updated = f['updated_at']
            latest = updated or created
            date_str = latest.strftime('%Y-%m-%d') if latest else '—'
            created_str = created.strftime('%Y-%m-%d') if created else '—'

            # Calculate D1~D4
            elevations = [
                f['el_l1_start'], f['el_l1_end'], f['el_l2_start'], f['el_l2_end'],
                f['el_b1_start'], f['el_b1_end'], f['el_b2_start'], f['el_b2_end']
            ]
            max_el = max(elevations)
            min_el = min(elevations)
            if max_el - min_el <= 1.0:
                reference_el = sum(elevations) / 8.0
            else:
                reference_el = max_el
            reference_el = round(reference_el * 20) / 20.0
            final_el = f['column_base_el'] - f['h1_thickness'] - f['c_pc_thickness']
            H = reference_el - final_el
            
            from .services import ExcavationService
            calc = ExcavationService.calculate_supports(
                H=H,
                reference_el=reference_el,
                h1_thickness=f['h1_thickness'],
                c_pc_thickness=f['c_pc_thickness'],
                d1_manual=f['d1_manual']
            )
            D_vals = calc.get('D', {})

            foundation_entry = {
                'id': f['id'],
                'bridge_id': f['bridge_id'],
                'excavation_plan': f['excavation_plan'] or '',
                'excavation_section': f['excavation_section'] or '',
                'column_base_el': f['column_base_el'],
                'h1_thickness': f['h1_thickness'],
                'c_pc_thickness': f['c_pc_thickness'],
                'B1': f['B1'], 'B2': f['B2'], 'L1': f['L1'], 'L2': f['L2'],
                'skew_angle': f['skew_angle'],
                'el_l1_start': f['el_l1_start'], 'el_l1_end': f['el_l1_end'],
                'el_l2_start': f['el_l2_start'], 'el_l2_end': f['el_l2_end'],
                'el_b1_start': f['el_b1_start'], 'el_b1_end': f['el_b1_end'],
                'el_b2_start': f['el_b2_start'], 'el_b2_end': f['el_b2_end'],
                'D1': D_vals.get('D1', ''),
                'D2': D_vals.get('D2', ''),
                'D3': D_vals.get('D3', ''),
                'D4': D_vals.get('D4', ''),
                'needs_review': f['needs_review'],
                'created_at': created_str,
                'updated_at': date_str,
            }
            projects[pc]['bridges'][bn]['foundations'].append(foundation_entry)
            projects[pc]['bridges'][bn]['foundation_count'] += 1

            # Track latest date per bridge / project
            if latest:
                bl = projects[pc]['bridges'][bn]['latest_date']
                if bl is None or latest > bl:
                    projects[pc]['bridges'][bn]['latest_date'] = latest
                pl = projects[pc]['latest_date']
                if pl is None or latest > pl:
                    projects[pc]['latest_date'] = latest

        # Finalise bridge/project counts and convert dates to strings
        result = []
        for pc, proj in projects.items():
            bridge_list = []
            for bn, bridge in proj['bridges'].items():
                ld = bridge['latest_date']
                bridge_list.append({
                    'bridge_name': bn,
                    'foundation_count': bridge['foundation_count'],
                    'latest_date': ld.strftime('%Y-%m-%d') if ld else '—',
                    'foundations': bridge['foundations'],
                })
            proj['bridge_count'] = len(bridge_list)
            proj['foundation_count'] = sum(b['foundation_count'] for b in bridge_list)
            ld = proj['latest_date']
            proj['latest_date'] = ld.strftime('%Y-%m-%d') if ld else '—'
            proj['bridges'] = bridge_list
            result.append(proj)

        return Response(result, status=status.HTTP_200_OK)

