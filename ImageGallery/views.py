from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST

from .models import Image, ImageCategory, ImageRating
from django.forms import modelformset_factory
from .forms import ImageUploadForm, CategoryForm, BulkUploadForm, ImageBatchEditForm, ImageEditForm


def gallery_list(request):
    """圖片列表頁面"""
    images = Image.objects.select_related('uploaded_by', 'category').all()
    
    # 分類篩選
    category_id = request.GET.get('category')
    if category_id:
        images = images.filter(category_id=category_id)
    
    # 搜尋功能
    search = request.GET.get('search')
    if search:
        images = images.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    # 排序
    sort = request.GET.get('sort', '-uploaded_at')
    if sort == 'rating':
        # 依評分排序
        images = images.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating', '-uploaded_at')
    elif sort == 'popular':
        # 依瀏覽次數排序
        images = images.order_by('-view_count', '-uploaded_at')
    else:
        images = images.order_by(sort)
    
    # 分頁
    paginator = Paginator(images, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 取得所有分類
    categories = ImageCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_id,
        'current_sort': sort,
        'search_query': search or '',
    }
    return render(request, 'gallery/gallery_list.html', context)


def gallery_detail(request, pk):
    """圖片詳情頁面"""
    image = get_object_or_404(
        Image.objects.select_related('uploaded_by', 'category'),
        pk=pk
    )
    
    # 增加瀏覽次數
    image.increment_view_count()
    
    # 取得使用者的評分
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = ImageRating.objects.get(image=image, user=request.user)
        except ImageRating.DoesNotExist:
            pass
    
    # 取得評分分布
    rating_distribution = image.get_rating_distribution()
    
    context = {
        'image': image,
        'user_rating': user_rating,
        'rating_distribution': rating_distribution,
    }
    return render(request, 'gallery/gallery_detail.html', context)


@login_required
def gallery_upload(request):
    """圖片上傳頁面（單張）"""
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.uploaded_by = request.user
            image.save()
            messages.success(request, '圖片上傳成功！')
            return redirect('gallery:detail', pk=image.pk)
    else:
        form = ImageUploadForm()
    
    context = {
        'form': form,
    }
    return render(request, 'gallery/gallery_upload.html', context)


@login_required
def gallery_upload_bulk(request):
    """批量圖片上傳 API"""
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_ids = []
            images = request.FILES.getlist('images')
            
            for image_file in images:
                # 使用檔名作為預設標題（去除副檔名）
                title = image_file.name.rsplit('.', 1)[0]
                
                image = Image.objects.create(
                    title=title,
                    image=image_file,
                    uploaded_by=request.user
                )
                uploaded_ids.append(image.id)
            
            # 將上傳的圖片 ID 存入 Session，供批量編輯使用
            request.session['bulk_edit_ids'] = uploaded_ids
            
            return JsonResponse({
                'success': True, 
                'redirect_url': '/gallery/batch-edit/',
                'message': f'成功上傳 {len(uploaded_ids)} 張圖片'
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    return JsonResponse({'success': False, 'error': '不支援的請求方法'}, status=405)


@login_required
def gallery_batch_edit(request):
    """批量編輯頁面"""
    # 從 Session 取得要編輯的圖片 ID
    image_ids = request.session.get('bulk_edit_ids', [])
    
    if not image_ids:
        messages.warning(request, '沒有需要編輯的圖片')
        return redirect('gallery:list')
    
    # 建立 FormSet
    ImageFormSet = modelformset_factory(
        Image, 
        form=ImageBatchEditForm, 
        extra=0, 
        can_delete=True
    )
    
    queryset = Image.objects.filter(id__in=image_ids, uploaded_by=request.user)
    
    if request.method == 'POST':
        formset = ImageFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            # 清除 Session
            if 'bulk_edit_ids' in request.session:
                del request.session['bulk_edit_ids']
            
            messages.success(request, '圖片資訊更新成功！')
            return redirect('gallery:list')
    else:
        formset = ImageFormSet(queryset=queryset)
    
    context = {
        'formset': formset,
    }
    return render(request, 'gallery/gallery_batch_edit.html', context)


@login_required
@require_POST
def image_rate(request, pk):
    """圖片評分 API"""
    image = get_object_or_404(Image, pk=pk)
    rating_value = request.POST.get('rating')
    
    try:
        rating_value = int(rating_value)
        if rating_value < 1 or rating_value > 5:
            return JsonResponse({'success': False, 'error': '評分必須在 1-5 之間'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': '無效的評分'}, status=400)
    
    # 建立或更新評分
    rating, created = ImageRating.objects.update_or_create(
        image=image,
        user=request.user,
        defaults={'rating': rating_value}
    )
    
    # 重新計算平均評分
    avg_rating = image.average_rating
    total_ratings = image.total_ratings
    
    return JsonResponse({
        'success': True,
        'average_rating': avg_rating,
        'total_ratings': total_ratings,
        'user_rating': rating_value,
        'message': '評分已更新' if not created else '評分成功'
    })


def leaderboard(request, period='all'):
    """排行榜頁面"""
    # 計算時間範圍
    now = timezone.now()

    if period == 'week':
        # 本周（週一到週日）
        start_of_week = now - timedelta(days=now.weekday())
        start_date = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        title = '本周排行榜'
    elif period == 'month':
        # 本月
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        title = '本月排行榜'
    else:
        # 總排行
        start_date = None
        title = '總排行榜'

    # 獲取排序方式（rating: 評分, views: 瀏覽次數）
    sort_by = request.GET.get('sort', 'rating')

    # 查詢圖片
    images = Image.objects.select_related('uploaded_by', 'category').all()

    # 計算平均評分和評分數量
    images = images.annotate(
        avg_rating=Avg('ratings__rating'),
        rating_count=Count('ratings')
    )

    # 根據排序方式篩選和排序
    if sort_by == 'views':
        # 按瀏覽次數排序（至少 1 次瀏覽）
        images = images.filter(view_count__gte=1).order_by('-view_count', '-avg_rating')[:50]
        sort_title = '（依瀏覽次數）'
    else:
        # 按評分排序（至少 1 個評分）
        images = images.filter(rating_count__gte=1).order_by('-avg_rating', '-rating_count')[:50]
        sort_title = '（依評分）'

    context = {
        'images': images,
        'period': period,
        'title': title + ' ' + sort_title,
        'sort_by': sort_by,
    }
    return render(request, 'gallery/leaderboard.html', context)


@login_required
def category_manage(request):
    """分類管理頁面"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            messages.success(request, f'分類「{category.name}」建立成功！')
            return redirect('gallery:category_manage')
    else:
        form = CategoryForm()

    # 取得所有分類
    categories = ImageCategory.objects.select_related('created_by').all()

    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'gallery/category_manage.html', context)


@login_required
def gallery_edit(request, pk):
    """單張圖片編輯頁面"""
    image = get_object_or_404(Image, pk=pk)

    # 確保只有上傳者可以編輯
    if image.uploaded_by != request.user:
        messages.error(request, '您沒有權限編輯此圖片')
        return redirect('gallery:detail', pk=pk)

    if request.method == 'POST':
        form = ImageEditForm(request.POST, instance=image)
        if form.is_valid():
            form.save()
            messages.success(request, '圖片資訊更新成功！')
            return redirect('gallery:detail', pk=pk)
    else:
        form = ImageEditForm(instance=image)

    context = {
        'form': form,
        'image': image,
    }
    return render(request, 'gallery/gallery_edit.html', context)
