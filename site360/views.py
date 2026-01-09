from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from .models import Project, Scene, Hotspot

class ProjectListView(ListView):
    model = Project
    template_name = 'site360/project_list.html'
    context_object_name = 'projects'

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'site360/project_detail.html'
    context_object_name = 'project'

@csrf_exempt
def save_hotspot(request):
    if request.method == 'POST':
        try:
            scene_id = request.POST.get('scene_id')
            hotspot_type = request.POST.get('type')
            pitch = request.POST.get('pitch')
            yaw = request.POST.get('yaw')
            title = request.POST.get('title')
            description = request.POST.get('description')
            
            scene = get_object_or_404(Scene, id=scene_id)
            
            hotspot = Hotspot(
                scene=scene,
                hotspot_type=hotspot_type,
                pitch=float(pitch),
                yaw=float(yaw),
                title=title,
                description=description
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
                    "image": hs.image.url if hs.image else "",
                    "video": hs.video.url if hs.video else ""
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
