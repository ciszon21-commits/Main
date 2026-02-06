from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db.models import Q, Count
from django.db.models.functions import Concat
import json

from .models import Scene, SceneObject, Asset3D, Panorama, InfoCard, CardReadStatus
from .forms import SceneForm, Asset3DForm, PanoramaForm, InfoCardForm

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

class SceneUpdateView(UpdateView):
    model = Scene
    form_class = SceneForm
    template_name = 'sinoVR/scene_form.html'
    context_object_name = 'scene'

    def get_success_url(self):
        return reverse_lazy('sinoVR:scene_list')

    def form_valid(self, form):
        if form.cleaned_data.get('new_background_image'):
            image = form.cleaned_data['new_background_image']
            try:
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
        context['info_cards'] = InfoCard.objects.all()
        return context

class SceneViewerView(DetailView):
    model = Scene
    template_name = 'sinoVR/viewer.html'
    context_object_name = 'scene'

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
                info_card_id = obj_data.get('info_card_id')
                
                if not asset_id and not info_card_id:
                    continue
                
                asset = Asset3D.objects.get(pk=asset_id) if asset_id else None
                info_card = InfoCard.objects.get(pk=info_card_id) if info_card_id else None
                transform = obj_data.get('transform', {})
                position = transform.get('position', {})
                rotation = transform.get('rotation', {})
                scale = transform.get('scale', {})
                
                SceneObject.objects.create(
                    scene=scene,
                    asset=asset,
                    info_card=info_card,
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
        # Handle InfoCard creation via JSON
        elif request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                if data.get('type') == 'info_card':
                    info_card = InfoCard.objects.create(
                        title=data.get('title', ''),
                        content=data.get('content', ''),
                        bg_color=data.get('bg_color', 'rgba(173, 216, 230, 0.95)'),
                        content_font_size=data.get('content_font_size', 50)
                    )
                    return JsonResponse({'id': info_card.id, 'title': info_card.title, 'type': 'info_card'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error'}, status=400)


class InfoCardUpdateView(View):
    """API to update existing InfoCard"""
    def post(self, request, card_id):
        try:
            data = json.loads(request.body)
            info_card = InfoCard.objects.get(id=card_id)
            
            info_card.title = data.get('title', info_card.title)
            info_card.content = data.get('content', info_card.content)
            info_card.bg_color = data.get('bg_color', info_card.bg_color)
            info_card.content_font_size = data.get('content_font_size', info_card.content_font_size)
            info_card.save()
            
            return JsonResponse({
                'status': 'success',
                'id': info_card.id,
                'title': info_card.title
            })
        except InfoCard.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'InfoCard not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AssetDeleteView(View):
    def post(self, request, pk):
        asset = get_object_or_404(Asset3D, pk=pk)
        try:
            asset.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def delete(self, request, pk):
        return self.post(request, pk)

@method_decorator(csrf_exempt, name='dispatch')
class PanoramaDeleteView(View):
    def post(self, request, pk):
        pano = get_object_or_404(Panorama, pk=pk)
        try:
            pano.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def delete(self, request, pk):
        return self.post(request, pk)

@method_decorator(csrf_exempt, name='dispatch')
class InfoCardReadAPI(View):
    def post(self, request, card_id):
        if not request.user.is_authenticated:
             return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)
        
        info_card = get_object_or_404(InfoCard, id=card_id)
        from .models import CardReadStatus
        
        # Always create a new record for history tracking
        CardReadStatus.objects.create(user=request.user, info_card=info_card, is_read=True)
            
        return JsonResponse({'status': 'success', 'is_read': True})

class ReadStatusListView(ListView):
    model = CardReadStatus
    template_name = 'sinoVR/read_logs.html'
    context_object_name = 'object_list'
    ordering = ['-read_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['scenes'] = Scene.objects.all()
        return context

    def get_queryset(self):
        queryset = CardReadStatus.objects.select_related('user', 'info_card').prefetch_related('info_card__sceneobject_set__scene').order_by('-read_at')
        
        # 1. Scene Filter (Dropdown)
        scene_id = self.request.GET.get('scene')
        if scene_id:
            # Use subquery to avoid complex join issues
            card_ids = SceneObject.objects.filter(scene_id=scene_id).values_list('info_card_id', flat=True)
            queryset = queryset.filter(info_card_id__in=card_ids)

        # 2. User Filter (Text)
        user_query = self.request.GET.get('user')
        if user_query:
            queryset = queryset.annotate(
                full_name_nospace=Concat('user__last_name', 'user__first_name'),
                full_name_reverse=Concat('user__first_name', 'user__last_name')
            ).filter(
                Q(user__username__icontains=user_query) |
                Q(user__first_name__icontains=user_query) |
                Q(user__last_name__icontains=user_query) |
                Q(full_name_nospace__icontains=user_query) |
                Q(full_name_reverse__icontains=user_query)
            )

        # 3. Content/Keyword Filter (Text)
        keyword = self.request.GET.get('keyword')
        if keyword:
            queryset = queryset.filter(
                Q(info_card__title__icontains=keyword) |
                Q(info_card__content__icontains=keyword)
            )
            
        return queryset.distinct()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class AssetManagementView(View):
    template_name = 'sinoVR/asset_list.html'

    @method_decorator(login_required)
    def get(self, request):
        assets_3d = Asset3D.objects.all().annotate(
            usage_count=Count('sceneobject')
        ).select_related('uploader').order_by('-uploaded_at')
        
        panoramas = Panorama.objects.all().order_by('-uploaded_at')
        return render(request, self.template_name, {
            'assets_3d': assets_3d,
            'panoramas': panoramas
        })

    @method_decorator(login_required)
    def post(self, request):
        upload_type = request.POST.get('upload_type')
        
        try:
            if upload_type == 'model':
                file = request.FILES.get('file')
                if file:
                    Asset3D.objects.create(
                        title=file.name, 
                        file=file,
                        uploader=request.user
                    )
            elif upload_type == 'panorama':
                image = request.FILES.get('image')
                if image:
                    Panorama.objects.create(title=image.name, image=image)
        except Exception as e:
            # Simple error handling for now, maybe add messages later
            pass
            
        return redirect('sinoVR:asset_list')
