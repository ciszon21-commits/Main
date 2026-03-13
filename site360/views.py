from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, DeleteView
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Max, Count
from django.db import models
from .forms import ProjectForm, SceneForm, ProjectMapSearchForm
from .models import Project, Scene, Hotspot, UserActionLog
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
import os
import re
import json
from django.conf import settings
from .mixins import UserActionLoggingMixin
from .decorators import user_action_logging

def get_cities(request):
    """API: 取得所有台灣縣市列表"""
    data_path = os.path.join(settings.BASE_DIR, 'site360', 'static', 'site360', 'data', 'taiwan_districts.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cities = list(data.keys())
        return JsonResponse({'cities': cities})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_districts(request):
    """API: 根據縣市取得區域列表"""
    city = request.GET.get('city')
    if not city:
        return JsonResponse({'districts': []})
        
    data_path = os.path.join(settings.BASE_DIR, 'site360', 'static', 'site360', 'data', 'taiwan_districts.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            districts = data.get(city, [])
        return JsonResponse({'districts': districts})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class ProjectListView(UserActionLoggingMixin, ListView):
    model = Project
    template_name = 'site360/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        queryset = super().get_queryset()
        project_code = self.request.GET.get('project_code')
        tender_code = self.request.GET.get('tender_code')
        tender_name = self.request.GET.get('tender_name')

        if project_code:
            queryset = queryset.filter(project_code__icontains=project_code)
        if tender_code:
            queryset = queryset.filter(tender_code__icontains=tender_code)
        if tender_name:
            queryset = queryset.filter(tender_name__icontains=tender_name)
            
        return queryset

class ProjectCreateView(UserActionLoggingMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'site360/project_form.html'
    success_url = reverse_lazy('site360:project_list')

class ProjectUpdateView(UserActionLoggingMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'site360/project_form.html'
    
    def get_success_url(self):
        return reverse_lazy('site360:project_detail', kwargs={'pk': self.object.pk})

class ProjectDeleteView(UserActionLoggingMixin, DeleteView):
    model = Project
    template_name = 'site360/project_confirm_delete.html'
    success_url = reverse_lazy('site360:project_list')
    context_object_name = 'project'

class ProjectMapView(UserActionLoggingMixin, TemplateView):
    template_name = 'site360/project_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Project
        from django.db.models import Q
        
        # Create search form with GET data
        search_form = ProjectMapSearchForm(self.request.GET or None)
        context['search_form'] = search_form
        
        # Start with all projects
        projects = Project.objects.all()
        
        # Apply search filters if form is valid
        if search_form.is_valid():
            search_query = search_form.cleaned_data.get('search_query')
            city_filter = search_form.cleaned_data.get('city')
            address_filter = search_form.cleaned_data.get('address')
            
            if search_query:
                projects = projects.filter(name__icontains=search_query)
            
            if city_filter:
                projects = projects.filter(city=city_filter)
            
            if address_filter:
                projects = projects.filter(
                    Q(city__icontains=address_filter) |
                    Q(district__icontains=address_filter) |
                    Q(address_detail__icontains=address_filter)
                )
        
        # Group projects by city for stats
        projects = projects.exclude(city='').order_by('city', '-created_at')
        
        cities_data = {}
        for p in projects:
            if p.city not in cities_data:
                cities_data[p.city] = []
            cities_data[p.city].append(p)
            
        # Convert to list of dicts and sort by count desc
        city_stats = []
        for city, proj_list in cities_data.items():
            city_stats.append({
                'city': city,
                'count': len(proj_list),
                'projects': proj_list
            })
        
        city_stats.sort(key=lambda x: x['count'], reverse=True)
        
        context['city_stats'] = city_stats
        return context

def project_map_data(request):
    """API: 回傳所有專案的地圖資料，包含熱點統計（支援搜尋篩選）"""
    from django.db.models import Count, Q
    
    # Start with projects that have coordinates
    projects = Project.objects.filter(latitude__isnull=False, longitude__isnull=False)
    
    # Apply search filters from GET parameters
    search_query = request.GET.get('search_query', '').strip()
    city_filter = request.GET.get('city', '').strip()
    address_filter = request.GET.get('address', '').strip()
    
    if search_query:
        projects = projects.filter(name__icontains=search_query)
    
    if city_filter:
        projects = projects.filter(city=city_filter)
    
    if address_filter:
        projects = projects.filter(
            Q(city__icontains=address_filter) |
            Q(district__icontains=address_filter) |
            Q(address_detail__icontains=address_filter)
        )
    
    # Annotate with hotspot counts
    projects = projects.annotate(
        text_count=Count('scenes__hotspots', filter=Q(scenes__hotspots__hotspot_type__in=['text', 'text_hover'])),
        image_count=Count('scenes__hotspots', filter=Q(scenes__hotspots__hotspot_type__in=['image', 'image_hover'])),
        video_count=Count('scenes__hotspots', filter=Q(scenes__hotspots__hotspot_type__in=['video', 'video_hover']))
    )
    
    data = []
    for p in projects:
        data.append({
             'id': p.id,
             'name': p.name,
             'lat': p.latitude,
             'lng': p.longitude,
             'cover': p.cover_image.url if p.cover_image else None,
             'url': reverse('site360:project_detail', kwargs={'pk': p.pk}),
             'description': p.description[:50] + '...' if p.description else '',
             'stats': {
                 'text': p.text_count,
                 'image': p.image_count,
                 'video': p.video_count
             }
        })
    return JsonResponse({'projects': data})

class ProjectDetailView(UserActionLoggingMixin, DetailView):
    model = Project
    template_name = 'site360/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Aggregate hotspot counts per scene
        from django.db.models import Count, Q
        scenes = project.scenes.annotate(
            text_count=Count('hotspots', filter=Q(hotspots__hotspot_type__in=['text', 'text_hover'])),
            image_count=Count('hotspots', filter=Q(hotspots__hotspot_type__in=['image', 'image_hover'])),
            video_count=Count('hotspots', filter=Q(hotspots__hotspot_type__in=['video', 'video_hover']))
        ).order_by('order')
        
        context['scenes'] = scenes
        return context

class SceneCreateView(UserActionLoggingMixin, CreateView):
    model = Scene
    form_class = SceneForm
    template_name = 'site360/scene_form.html'
    
    def post(self, request, *args, **kwargs):
        upload_mode = request.POST.get('upload_mode', 'single')
        
        # Handle batch upload separately to avoid form validation issues
        if upload_mode == 'batch':
            return self.handle_batch_upload(request)
        
        # For single upload, use the standard form processing
        return super().post(request, *args, **kwargs)
    
    def handle_batch_upload(self, request):
        """Handle batch upload with default values"""
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        images = request.FILES.getlist('batch_images')
        
        if not images:
            # Return to form with error
            form = self.get_form()
            form.add_error(None, '請至少選擇一張照片進行批量上傳')
            return self.form_invalid(form)
        
        # Auto-calculate starting order
        max_order = project.scenes.aggregate(Max('order'))['order__max']
        starting_order = (max_order or 0) + 1
        
        # Create scenes with default values
        for index, image_file in enumerate(images):
            scene = Scene(
                project=project,
                title=f"場景 {index + 1}",
                image=image_file,
                pitch=0,
                yaw=0,
                hfov=100,
                order=starting_order + index
            )
            scene.save()
        
        # Redirect to project detail
        return redirect(self.get_success_url())

    def form_valid(self, form):
        """Handle single upload with custom values"""
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        
        # Auto-calculate order
        max_order = project.scenes.aggregate(Max('order'))['order__max']
        form.instance.project = project
        form.instance.order = (max_order or 0) + 1
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse('site360:project_detail', kwargs={'pk': self.kwargs['pk']})




@csrf_exempt
@user_action_logging
def move_hotspot(request, pk):
    if request.method == 'POST':
        try:
            hotspot = get_object_or_404(Hotspot, pk=pk)
            hotspot.pitch = float(request.POST.get('pitch'))
            hotspot.yaw = float(request.POST.get('yaw'))
            hotspot.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

@csrf_exempt
@user_action_logging
def delete_hotspot(request, pk):
    if request.method == 'POST':
        try:
            hotspot = Hotspot.objects.get(pk=pk)
            hotspot.delete()
            return JsonResponse({'status': 'success'})
        except Hotspot.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Hotspot not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@user_action_logging
def update_scene_nav(request, pk):
    """
    Updates the position or icon of the Next or Prev navigation hotspot for a scene.
    pk: Scene ID
    POST data: nav_type ('next' or 'prev'), pitch, yaw, icon (optional)
    """
    if request.method == 'POST':
        try:
            scene = get_object_or_404(Scene, pk=pk)
            nav_type = request.POST.get('nav_type') # 'next' or 'prev'
            pitch = request.POST.get('pitch')
            yaw = request.POST.get('yaw')
            icon = request.POST.get('icon')  # optional
            
            if nav_type == 'next':
                if pitch is not None: scene.next_pitch = float(pitch)
                if yaw is not None: scene.next_yaw = float(yaw)
                if icon: scene.next_icon = icon
            elif nav_type == 'prev':
                if pitch is not None: scene.prev_pitch = float(pitch)
                if yaw is not None: scene.prev_yaw = float(yaw)
                if icon: scene.prev_icon = icon
            else:
                 return JsonResponse({'status': 'error', 'message': 'Invalid nav_type'}, status=400)
            
            scene.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@user_action_logging
def save_hotspot(request):
    if request.method == 'POST':
        try:
            scene_id = request.POST.get('scene_id')
            hotspot_id = request.POST.get('hotspot_id')
            hotspot_type = request.POST.get('type')
            pitch = request.POST.get('pitch')
            yaw = request.POST.get('yaw')
            title = request.POST.get('title')
            description = request.POST.get('description')
            icon = request.POST.get('icon')
            icon_color = request.POST.get('icon_color')
            
            hazard_types_vals = request.POST.getlist('hazard_types')
            hazard_types_ids = [int(val) for val in hazard_types_vals if val]
            
            # Import Logic
            copy_from_id = request.POST.get('copy_from_id')
            clear_source = request.POST.get('clear_source')  # 檢查是否明確要求清除引用
            source_hotspot = None

            if copy_from_id:
                try:
                    source_hotspot = Hotspot.objects.get(pk=copy_from_id)
                except Hotspot.DoesNotExist:
                    source_hotspot = None # Gracefully handle missing source

            scene = Scene.objects.get(pk=scene_id)
            
            if hotspot_id:
                # Update existing
                try:
                    hotspot = Hotspot.objects.get(pk=hotspot_id)
                except Hotspot.DoesNotExist:
                     return JsonResponse({'status': 'error', 'message': f'Target hotspot {hotspot_id} not found.'}, status=404)

                hotspot.hotspot_type = hotspot_type
                hotspot.pitch = float(pitch)
                hotspot.yaw = float(yaw)
                hotspot.title = title
                hotspot.description = description
                hotspot.icon = icon
                hotspot.icon_color = icon_color
                # hotspot.hazard_type_id = hazard_type_id # Legacy field
                hotspot.save() # Save first before setting M2M
                hotspot.hazard_types.set(hazard_types_ids)
                
                # 處理清除引用的請求
                if clear_source == 'true':
                    hotspot.source_hotspot = None
            else:
                # Create new
                hotspot = Hotspot(
                    scene=scene,
                    hotspot_type=hotspot_type,
                    pitch=float(pitch),
                    yaw=float(yaw),
                    title=title,
                    description=description,
                    icon=icon,
                )
                hotspot.save()
                hotspot.hazard_types.set(hazard_types_ids)

            # Handle Import (Copy/Reference fields)
            if source_hotspot:
                hotspot.source_hotspot = source_hotspot
                
                # Copy Image if no new file provided
                if source_hotspot.image and not request.FILES.get('image') and not request.FILES.get('video'):
                    hotspot.image = source_hotspot.image
                    # 引用圖片資源時，清除影片字段以確保互斥
                    hotspot.video = None
                
                # Copy Video if no new file provided
                if source_hotspot.video and not request.FILES.get('video') and not request.FILES.get('image'):
                    hotspot.video = source_hotspot.video
                    # 引用影片資源時，清除圖片字段以確保互斥
                    hotspot.image = None
            
            # Handle File Uploads (Overrides imported files)
            # 圖片和影片互斥：上傳圖片時清除影片，上傳影片時清除圖片
            if 'image' in request.FILES:
                hotspot.image = request.FILES['image']
                # 清除影片字段，確保不併存
                hotspot.video = None
            
            if 'video' in request.FILES:
                hotspot.video = request.FILES['video']
                # 清除圖片字段，確保不併存
                hotspot.image = None
            
            # 根據熱點類型清理不需要的媒體文件
            if hotspot_type in ['text', 'text_hover']:
                # 文字類型不需要圖片和影片
                hotspot.image = None
                hotspot.video = None
            elif hotspot_type in ['image', 'image_hover']:
                # 圖片類型不需要影片
                hotspot.video = None
            elif hotspot_type in ['video', 'video_hover']:
                # 影片類型不需要圖片
                hotspot.image = None
                
            hotspot.save()
            
            return JsonResponse({'status': 'success', 'id': hotspot.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def list_resources(request):
    """
    API to list all available resources (hotspots) for the library with pagination and filtering.
    """
    from django.db.models import Q
    from django.core.paginator import Paginator

    try:
        page_number = request.GET.get('page', 1)
        search = request.GET.get('search', '').lower()
        ht_type = request.GET.get('type', '')
        project_name = request.GET.get('project', '')
        form_uid = request.GET.get('form_uid', '')
        is_recommend = request.GET.get('recommend', 'true').lower() == 'true'

        # Base queryset
        queryset = Hotspot.objects.select_related('scene', 'scene__project', 'project').all().order_by('-created_at')

        # Filtering
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        if ht_type:
            if ht_type == 'text':
                queryset = queryset.filter(hotspot_type__in=['text', 'text_hover'])
            elif ht_type == 'image':
                queryset = queryset.filter(hotspot_type__in=['image', 'image_hover'])
            elif ht_type == 'video':
                queryset = queryset.filter(hotspot_type__in=['video', 'video_hover'])
            else:
                queryset = queryset.filter(hotspot_type=ht_type)
        
        if project_name:
            if project_name == '__none__':
                queryset = queryset.filter(scene__isnull=True, project__isnull=True)
            else:
                queryset = queryset.filter(Q(scene__project__name=project_name) | Q(project__name=project_name))
        
        if form_uid:
            if is_recommend:
                queryset = queryset.filter(external_form_uid=form_uid)
            else:
                queryset = queryset.exclude(external_form_uid=form_uid)

        # Pagination
        paginator = Paginator(queryset, 15) # 15 items per page
        page_obj = paginator.get_page(page_number)

        data = []
        for h in page_obj:
            item = {
                'id': h.id,
                'title': h.title,
                'description': h.description,
                'type': h.hotspot_type,
                'type_display': h.get_hotspot_type_display(),
                'project_name': h.project.name if h.project else (h.scene.project.name if h.scene else '（未分配）'),
                'scene_title': h.scene.title if h.scene else '（未分配至場景）',
                'is_unassigned': h.scene is None,
                'is_external_card': h.scene is None and h.project is not None,
                'thumb_url': f"{h.image.url}?v={int(h.updated_at.timestamp())}" if h.image and h.hotspot_type in ['image', 'image_hover'] else None,
                'video_url': f"{h.video.url}?v={int(h.updated_at.timestamp())}" if h.video else None,
                'has_video': bool(h.video),
                'icon': h.icon,
                'icon_color': h.icon_color,
                'usage_count': h.copied_by.count(),
                'hazard_types': [ht.id for ht in h.hazard_types.all()],
                'external_form_uid': h.external_form_uid
            }
            data.append(item)
            
        return JsonResponse({
            'status': 'success', 
            'resources': data,
            'has_next': page_obj.has_next(),
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@user_action_logging
def create_standalone_hotspot(request):
    """
    Creates a standalone hotspot (not tied to any scene) for the resource library.
    """
    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            if not title:
                return JsonResponse({'status': 'error', 'message': '標題不能為空'}, status=400)

            hotspot_type = request.POST.get('type', 'text')
            description = request.POST.get('description', '')
            icon = request.POST.get('icon', 'fas fa-info-circle')
            icon_color = request.POST.get('icon_color', '#ffffff')
            hazard_types_ids = request.POST.getlist('hazard_types')
            hazard_types_ids = [int(val) for val in hazard_types_ids if val]

            hotspot = Hotspot(
                scene=None,
                hotspot_type=hotspot_type,
                pitch=0.0,
                yaw=0.0,
                title=title,
                description=description,
                icon_color=icon_color,
            )

            if 'image' in request.FILES:
                hotspot.image = request.FILES['image']
            if 'video' in request.FILES:
                hotspot.video = request.FILES['video']

            # Enforce media exclusivity based on type
            if hotspot_type in ['text', 'text_hover']:
                hotspot.image = None
                hotspot.video = None
            elif hotspot_type in ['image', 'image_hover']:
                hotspot.video = None
            elif hotspot_type in ['video', 'video_hover']:
                hotspot.image = None

            hotspot.save()
            hotspot.hazard_types.set(hazard_types_ids)
            return JsonResponse({'status': 'success', 'id': hotspot.id, 'message': '素材已成功建立'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
@user_action_logging
def reorder_scenes(request):
    if request.method == 'POST':
        try:
            # Expecting scene_ids[] in POST data
            scene_ids = request.POST.getlist('scene_ids[]')
            if not scene_ids:
                return JsonResponse({'status': 'error', 'message': 'No IDs provided'}, status=400)
            
            # Loop through IDs and update order
            for index, scene_id in enumerate(scene_ids):
                # Update each scene's order. 
                # Note: This executes one query per scene. For large lists, bulk_update is better.
                # Given < 100 scenes typically, this is acceptable for now.
                Scene.objects.filter(id=scene_id).update(order=index)
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

@csrf_exempt
@user_action_logging
def set_cover_image(request, pk):
    if request.method == 'POST':
        try:
            scene = get_object_or_404(Scene, pk=pk)
            project = scene.project
            
            # We need to copy the scene image to the project cover_image
            # Or simplified: just reference it if fields were compatible, but they are different ImageFields
            # Actually, we can just open the scene image and save it to cover_image
            from django.core.files import File
            
            if scene.image:
                # Create a copy/reference. Since they are both ImageFields, we can assign the file.
                # But to avoid moving the file, we should probably just re-save it or use the same path if media storage allows.
                # Simplest way: set the file directly.
                project.cover_image = scene.image
                project.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Scene has no image'}, status=400)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

@csrf_exempt
@user_action_logging
def delete_scene(request, pk):
    """Delete a scene and all its associated hotspots"""
    if request.method == 'POST':
        try:
            scene = get_object_or_404(Scene, pk=pk)
            scene_title = scene.title
            
            # Delete the scene (cascade will handle hotspots)
            scene.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'場景「{scene_title}」已成功刪除'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def serve_hotspot_video(request, pk):
    """
    Serves hotspot video with HTTP Range support for seeking (critical for Dev Server).
    """
    hotspot = get_object_or_404(Hotspot, pk=pk)
    if not hotspot.video:
        return JsonResponse({"error": "No video for this hotspot"}, status=404)
    
    file_path = hotspot.video.path
    if not os.path.exists(file_path):
        return JsonResponse({"error": "Video file not found"}, status=404)
        
    file_size = os.path.getsize(file_path)
    
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else file_size - 1
        if last_byte >= file_size:
            last_byte = file_size - 1
        length = last_byte - first_byte + 1
        
        def file_iterator(path, offset, length, chunk_size=8192):
            with open(path, 'rb') as f:
                f.seek(offset)
                remaining = length
                while remaining > 0:
                    read_size = min(chunk_size, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    yield data
                    remaining -= len(data)

        response = StreamingHttpResponse(file_iterator(file_path, first_byte, length), status=206, content_type='video/mp4')
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(length)
    else:
        # Full content
        def file_iterator(path, chunk_size=8192):
            with open(path, 'rb') as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data

        response = StreamingHttpResponse(file_iterator(file_path), content_type='video/mp4')
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
    
    return response

    return response

def project_resource_list(request, pk):
    """
    Displays a list of all resources (hotspots), optionally defaults to the specified project.
    """
    from django.db.models import Prefetch, Count
    from .models import HazardType

    project = get_object_or_404(Project, pk=pk)

    scenes = Scene.objects.all().order_by('project', 'order').prefetch_related(
        'project',
        Prefetch('hotspots', queryset=Hotspot.objects.annotate(usage_count=Count('copied_by')).select_related('source_hotspot', 'project').prefetch_related('hazard_types').order_by('created_at'))
    )

    all_projects = Project.objects.all().order_by('name')
    hazard_types = HazardType.objects.all().order_by('serial_number')

    # Unassigned hotspots: scene is null
    unassigned_hotspots = Hotspot.objects.filter(scene__isnull=True).annotate(
        usage_count=Count('copied_by')
    ).select_related('source_hotspot', 'project').prefetch_related('hazard_types').order_by('-created_at')

    context = {
        'project': project,
        'all_projects': all_projects,
        'scenes': scenes,
        'hazard_types': hazard_types,
        'unassigned_hotspots': unassigned_hotspots,
    }
    return render(request, 'site360/resource_list.html', context)

def all_resource_list(request):
    """
    Displays a list of all resources (hotspots) across all projects.
    Also includes standalone hotspots that have no scene.
    """
    from django.db.models import Prefetch
    from .models import HazardType

    scenes = Scene.objects.all().order_by('project', 'order').prefetch_related(
        'project',
        Prefetch('hotspots', queryset=Hotspot.objects.annotate(usage_count=Count('copied_by')).select_related('source_hotspot', 'project').prefetch_related('hazard_types').order_by('created_at'))
    )

    projects = Project.objects.all().order_by('name')
    hazard_types = HazardType.objects.all().order_by('serial_number')

    # Unassigned hotspots: scene is null
    unassigned_hotspots = Hotspot.objects.filter(scene__isnull=True).annotate(
        usage_count=Count('copied_by')
    ).select_related('source_hotspot', 'project').prefetch_related('hazard_types').order_by('-created_at')

    context = {
        'scenes': scenes,
        'all_projects': projects,
        'unassigned_hotspots': unassigned_hotspots,
        'hazard_types': hazard_types,
    }
    return render(request, 'site360/resource_list.html', context)

def project_tour_data(request, pk):
    """
    Returns the JSON configuration for Pannellum tour.
    """
    project = get_object_or_404(Project, pk=pk)
    scenes = project.scenes.all().order_by('order')
    
    if not scenes.exists():
        return JsonResponse({"error": "No scenes found"}, status=404)

    target_scene_id = request.GET.get('scene_id')
    if target_scene_id and scenes.filter(id=target_scene_id).exists():
        first_scene_id = target_scene_id
    else:
        # Fallback to the first scene in the order
        first_scene = scenes.first()
        first_scene_id = str(first_scene.id)
    
    tour_config = {
        "default": {
            "firstScene": first_scene_id,
            "sceneFadeDuration": 1000,
            "autoLoad": True,
            "compass": True,
        },
        "scenes": {}
    }

    # Build scene dictionary
    for i, scene in enumerate(scenes):
        scene_id = str(scene.id)
        next_scene = scenes[i+1] if i + 1 < len(scenes) else None
        prev_scene = scenes[i-1] if i > 0 else None
        
        hotspots = []
        
        # Navigation Hotspots
        if next_scene:
            hotspots.append({
                "pitch": scene.next_pitch,
                "yaw": scene.next_yaw,
                "type": "scene",
                "text": f"Next: {next_scene.title}",
                "sceneId": str(next_scene.id),
                "id": f"nav_next_{scene.id}",
                "createTooltipFunc": "hotspotTooltip",
                "createTooltipArgs": { 
                    "type": "scene", 
                    "id": f"nav_next_{scene.id}",
                    "nav_type": "next",
                    "scene_id": str(scene.id),
                    "sceneId": str(next_scene.id),
                    "icon": scene.next_icon or "fas fa-arrow-right",
                    "icon_color": "#00d2ff",
                    "title": f"下一個場景：{next_scene.title}"
                }
            })
        if prev_scene:
            hotspots.append({
                "pitch": scene.prev_pitch,
                "yaw": scene.prev_yaw,
                "type": "scene",
                "text": f"Prev: {prev_scene.title}",
                "sceneId": str(prev_scene.id),
                "id": f"nav_prev_{scene.id}",
                "createTooltipFunc": "hotspotTooltip",
                "createTooltipArgs": { 
                    "type": "scene", 
                    "id": f"nav_prev_{scene.id}",
                    "nav_type": "prev",
                    "scene_id": str(scene.id),
                    "sceneId": str(prev_scene.id),
                    "icon": scene.prev_icon or "fas fa-arrow-left",
                    "icon_color": "#00d2ff",
                    "title": f"上一個場景：{prev_scene.title}"
                }
            })

        # Rich Media Hotspots
        for hs in scene.hotspots.all():
            hs_data = {
                "id": hs.id,
                "pitch": hs.pitch,
                "yaw": hs.yaw,
                "type": "info", # Use generic info type, we will customize icon via createTooltipFunc
                "text": hs.title,
                # Custom data for our frontend handler
                "createTooltipFunc": "hotspotTooltip", 
                "createTooltipArgs": {
                    "id": hs.id,
                    "type": hs.hotspot_type,
                    "title": hs.title,
                    "description": hs.description,
                    "icon": hs.icon, 
                    "icon_color": hs.icon_color,
                    "image": f"{hs.image.url}?v={int(hs.updated_at.timestamp())}" if hs.image else "",
                    "video": f"{reverse('site360:serve_hotspot_video', kwargs={'pk': hs.id})}?v={int(hs.updated_at.timestamp())}" if hs.video else "",
                    "video_raw": hs.video.url if hs.video else "", # Raw URL for comparison checks
                    "source_hotspot_id": hs.source_hotspot.id if hs.source_hotspot else None,
                    "source_hotspot_title": hs.source_hotspot.title if hs.source_hotspot else None,
                    "hazard_types": [
                        {"id": ht.id, "name_with_serial": f"{ht.serial_number}. {ht.name}"}
                        for ht in hs.hazard_types.all()
                    ],
                }
            }
            hotspots.append(hs_data)

        tour_config["scenes"][scene_id] = {
            "title": scene.title,
            "hfov": scene.hfov,
            "pitch": scene.pitch,
            "yaw": scene.yaw,
            "type": "equirectangular",
            "panorama": scene.image.url,
            "hotSpots": hotspots
        }

    return JsonResponse(tour_config)

def tour_view(request, pk):
    from .models import HazardType
    projet = get_object_or_404(Project, pk=pk)
    hazard_types = HazardType.objects.all().order_by('serial_number')
    return render(request, 'site360/tour.html', {'project': projet, 'hazard_types': hazard_types})

@csrf_exempt
@user_action_logging
def edit_resource(request, pk):
    """
    Edit a resource (hotspot). If the resource is referenced (usage_count > 0),
    create a new version instead of modifying the original.
    """
    if request.method == 'POST':
        try:
            hotspot = get_object_or_404(Hotspot, pk=pk)
            usage_count = hotspot.copied_by.count()
            
            # Get form data
            title = request.POST.get('title')
            description = request.POST.get('description')
            hotspot_type = request.POST.get('type')
            hazard_types_ids = request.POST.getlist('hazard_types')
            hazard_types_ids = [int(val) for val in hazard_types_ids if val]

            # Always update directly - no version creation in basic edit
            hotspot.title = title
            hotspot.description = description
            hotspot.hotspot_type = hotspot_type
            # hotspot.hazard_type_id = hazard_type_id # Legacy field
            
            # Check if this is a referencing hotspot
            if hotspot.source_hotspot:
                # If referencing, do NOT allow changing media files
                if 'image' in request.FILES or 'video' in request.FILES:
                    return JsonResponse({
                        'status': 'error', 
                        'message': '此為引用資源，無法修改媒體內容。請編輯原始資源。'
                    }, status=400)
                
                # If referencing, do NOT allow changing media type category
                # Determine current media category
                current_has_image = bool(hotspot.image)
                current_has_video = bool(hotspot.video)
                
                # Determine new media category from type
                new_is_image_type = hotspot_type in ['image', 'image_hover']
                new_is_video_type = hotspot_type in ['video', 'video_hover']
                new_is_text_type = hotspot_type in ['text', 'text_hover']
                
                # Validate that the type change stays within the same media category
                if current_has_image and not new_is_image_type:
                    return JsonResponse({
                        'status': 'error', 
                        'message': '此為引用圖片資源，只能在「圖片」和「懸浮圖片」之間切換類型。'
                    }, status=400)
                elif current_has_video and not new_is_video_type:
                    return JsonResponse({
                        'status': 'error', 
                        'message': '此為引用影片資源，只能在「影片」和「懸浮影片」之間切換類型。'
                    }, status=400)
                elif not current_has_image and not current_has_video and not new_is_text_type:
                    return JsonResponse({
                        'status': 'error', 
                        'message': '此為引用文字資源，只能在「文字」和「懸浮文字」之間切換類型。'
                    }, status=400)
            
            # Handle media files
            if 'image' in request.FILES:
                hotspot.image = request.FILES['image']
                hotspot.video = None
            elif 'video' in request.FILES:
                hotspot.video = request.FILES['video']
                hotspot.image = None
            
            # Clean up media based on type
            if hotspot_type in ['text', 'text_hover']:
                hotspot.image = None
                hotspot.video = None
            elif hotspot_type in ['image', 'image_hover']:
                hotspot.video = None
            elif hotspot_type in ['video', 'video_hover']:
                hotspot.image = None
            
            hotspot.save()
            hotspot.hazard_types.set(hazard_types_ids)
            
            return JsonResponse({
                'status': 'success',
                'message': '資源已更新',
                'new_version': False,
                'id': hotspot.id
            })
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def check_resource_updates(request):
    """
    Check for resources that have newer versions available.
    Returns a list of hotspots that reference outdated versions.
    """
    try:
        # Find all hotspots that have source_hotspot and where the source is not the latest version
        outdated_references = []
        
        hotspots_with_source = Hotspot.objects.filter(source_hotspot__isnull=False).select_related('source_hotspot', 'source_hotspot__original_resource')
        
        for hotspot in hotspots_with_source:
            source = hotspot.source_hotspot
            
            # Check if source is not the latest version
            if not source.is_latest_version:
                # Find the latest version
                if source.original_resource:
                    # Source is a version, find latest from original
                    latest_version = Hotspot.objects.filter(
                        original_resource=source.original_resource,
                        is_latest_version=True
                    ).first()
                else:
                    # Source is original, find latest version
                    latest_version = Hotspot.objects.filter(
                        original_resource=source,
                        is_latest_version=True
                    ).first()
                
                if latest_version:
                    outdated_references.append({
                        'hotspot_id': hotspot.id,
                        'hotspot_title': hotspot.title,
                        'scene_title': hotspot.scene.title,
                        'current_version': source.version_number,
                        'latest_version': latest_version.version_number,
                        'latest_version_id': latest_version.id,
                        'latest_title': latest_version.title
                    })
        
        return JsonResponse({
            'status': 'success',
            'outdated_count': len(outdated_references),
            'outdated_references': outdated_references
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def update_resource_reference(request, pk):
    """
    Update a single hotspot to reference the latest version of its source.
    """
    if request.method == 'POST':
        try:
            hotspot = get_object_or_404(Hotspot, pk=pk)
            
            if not hotspot.source_hotspot:
                return JsonResponse({'status': 'error', 'message': 'This hotspot has no source reference'}, status=400)
            
            source = hotspot.source_hotspot
            
            # Directly use the source hotspot (no version control needed anymore)
            # Update the hotspot with source data
            hotspot.title = source.title
            hotspot.description = source.description
            hotspot.hotspot_type = source.hotspot_type
            try:
                hotspot.image = source.image
            except Exception as img_err:
                print(f"Error copying image for hotspot {pk}: {img_err}")
                
            try:
                hotspot.video = source.video
            except Exception as vid_err:
                print(f"Error copying video for hotspot {pk}: {vid_err}")
            hotspot.icon = source.icon
            hotspot.icon_color = source.icon_color
            hotspot.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'已更新引用內容',
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def batch_update_references(request):
    """
    Batch update multiple hotspots to their latest versions.
    """
    if request.method == 'POST':
        try:
            import json
            hotspot_ids = json.loads(request.POST.get('hotspot_ids', '[]'))
            
            if not hotspot_ids:
                return JsonResponse({'status': 'error', 'message': 'No hotspot IDs provided'}, status=400)
            
            updated_count = 0
            errors = []
            
            for hotspot_id in hotspot_ids:
                try:
                    hotspot = Hotspot.objects.get(pk=hotspot_id)
                    
                    if not hotspot.source_hotspot:
                        continue
                    
                    source = hotspot.source_hotspot
                    
                    # Find the latest version
                    if source.original_resource:
                        latest_version = Hotspot.objects.filter(
                            original_resource=source.original_resource,
                            is_latest_version=True
                        ).first()
                    else:
                        latest_version = Hotspot.objects.filter(
                            original_resource=source,
                            is_latest_version=True
                        ).first()
                    
                    if latest_version:
                        # Update the hotspot
                        hotspot.source_hotspot = latest_version
                        hotspot.title = latest_version.title
                        hotspot.description = latest_version.description
                        hotspot.hotspot_type = latest_version.hotspot_type
                        hotspot.image = latest_version.image
                        hotspot.video = latest_version.video
                        hotspot.icon = latest_version.icon
                        hotspot.icon_color = latest_version.icon_color
                        hotspot.save()
                        updated_count += 1
                        
                except Hotspot.DoesNotExist:
                    errors.append(f'Hotspot {hotspot_id} not found')
                except Exception as e:
                    errors.append(f'Error updating hotspot {hotspot_id}: {str(e)}')
            
            return JsonResponse({
                'status': 'success',
                'updated_count': updated_count,
                'errors': errors
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def get_resource_references(request, pk):
    """
    Get detailed information about all hotspots that reference this resource.
    Shows which projects/scenes use it and whether they have outdated versions.
    """
    try:
        resource = get_object_or_404(Hotspot, pk=pk)
        
        # Get all hotspots that reference this resource (via source_hotspot)
        references = Hotspot.objects.filter(source_hotspot=resource).select_related('scene', 'scene__project', 'project')
        
        # Build reference details
        reference_list = []
        for ref in references:
            # Check if this reference is outdated by comparing content
            # A reference is "outdated" if its content differs from the source
            is_outdated = (
                ref.title != resource.title or
                ref.description != resource.description or
                ref.hotspot_type != resource.hotspot_type or
                ref.image != resource.image or
                ref.video != resource.video
            )
            
            reference_list.append({
                'id': ref.id,
                'project_name': ref.project.name if ref.project else (ref.scene.project.name if ref.scene else '（未分配）'),
                'scene_title': ref.scene.title if ref.scene else '（未分配至場景）',
                'scene_id': ref.scene.id if ref.scene else None,
                'hotspot_title': ref.title,
                'hotspot_type': ref.hotspot_type,
                'hotspot_type_display': ref.get_hotspot_type_display(),
                'hotspot_description': ref.description,  # The reference's description (may be modified)
                'source_title': resource.title,  # The original resource's title
                'source_type': resource.hotspot_type,  # The original resource's type
                'source_type_display': resource.get_hotspot_type_display(),  # The original resource's type display
                'source_description': resource.description,  # The original resource's description
                'title_modified': ref.title != resource.title,  # Flag if titles differ
                'type_modified': ref.hotspot_type != resource.hotspot_type,  # Flag if types differ
                'description_modified': ref.description != resource.description,  # Flag if descriptions differ
                'is_outdated': is_outdated,
                'current_version': resource.version_number,
                'latest_version': resource.version_number,
                'latest_version_id': resource.id
            })
        
        return JsonResponse({
            'status': 'success',
            'resource_id': resource.id,
            'resource_title': resource.title,
            'resource_version': resource.version_number,
            'is_latest': True,  # Always latest since no version control
            'reference_count': len(reference_list),
            'references': reference_list,
            'has_newer_version': False,  # Never has newer version
            'latest_version_id': resource.id
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def hotspot_data(request, pk):
    """
    Get hotspot data for comparison purposes in tour edit modal.
    """
    try:
        hotspot = get_object_or_404(Hotspot, pk=pk)
        return JsonResponse({
            'status': 'success',
            'hotspot': {
                'id': hotspot.id,
                'title': hotspot.title,
                'description': hotspot.description,
                'hotspot_type': hotspot.hotspot_type,
                'image': hotspot.image.url if hotspot.image else None,
                'video': hotspot.video.url if hotspot.video else None,
                'icon': hotspot.icon,
                'icon_color': hotspot.icon_color,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class UserActivityLogListView(ListView):
    """
    使用者操作記錄列表視圖
    提供篩選、搜尋、分頁功能
    """
    model = UserActionLog
    template_name = 'site360/user_activity_logs.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = UserActionLog.objects.select_related('user', 'content_type').all()
        
        # 篩選：操作類型
        action_type = self.request.GET.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # 篩選：使用者
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 篩選：對象類型
        content_type_id = self.request.GET.get('content_type')
        if content_type_id:
            queryset = queryset.filter(content_type_id=content_type_id)
        
        # 篩選：日期範圍
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            from datetime import datetime, timedelta
            # Add one day to include the entire end date
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=date_to_obj)
        
        # 搜尋
        search = self.request.GET.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(object_repr__icontains=search) |
                Q(request_path__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 提供篩選選項
        from django.contrib.auth.models import User
        from django.contrib.contenttypes.models import ContentType
        
        context['all_users'] = User.objects.all().order_by('username')
        context['action_types'] = UserActionLog.ACTION_TYPE_CHOICES
        context['content_types'] = ContentType.objects.filter(
            id__in=UserActionLog.objects.values_list('content_type_id', flat=True).distinct()
        ).order_by('model')
        
        # 保留當前篩選條件
        context['current_action_type'] = self.request.GET.get('action_type', '')
        context['current_user'] = self.request.GET.get('user', '')
        context['current_content_type'] = self.request.GET.get('content_type', '')
        context['current_date_from'] = self.request.GET.get('date_from', '')
        context['current_date_to'] = self.request.GET.get('date_to', '')
        context['current_search'] = self.request.GET.get('search', '')
        
        # 操作類型顏色映射（與 admin 一致）
        context['action_colors'] = {
            'CREATE': '#28a745',
            'UPDATE': '#ffc107',
            'DELETE': '#dc3545',
            'VIEW': '#17a2b8',
            'LOGIN': '#6610f2',
            'LOGOUT': '#6c757d',
            'UPLOAD': '#007bff',
            'DOWNLOAD': '#20c997',
            'REFERENCE': '#fd7e14',
            'REORDER': '#e83e8c',
            'MOVE': '#6f42c1',
            'SET_COVER': '#17a2b8',
            'OTHER': '#6c757d',
        }
        
        return context

import requests
import logging
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from site360.services.third_party_sync import SinoTechAPIParser, cms_api_get

logger = logging.getLogger(__name__)

def integrate_from_cms(request):
    """
    接收外部平台（PMIS）轉跳，自動拉取表單資料並建立 360 專案。

    流程：
    1. 從 GET 參數取得 form_uid
    2. 使用兩段式 Middleware Auth 呼叫 CMS API 取得 JSON 資料
    3. 呼叫 SinoTechAPIParser 解析並建立 Project / Scene / Hotspot
    4. Redirect 使用者到該專案的 360 Tour 頁面

    預期 GET 參數：
        form_uid (str): CMS 平台的表單唯一識別碼
    """
    form_uid = request.GET.get('form_uid')
    if not form_uid:
        return JsonResponse({"success": False, "error": "缺少必要參數 form_uid"}, status=400)

    base_url = "https://cmservice.sinotech.com.tw"
    api_url  = f"{base_url}/HN/api/form-basic/{form_uid}/"

    try:
        # Step 1：使用兩段式 Middleware Auth 向 CMS 取得 JSON 資料
        logger.info(f"[CMS Integrate] 開始處理 form_uid={form_uid}")
        response, cookie_header = cms_api_get(api_url)

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            logger.error(f"[CMS Integrate] CMS 回傳非 JSON 內容：{content_type}")
            return JsonResponse({
                "success": False,
                "error": f"CMS API 回傳非 JSON 格式（Content-Type: {content_type}），請確認認證設定"
            }, status=502)

        json_resp = response.json()

        if not json_resp.get("success"):
            logger.error(f"[CMS Integrate] CMS API 回傳失敗：{json_resp}")
            return JsonResponse({"success": False, "error": "CMS API 回傳 success=false"}, status=502)

        data = json_resp.get("data", {})

        # Step 2：解析資料並建立 Project / Scene / Hotspot
        # 傳入 cookie_header 讓圖片下載可重用同一 Session，不需再次登入
        parser  = SinoTechAPIParser(data=data, base_url=base_url, session_cookie=cookie_header)
        project = parser.process()

        logger.info(f"[CMS Integrate] 完成！Project pk={project.pk}，Redirect 至 Project 詳情頁")

        # Step 3：成功後將使用者 Redirect 到 360 專案詳情頁面
        return HttpResponseRedirect(reverse('site360:project_detail', kwargs={'pk': project.pk}))

    except Exception as e:
        logger.error(f"[CMS Integrate] 失敗：{e}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)}, status=500)
