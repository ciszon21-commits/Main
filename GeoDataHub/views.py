"""
GeoDataHub Views
=================
視圖與 API 端點
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.views import View
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse_lazy
from decimal import Decimal
import json

from .models import GeoCategory, GeoLocation, GeoDataSource, DataTag, GeoDataView, GeoClickLog
from .forms import GeoLocationForm, GeoDataSourceForm, GeoSearchForm, GeoCategoryForm
from .services import GeocodingService, GeoQueryService, OpenSearchGeoService


class SuperuserRequiredMixin(UserPassesTestMixin):
    """只允許 superuser 存取的 Mixin"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser
    
    def handle_no_permission(self):
        from django.contrib import messages
        messages.error(self.request, '此功能僅限管理員使用')
        return redirect('geodatahub:map')




class MapView(TemplateView):
    """主地圖頁面"""
    template_name = 'GeoDataHub/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 取得分類列表
        # 取得分類列表
        categories = GeoCategory.objects.filter(is_active=True).annotate(
            source_count=Count('data_sources', filter=Q(data_sources__is_visible=True, data_sources__location__isnull=False))
        ).order_by('sort_order', 'name')
        
        # 取得總數 (已有座標的項目)
        total_count = GeoDataSource.objects.filter(is_visible=True, location__isnull=False).count()
        
        context['categories'] = categories
        context['total_count'] = total_count
        context['search_form'] = GeoSearchForm()
        
        # 預設中心點：台灣
        context['default_center'] = {
            'lat': 23.6978,
            'lng': 120.9605,
            'zoom': 7
        }
        
        return context


class DashboardView(TemplateView):
    """使用量儀表板"""
    template_name = 'GeoDataHub/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 30 Days Daily Stats
        last_30_days = timezone.now() - timedelta(days=30)
        daily_stats = GeoClickLog.objects.filter(
            created_at__gte=last_30_days
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # 12 Months Monthly Stats
        last_12_months = timezone.now() - timedelta(days=365)
        monthly_stats = GeoClickLog.objects.filter(
            created_at__gte=last_12_months
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Format for Chart.js / Display
        context['daily_labels'] = [d['date'].strftime('%Y-%m-%d') for d in daily_stats]
        context['daily_data'] = [d['count'] for d in daily_stats]
        
        context['monthly_labels'] = [m['month'].strftime('%Y-%m') for m in monthly_stats]
        context['monthly_data'] = [m['count'] for m in monthly_stats]
        
        
        # Superuser Only: Recent Logs
        if self.request.user.is_superuser:
            context['recent_logs'] = GeoClickLog.objects.select_related(
                'source', 'user', 'category'
            ).order_by('-created_at')[:100]
            
        return context


class CategoryListAPI(View):
    """分類列表 API"""
    
    def get(self, request):
        # 取得邊界參數
        north = request.GET.get('north')
        south = request.GET.get('south')
        east = request.GET.get('east')
        west = request.GET.get('west')
        
        bounds = None
        if all([north, south, east, west]):
            bounds = {
                'north': float(north),
                'south': float(south),
                'east': float(east),
                'west': float(west)
            }
        
        service = GeoQueryService()
        categories = service.get_categories_with_counts(bounds)
        
        return JsonResponse({
            'success': True,
            'categories': categories
        })


class GeoSearchAPI(View):
    """地理搜尋 API"""
    
    def get(self, request):
        # 解析參數
        try:
            north = float(request.GET.get('north', 25.3))
            south = float(request.GET.get('south', 21.9))
            east = float(request.GET.get('east', 122.0))
            west = float(request.GET.get('west', 120.0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid bounds'}, status=400)
        
        category_id = request.GET.get('category')
        keyword = request.GET.get('keyword', '').strip()
        source_type = request.GET.get('source_type', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 2000))
        
        if category_id:
            try:
                category_id = int(category_id)
            except ValueError:
                category_id = None
        
        # 執行搜尋
        service = GeoQueryService()
        result = service.search_by_bounds(
            north=north,
            south=south,
            east=east,
            west=west,
            category_id=category_id,
            keyword=keyword if keyword else None,
            source_type=source_type if source_type else None,
            limit=2000  # 提高上限以顯示更多點
        )
        
        # 分頁處理
        paginator = Paginator(list(result['results']), page_size)
        page_obj = paginator.get_page(page)
        
        # 序列化結果
        items = []
        for source in page_obj:
            item = {
                'id': source.id,
                'title': source.title,
                'description': source.description[:200] if source.description else '',
                'source_type': source.source_type,
                'category': {
                    'id': source.category.id,
                    'name': source.category.name,
                    'icon': source.category.icon,
                    'color': source.category.color
                } if source.category else None,
                'view_count': source.view_count,
                'metadata': source.metadata,
            }
            
            if source.location:
                item['location'] = {
                    'lat': float(source.location.latitude),
                    'lng': float(source.location.longitude),
                    'address': source.location.address
                }
            
            items.append(item)
        
        return JsonResponse({
            'success': True,
            'count': result['count'],
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'items': items
        })


class GeoCountAPI(View):
    """區域資料數量 API"""
    
    def get(self, request):
        try:
            north = float(request.GET.get('north'))
            south = float(request.GET.get('south'))
            east = float(request.GET.get('east'))
            west = float(request.GET.get('west'))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid bounds'}, status=400)
        
        category_id = request.GET.get('category')
        if category_id:
            try:
                category_id = int(category_id)
            except ValueError:
                category_id = None
        
        service = GeoQueryService()
        count = service.count_by_area(
            north=north,
            south=south,
            east=east,
            west=west,
            category_id=category_id
        )
        
        return JsonResponse({
            'success': True,
            'count': count
        })


class GeocodeAPI(View):
    """地址轉座標 API"""
    
    def get(self, request):
        address = request.GET.get('address', '').strip()
        if not address:
            return JsonResponse({'success': False, 'error': 'Address required'}, status=400)
        
        country = request.GET.get('country', 'TW')
        
        service = GeocodingService()
        result = service.geocode_address(address, country)
        
        if result:
            return JsonResponse({
                'success': True,
                'result': {
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'display_name': result['display_name'],
                    'confidence': result['confidence']
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '找不到此地址'
            })


class ReverseGeocodeAPI(View):
    """座標轉地址 API"""
    
    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lng = float(request.GET.get('lng'))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid coordinates'}, status=400)
        
        service = GeocodingService()
        result = service.reverse_geocode(lat, lng)
        
        if result:
            return JsonResponse({
                'success': True,
                'result': result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '找不到此位置的地址資訊'
            })


class DataSourceListView(ListView):
    """資料來源列表頁面"""
    model = GeoDataSource
    template_name = 'GeoDataHub/source_list.html'
    context_object_name = 'sources'
    paginate_by = 20

    def get_queryset(self):
        queryset = GeoDataSource.objects.filter(is_visible=True).select_related(
            'location', 'category', 'created_by'
        ).prefetch_related('tags')
        
        # 分類篩選
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # 關鍵字搜尋
        keyword = self.request.GET.get('keyword', '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword)
            )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = GeoCategory.objects.filter(is_active=True)
        context['current_category'] = self.request.GET.get('category')
        context['current_keyword'] = self.request.GET.get('keyword', '')
        return context


class DataSourceDetailView(DetailView):
    """資料來源詳情頁面"""
    model = GeoDataSource
    template_name = 'GeoDataHub/source_detail.html'
    context_object_name = 'source'

    def get_queryset(self):
        return GeoDataSource.objects.select_related(
            'location', 'category', 'created_by'
        ).prefetch_related('tags')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # 記錄瀏覽
        source = self.object
        source.increment_view_count()
        
        # 建立瀏覽記錄
        GeoDataView.objects.create(
            source=source,
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key or '',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class DataSourceDeleteView(SuperuserRequiredMixin, DeleteView):
    """刪除資料來源 - 僅限 Superuser"""
    model = GeoDataSource
    success_url = reverse_lazy('geodatahub:map')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        return obj
    
    def form_valid(self, form):
        # 同時刪除關聯的 location
        if self.object.location:
            location = self.object.location
            self.object.location = None
            self.object.save()
            location.delete()
        
        from django.contrib import messages
        messages.success(self.request, f'已成功刪除「{self.object.title}」')
        return super().form_valid(form)


class DataSourceDeleteAPI(View):
    """AJAX 刪除資料來源 API - 僅限 Superuser"""
    
    def post(self, request, pk):
        # 檢查權限
        if not request.user.is_authenticated or not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': '權限不足'}, status=403)
        
        try:
            source = get_object_or_404(GeoDataSource, pk=pk)
            title = source.title
            
            # 刪除關聯的 location
            if source.location:
                location = source.location
                source.location = None
                source.save()
                location.delete()
            
            # 刪除資料來源
            source.delete()
            
            return JsonResponse({'success': True, 'message': f'已刪除「{title}」'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class DataSourceCreateView(LoginRequiredMixin, CreateView):
    """新增資料來源"""
    model = GeoDataSource
    form_class = GeoDataSourceForm
    template_name = 'GeoDataHub/source_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location_form'] = GeoLocationForm()
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        # 處理地理位置
        location_data = self._get_location_data()
        if location_data:
            location = GeoLocation.objects.create(**location_data)
            form.instance.location = location
        
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def _get_location_data(self):
        lat = self.request.POST.get('latitude')
        lng = self.request.POST.get('longitude')
        
        if lat and lng:
            try:
                return {
                    'latitude': Decimal(lat),
                    'longitude': Decimal(lng),
                    'address': self.request.POST.get('address', ''),
                    'city': self.request.POST.get('city', ''),
                    'district': self.request.POST.get('district', ''),
                    'country': self.request.POST.get('country', '台灣'),
                    'is_manually_adjusted': self.request.POST.get('is_manually_adjusted') == 'on'
                }
            except:
                return None
        return None

    def get_success_url(self):
        return self.object.get_absolute_url() if hasattr(self.object, 'get_absolute_url') else '/geodatahub/'


class DataSourceUpdateView(LoginRequiredMixin, UpdateView):
    """編輯資料來源"""
    model = GeoDataSource
    form_class = GeoDataSourceForm
    template_name = 'GeoDataHub/source_form.html'

    def get_queryset(self):
        # 只能編輯自己建立的
        return GeoDataSource.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.location:
            context['location_form'] = GeoLocationForm(instance=self.object.location)
        else:
            context['location_form'] = GeoLocationForm()
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        # 處理地理位置更新
        location_data = self._get_location_data()
        if location_data:
            if form.instance.location:
                for key, value in location_data.items():
                    setattr(form.instance.location, key, value)
                form.instance.location.save()
            else:
                location = GeoLocation.objects.create(**location_data)
                form.instance.location = location
        
        return super().form_valid(form)

    def _get_location_data(self):
        lat = self.request.POST.get('latitude')
        lng = self.request.POST.get('longitude')
        
        if lat and lng:
            try:
                return {
                    'latitude': Decimal(lat),
                    'longitude': Decimal(lng),
                    'address': self.request.POST.get('address', ''),
                    'city': self.request.POST.get('city', ''),
                    'district': self.request.POST.get('district', ''),
                    'country': self.request.POST.get('country', '台灣'),
                    'is_manually_adjusted': self.request.POST.get('is_manually_adjusted') == 'on'
                }
            except:
                return None
        return None


class MapMarkView(LoginRequiredMixin, TemplateView):
    """地圖標記介面 - 快速新增地理資料"""
    template_name = 'GeoDataHub/map_mark.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = GeoCategory.objects.filter(is_active=True)
        context['source_form'] = GeoDataSourceForm()
        context['location_form'] = GeoLocationForm()
        return context


class TagListAPI(View):
    """標籤列表 API (用於自動完成)"""
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        tags = DataTag.objects.all()
        if query:
            tags = tags.filter(name__icontains=query)
        
        tags = tags[:20]
        
        return JsonResponse({
            'success': True,
            'tags': [{'id': t.id, 'name': t.name} for t in tags]
        })


class OpenSearchGeoSearchAPI(View):
    """OpenSearch 地理搜尋 API"""
    
    def get(self, request):
        # 解析參數
        query = request.GET.get('query', '')
        indices = request.GET.get('indices', '*')
        
        try:
            north = float(request.GET.get('north', 25.3))
            south = float(request.GET.get('south', 21.9))
            east = float(request.GET.get('east', 122.0))
            west = float(request.GET.get('west', 120.0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid bounds'}, status=400)
        
        size = int(request.GET.get('size', 50))
        from_ = int(request.GET.get('from', 0))
        
        # 建構邊界
        bounds = {
            'top_left': {'lat': north, 'lon': west},
            'bottom_right': {'lat': south, 'lon': east}
        }
        
        service = OpenSearchGeoService()
        result = service.geo_bounding_box_search(
            query=query,
            indices=indices,
            bounds=bounds,
            size=size,
            from_=from_
        )
        
        if 'error' in result and result.get('hits', {}).get('total', {}).get('value', 0) == 0:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
        
        return JsonResponse({
            'success': True,
            'total': result.get('hits', {}).get('total', {}).get('value', 0),
            'hits': result.get('hits', {}).get('hits', [])
        })


class GeoClickLogAPI(View):
    """點擊記錄 API"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            source_id = data.get('source_id')
            category_id = data.get('category_id')
            click_type = data.get('click_type', 'view_detail')
            
            if not source_id:
                return JsonResponse({'success': False, 'error': 'Source ID required'}, status=400)

            # Get objects
            source = get_object_or_404(GeoDataSource, id=source_id)
            category = None
            if category_id:
                # Handle empty string or invalid id
                try:
                    category = GeoCategory.objects.filter(id=category_id).first()
                except (ValueError, TypeError):
                    pass
                
            # Create log
            GeoClickLog.objects.create(
                source=source,
                user=request.user if request.user.is_authenticated else None,
                category=category,
                click_type=click_type,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


# ============================================
# 分類管理 (僅限 Superuser)
# ============================================

class CategoryManageView(SuperuserRequiredMixin, ListView):
    """分類管理列表 - 僅限 Superuser"""
    model = GeoCategory
    template_name = 'GeoDataHub/category_manage.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return GeoCategory.objects.annotate(
            source_count=Count('data_sources')
        ).order_by('sort_order', 'name')


class CategoryCreateView(SuperuserRequiredMixin, CreateView):
    """新增分類 - 僅限 Superuser"""
    model = GeoCategory
    form_class = GeoCategoryForm
    template_name = 'GeoDataHub/category_form.html'
    success_url = reverse_lazy('geodatahub:category_manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        # 手動處理表單資料
        self.object = GeoCategory(
            name=self.request.POST.get('name', ''),
            icon=self.request.POST.get('icon', '📍'),
            color=self.request.POST.get('color', '#0000FF'),
            description=self.request.POST.get('description', ''),
            opensearch_pattern=self.request.POST.get('opensearch_pattern', ''),
            sort_order=int(self.request.POST.get('sort_order', 0) or 0),
            is_active=self.request.POST.get('is_active') == 'on'
        )
        self.object.save()
        return redirect(self.success_url)


class CategoryUpdateView(SuperuserRequiredMixin, UpdateView):
    """編輯分類 - 僅限 Superuser"""
    model = GeoCategory
    form_class = GeoCategoryForm
    template_name = 'GeoDataHub/category_form.html'
    success_url = reverse_lazy('geodatahub:category_manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        # 手動處理表單資料
        self.object.name = self.request.POST.get('name', '')
        self.object.icon = self.request.POST.get('icon', '📍')
        self.object.color = self.request.POST.get('color', '#0000FF')
        self.object.description = self.request.POST.get('description', '')
        self.object.opensearch_pattern = self.request.POST.get('opensearch_pattern', '')
        self.object.sort_order = int(self.request.POST.get('sort_order', 0) or 0)
        self.object.is_active = self.request.POST.get('is_active') == 'on'
        self.object.save()
        return redirect(self.success_url)

