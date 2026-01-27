from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import Scene, SceneObject, Asset3D, Panorama
from .forms import SceneForm, Asset3DForm, PanoramaForm

class SceneListView(ListView):
    model = Scene
    template_name = 'sinoVR/scene_list.html'
    context_object_name = 'scenes'

class SceneCreateView(CreateView):
    model = Scene
    form_class = SceneForm
    template_name = 'sinoVR/scene_form.html'
    
    def get_success_url(self):
        return reverse_lazy('sinoVR:scene_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        if form.cleaned_data.get('new_background_image'):
            image = form.cleaned_data['new_background_image']
            # Create Panorama
            try:
                # Use scene title for panorama title if possible, or timestamp
                pano = Panorama.objects.create(title=f"{form.cleaned_data['title']} - Background", image=image)
                form.instance.background = pano
            except Exception as e:
                form.add_error('new_background_image', f"Upload failed: {e}")
                return self.form_invalid(form)
        return super().form_valid(form)

class SceneDetailView(DetailView):
    model = Scene
    template_name = 'sinoVR/editor.html'
    context_object_name = 'scene'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assets'] = Asset3D.objects.all()
        context['panoramas'] = Panorama.objects.all()
        return context

@method_decorator(csrf_exempt, name='dispatch')
class SceneUpdateAPI(View):
    def post(self, request, pk):
        scene = get_object_or_404(Scene, pk=pk)
        try:
            data = json.loads(request.body)
            objects_data = data.get('objects', [])
            
            # Clear existing objects or update them? 
            # For simplicity, let's sync. 
            # Strategy: Delete all objects in scene and recreate (simple but destructive for IDs)
            # OR: Update based on ID if present, create if new.
            
            # Simple approach for now:
            # We will receive a list of objects physically present in the scene.
            # However, mapping JS UUIDs to DB IDs is tricky if we don't persist them.
            # Let's assume the frontend sends everything.
            
            # Better approach: The frontend sends a list of {asset_id, transform}
            # We wipe old objects and recreate.
            SceneObject.objects.filter(scene=scene).delete()
            
            for obj_data in objects_data:
                asset_id = obj_data.get('asset_id')
                if not asset_id:
                    continue
                    
                asset = Asset3D.objects.get(pk=asset_id)
                transform = obj_data.get('transform', {})
                position = transform.get('position', {})
                rotation = transform.get('rotation', {})
                scale = transform.get('scale', {})
                
                SceneObject.objects.create(
                    scene=scene,
                    asset=asset,
                    position_x=position.get('x', 0),
                    position_y=position.get('y', 0),
                    position_z=position.get('z', 0),
                    rotation_x=rotation.get('x', 0),
                    rotation_y=rotation.get('y', 0),
                    rotation_z=rotation.get('z', 0),
                    scale_x=scale.get('x', 1),
                    scale_y=scale.get('y', 1),
                    scale_z=scale.get('z', 1),
                )
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class AssetUploadView(View):
    def post(self, request):
        # Handle simple file upload
        if 'file' in request.FILES:
            file = request.FILES['file']
            if file.name.lower().endswith('.fbx'):
                 asset = Asset3D.objects.create(title=file.name, file=file)
                 return JsonResponse({'id': asset.id, 'title': asset.title, 'url': asset.file.url, 'type': 'model'})
            elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                 pano = Panorama.objects.create(title=file.name, image=file)
                 return JsonResponse({'id': pano.id, 'title': pano.title, 'url': pano.image.url, 'type': 'panorama'})
        return JsonResponse({'status': 'error'}, status=400)
