from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Max, Count
from django.db import models
from .forms import ProjectForm, SceneForm
from .models import Project, Scene, Hotspot
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
import os
import re
import json
from django.conf import settings

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

class ProjectListView(ListView):
    model = Project
    template_name = 'site360/project_list.html'
    context_object_name = 'projects'

class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'site360/project_form.html'
    success_url = reverse_lazy('site360:project_list')

class ProjectUpdateView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'site360/project_form.html'
    
    def get_success_url(self):
        return reverse_lazy('site360:project_detail', kwargs={'pk': self.object.pk})

class ProjectMapView(TemplateView):
    template_name = 'site360/project_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Count
        from .models import Project
        
        # Aggregate projects by city
        # Exclude empty city strings if any
        city_stats = Project.objects.exclude(city='').values('city').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context['city_stats'] = city_stats
        return context

def project_map_data(request):
    """API: 回傳所有專案的地圖資料，包含熱點統計"""
    from django.db.models import Count, Q
    
    projects = Project.objects.filter(latitude__isnull=False, longitude__isnull=False).annotate(
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

class ProjectDetailView(DetailView):
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

class SceneCreateView(CreateView):
    model = Scene
    form_class = SceneForm
    template_name = 'site360/scene_form.html'

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        form.instance.project = project
        
        # Auto-calculate order
        max_order = project.scenes.aggregate(Max('order'))['order__max']
        form.instance.order = (max_order or 0) + 1
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse('site360:project_detail', kwargs={'pk': self.kwargs['pk']})


@csrf_exempt
def save_hotspot(request):
    if request.method == 'POST':
        try:
            hotspot_id = request.POST.get('hotspot_id')
            scene_id = request.POST.get('scene_id')
            hotspot_type = request.POST.get('type')
            pitch = request.POST.get('pitch')
            yaw = request.POST.get('yaw')
            title = request.POST.get('title')
            description = request.POST.get('description')
            icon = request.POST.get('icon', 'fas fa-info-circle')
            icon_color = request.POST.get('icon_color', '#ffffff')
            
            if hotspot_id:
                # Update existing
                hotspot = get_object_or_404(Hotspot, id=hotspot_id)
                hotspot.hotspot_type = hotspot_type
                hotspot.title = title
                hotspot.description = description
                hotspot.icon = icon
                hotspot.icon_color = icon_color
                # Only update pitch/yaw if provided (though usually they are hidden fields)
                if pitch: hotspot.pitch = float(pitch)
                if yaw: hotspot.yaw = float(yaw)
            else:
                # Create new
                scene = get_object_or_404(Scene, id=scene_id)

                if not icon_color: icon_color = '#ffffff'
                
                hotspot = Hotspot(
                    scene=scene,
                    hotspot_type=hotspot_type,
                    pitch=float(pitch),
                    yaw=float(yaw),
                    title=title,
                    description=description,
                    icon=icon,
                    icon_color=icon_color
                )
            
            # Handle source reference (copy_from_id from frontend)
            copy_from_id = request.POST.get('copy_from_id')
            clear_source = request.POST.get('clear_source')
            
            if clear_source == 'true':
                # Explicitly clear the relationship
                hotspot.source_hotspot = None
                hotspot.original_resource = None
            elif copy_from_id:
                try:
                    source_hotspot = Hotspot.objects.get(id=copy_from_id)
                    hotspot.source_hotspot = source_hotspot
                    # Inherit original_resource if source has one, otherwise source IS the original
                    hotspot.original_resource = source_hotspot.original_resource if source_hotspot.original_resource else source_hotspot
                except Hotspot.DoesNotExist:
                     # If source not found, we return error as this shouldn't happen in normal flow
                    return JsonResponse({'status': 'error', 'message': f'Target hotspot {copy_from_id} not found'})
            
            if 'image' in request.FILES:
                hotspot.image = request.FILES['image']
            if 'video' in request.FILES:
                hotspot.video = request.FILES['video']
                
            hotspot.save()
            
            return JsonResponse({'status': 'success', 'id': hotspot.id})

            
            return JsonResponse({'status': 'success', 'id': hotspot.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

@csrf_exempt
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
def update_scene_nav(request, pk):
    """
    Updates the position of the Next or Prev navigation hotspot for a scene.
    pk: Scene ID
    POST data: nav_type ('next' or 'prev'), pitch, yaw
    """
    if request.method == 'POST':
        try:
            scene = get_object_or_404(Scene, pk=pk)
            nav_type = request.POST.get('nav_type') # 'next' or 'prev'
            pitch = float(request.POST.get('pitch'))
            yaw = float(request.POST.get('yaw'))
            
            if nav_type == 'next':
                scene.next_pitch = pitch
                scene.next_yaw = yaw
            elif nav_type == 'prev':
                scene.prev_pitch = pitch
                scene.prev_yaw = yaw
            else:
                 return JsonResponse({'status': 'error', 'message': 'Invalid nav_type'}, status=400)
            
            scene.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
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
                    icon_color=icon_color
                )

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
    API to list all available resources (hotspots) for the library.
    """
    try:
        hotspots = Hotspot.objects.select_related('scene', 'scene__project').all().order_by('-created_at')
        data = []
        for h in hotspots:
            item = {
                'id': h.id,
                'title': h.title,
                'description': h.description,
                'type': h.hotspot_type,
                'type_display': h.get_hotspot_type_display(),
                'project_name': h.scene.project.name,
                'scene_title': h.scene.title,
                'thumb_url': f"{h.image.url}?v={int(h.updated_at.timestamp())}" if h.image and h.hotspot_type in ['image', 'image_hover'] else None,
                'video_url': f"{h.video.url}?v={int(h.updated_at.timestamp())}" if h.video else None,
                'has_video': bool(h.video),
                'icon': h.icon,
                'icon_color': h.icon_color,
                'usage_count': h.copied_by.count()
            }
            data.append(item)
        return JsonResponse({'status': 'success', 'resources': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
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
    Displays a list of all resources (hotspots) in a project defined by pk.
    """
    project = get_object_or_404(Project, pk=pk)
    # Get all scenes ordered by 'order'
    scenes = project.scenes.all().order_by('order')
    
    # We want to display resources grouped by scene.
    # The template can iterate over scenes and then their hotspots.
    # Hotspots should be pre-fetched to avoid N+1 queries.
    from django.db.models import Prefetch
    scenes = scenes.prefetch_related(
        Prefetch('hotspots', queryset=Hotspot.objects.annotate(usage_count=Count('copied_by')).select_related('source_hotspot').order_by('created_at'))
    )
    
    context = {
        'project': project,
        'scenes': scenes,
    }
    return render(request, 'site360/resource_list.html', context)

def all_resource_list(request):
    """
    Displays a list of all resources (hotspots) across all projects.
    """
    from django.db.models import Prefetch

    scenes = Scene.objects.all().order_by('project', 'order').prefetch_related(
        'project',
        Prefetch('hotspots', queryset=Hotspot.objects.annotate(usage_count=Count('copied_by')).select_related('source_hotspot').order_by('created_at'))
    )
    
    projects = Project.objects.all().order_by('name')

    context = {
        'scenes': scenes,
        'all_projects': projects,
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
                    "sceneId": str(next_scene.id),
                    "icon": "fas fa-arrow-circle-right",
                    "icon_color": "#000000",
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
                    "sceneId": str(prev_scene.id),
                    "icon": "fas fa-arrow-circle-left",
                    "icon_color": "#000000",
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
                    "source_hotspot_title": hs.source_hotspot.title if hs.source_hotspot else None
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
    projet = get_object_or_404(Project, pk=pk)
    return render(request, 'site360/tour.html', {'project': projet})

@csrf_exempt
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
            
            # Always update directly - no version creation in basic edit
            # Version control is for resource library references, not direct edits
            hotspot.title = title
            hotspot.description = description
            hotspot.hotspot_type = hotspot_type
            
            # Check if this is a referencing hotspot
            if hotspot.source_hotspot:
                # If referencing, do NOT allow changing media
                if 'image' in request.FILES or 'video' in request.FILES:
                    return JsonResponse({
                        'status': 'error', 
                        'message': '此為引用資源，無法修改媒體內容。請編輯原始資源。'
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
        references = Hotspot.objects.filter(source_hotspot=resource).select_related('scene', 'scene__project')
        
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
                'project_name': ref.scene.project.name,
                'scene_title': ref.scene.title,
                'scene_id': ref.scene.id,
                'hotspot_title': ref.title,
                'hotspot_description': ref.description,  # The reference's description (may be modified)
                'source_description': resource.description,  # The original resource's description
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
