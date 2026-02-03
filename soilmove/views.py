import csv
import openpyxl
from datetime import datetime
from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Max
from django.core.management import call_command
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import SoilMove

class DashboardView(TemplateView):
    template_name = "soilmove/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cities'] = SoilMove.objects.values_list('city', flat=True).distinct().order_by('city')
        context['site_types'] = SoilMove.objects.values_list('site_type', flat=True).distinct().order_by('site_type')
        # Add status choices for filter
        context['statuses'] = ['正常', '停止']
        
        last_update = SoilMove.objects.aggregate(Max('updated_at'))['updated_at__max']
        context['last_updated'] = last_update
        return context

@method_decorator(csrf_exempt, name='dispatch')
class UpdateDataView(View):
    def post(self, request, *args, **kwargs):
        try:
            call_command('fetch_soil_data')
            last_update = SoilMove.objects.aggregate(Max('updated_at'))['updated_at__max']
            return JsonResponse({'status': 'success', 'last_updated': last_update})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class BaseFilterView(View):
    def get_queryset(self):
        city = self.request.GET.get('city')
        site_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        
        qs = SoilMove.objects.all()
        if city:
            qs = qs.filter(city=city)
        if site_type:
            qs = qs.filter(site_type=site_type)
        if status:
            qs = qs.filter(status=status)
        return qs

class SoilDataAPI(BaseFilterView):
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = []
        for item in qs:
            data.append({
                'id': item.site_id,
                'name': item.name,
                'city': item.city,
                'type': item.site_type,
                'status': item.status,  # Include status in API
                'remain': item.remain_capacity,
                'lat': item.latitude,
                'lng': item.longitude,
                'address': item.city,
                'manager': item.control_id,
                'area': item.area,
                'max_capacity': item.max_capacity,
                'apply_date': item.apply_date,
                'coord_status': item.coord_status,
            })
        return JsonResponse(data, safe=False)

class ExportExcelView(BaseFilterView):
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="soil_data_{timestamp}.xlsx"'

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Soil Data"

        # Added Status column
        headers = ['ID', '名稱', '縣市', '類型', '狀態', 'B1~B7剩餘填埋量', '轉換狀態', '流向編號', '經度', '緯度', '面積', 'B1~B7核准填埋量', '申報日期']
        ws.append(headers)

        for item in qs:
            ws.append([
                item.site_id,
                item.name,
                item.city,
                item.site_type,
                item.status,
                item.remain_capacity,
                item.coord_status,
                item.control_id,
                item.longitude,
                item.latitude,
                item.area,
                item.max_capacity,
                item.apply_date
            ])

        wb.save(response)
        return response

class ExportKMLView(BaseFilterView):
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        response = HttpResponse(content_type='application/vnd.google-earth.kml+xml')
        response['Content-Disposition'] = f'attachment; filename="soil_data_{timestamp}.kml"'
        
        kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <LookAt>
        <longitude>121.0</longitude>
        <latitude>23.7</latitude>
        <altitude>0</altitude>
        <heading>0</heading>
        <tilt>0</tilt>
        <range>450000</range>
    </LookAt>
"""
        kml_footer = """  </Document>
</kml>"""
        
        kml_body = ""
        for item in qs:
            if item.longitude is not None and item.latitude is not None:
                description = f"""
                <b>名稱:</b> {item.name}<br/>
                <b>縣市:</b> {item.city}<br/>
                <b>類型:</b> {item.site_type}<br/>
                <b>狀態:</b> {item.status}<br/>
                <b>剩餘填埋量:</b> {item.remain_capacity}<br/>
                <b>核准填埋量:</b> {item.max_capacity}<br/>
                <b>面積:</b> {item.area}<br/>
                <b>申報日期:</b> {item.apply_date}<br/>
                <b>流向編號:</b> {item.control_id}<br/>
                """
                kml_body += f"""
    <Placemark>
      <name>{item.name}</name>
      <description><![CDATA[{description}]]></description>
      <Point>
        <coordinates>{item.longitude},{item.latitude},0</coordinates>
      </Point>
    </Placemark>
"""
        
        response.write(kml_header + kml_body + kml_footer)
        return response
