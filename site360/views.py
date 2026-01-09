from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Max
from .forms import ProjectForm, SceneForm
from .models import Project, Scene, Hotspot
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
import os
import re

class ProjectListView(ListView):
    model = Project
    template_name = 'site360/project_list.html'
    context_object_name = 'projects'

class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'site360/project_form.html'
    success_url = reverse_lazy('site360:project_list')

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'site360/project_detail.html'
    context_object_name = 'project'

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
            
            if 'image' in request.FILES:
                hotspot.image = request.FILES['image']
            if 'video' in request.FILES:
                hotspot.video = request.FILES['video']
                
            hotspot.save()
            
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
            hotspot = get_object_or_404(Hotspot, pk=pk)
            hotspot.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)

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
                "pitch": -5,
                "yaw": 0,
                "type": "scene",
                "text": f"Next: {next_scene.title}",
                "sceneId": str(next_scene.id)
            })
        if prev_scene:
            hotspots.append({
                "pitch": -5,
                "yaw": 180,
                "type": "scene",
                "text": f"Prev: {prev_scene.title}",
                "sceneId": str(prev_scene.id)
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
                    "image": hs.image.url if hs.image else "",
                    "video": reverse('site360:serve_hotspot_video', kwargs={'pk': hs.id}) if hs.video else ""
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
