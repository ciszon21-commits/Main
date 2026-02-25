import json
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, FileResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Max, Count, Value, CharField
from django.db.models.functions import Concat
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.core.paginator import Paginator

from .models import ChatRoom, ChatRoomMember, ChatMessage, ChatFile, ChatFileDownloadLog

# 每個聊天室最多顯示的訊息數量
MAX_MESSAGES_PER_ROOM = 50


def get_display_name(user):
    if not user:
        return '系統'
    full_name = user.get_full_name()
    if full_name:
        return full_name.strip() or user.username
    return user.username


def build_file_payload(chat_file):
    access_url = reverse('sinochat:file_access', args=[chat_file.id])
    return {
        'id': chat_file.id,
        'name': chat_file.original_name,
        'size': chat_file.file_size_display,
        'url': access_url,
        'download_url': f"{access_url}?download=1",
        'is_image': chat_file.is_image,
    }


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def chat_room_list(request):
    """聊天室列表頁面"""
    # 獲取用戶可以看到的聊天室
    # 公開的聊天室 或 用戶是成員的私人聊天室
    user = request.user

    if user.is_superuser:
        rooms = ChatRoom.objects.filter(is_active=True)
    else:
        public_rooms = ChatRoom.objects.filter(visibility='public', is_active=True)
        private_rooms = ChatRoom.objects.filter(
            visibility='private',
            is_active=True
        ).filter(
            Q(creator=user) |
            Q(members__user=user, members__is_active=True)
        )

        # 合併並去重
        rooms = (public_rooms | private_rooms).distinct()

    rooms = rooms.annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time', '-updated_at')

    # 獲取每個聊天室的未讀數量
    room_data = []
    for room in rooms:
        membership = room.members.filter(user=user, is_active=True).first()
        unread_count = 0
        if membership:
            unread_count = room.messages.filter(
                created_at__gt=membership.last_read_at
            ).exclude(sender=user).count()

        last_msg = room.last_message
        room_data.append({
            'room': room,
            'unread_count': unread_count,
            'last_message': last_msg,
            'is_member': membership is not None,
        })

    context = {
        'room_data': room_data,
    }
    return render(request, 'SinoChat/room_list.html', context)


@login_required
def chat_room_detail(request, room_id):
    """聊天室對話頁面"""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    user = request.user

    # 檢查訪問權限
    if not room.can_user_access(user):
        return render(request, 'SinoChat/access_denied.html', {'room': room})

    # 自動加入公開聊天室
    membership, created = ChatRoomMember.objects.get_or_create(
        room=room,
        user=user,
        defaults={'role': 'member'}
    )

    # 更新最後讀取時間
    membership.last_read_at = timezone.now()
    membership.save()

    # 獲取最後 50 條訊息
    messages = room.messages.filter(is_deleted=False).order_by('-created_at')[:MAX_MESSAGES_PER_ROOM]
    messages = list(reversed(messages))  # 反轉順序，讓舊的訊息在上面

    # 獲取聊天室成員
    members = room.members.filter(is_active=True).select_related('user', 'user__profile')

    context = {
        'room': room,
        'messages': messages,
        'members': members,
        'is_admin': membership.role == 'admin' or room.creator == user,
        'max_messages': MAX_MESSAGES_PER_ROOM,
    }
    return render(request, 'SinoChat/room_detail.html', context)


@login_required
def create_room(request):
    """建立聊天室頁面"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        visibility = request.POST.get('visibility', 'public')
        avatar_color = request.POST.get('avatar_color', '#C41E3A')
        invited_users = request.POST.getlist('invited_users')

        if not name:
            return JsonResponse({'success': False, 'error': '請輸入聊天室名稱'})

        # 建立聊天室
        room = ChatRoom.objects.create(
            name=name,
            description=description,
            creator=request.user,
            visibility=visibility,
            avatar_color=avatar_color,
        )

        # 將建立者加為管理員
        ChatRoomMember.objects.create(
            room=room,
            user=request.user,
            role='admin'
        )

        # 建立系統訊息
        ChatMessage.objects.create(
            room=room,
            sender=None,
            message_type='system',
            content=f'{get_display_name(request.user)} 建立了聊天室'
        )

        # 邀請成員（私人聊天室）
        if visibility == 'private' and invited_users:
            for user_id in invited_users:
                try:
                    invited_user = User.objects.get(id=user_id)
                    ChatRoomMember.objects.get_or_create(
                        room=room,
                        user=invited_user,
                        defaults={'role': 'member'}
                    )
                except User.DoesNotExist:
                    pass

        return redirect('sinochat:room_detail', room_id=room.id)

    # GET 請求 - 顯示建立表單
    users = User.objects.filter(is_active=True).exclude(id=request.user.id).select_related('profile')
    context = {
        'users': users,
        'color_options': ['#C41E3A', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4', '#E91E63', '#607D8B'],
    }
    return render(request, 'SinoChat/create_room.html', context)


@login_required
@require_http_methods(["POST"])
def send_message(request, room_id):
    """發送訊息 API"""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    user = request.user

    # 檢查訪問權限
    if not room.can_user_access(user):
        return JsonResponse({'success': False, 'error': '您沒有權限發送訊息'})

    content = request.POST.get('content', '').strip()
    message_type = request.POST.get('message_type', 'text')

    if not content and not request.FILES:
        return JsonResponse({'success': False, 'error': '訊息內容不能為空'})

    # 建立訊息
    message = ChatMessage.objects.create(
        room=room,
        sender=user,
        message_type=message_type,
        content=content
    )

    # 處理檔案上傳
    files_data = []
    if request.FILES:
        for uploaded_file in request.FILES.getlist('files'):
            file_type = mimetypes.guess_type(uploaded_file.name)[0] or ''
            chat_file = ChatFile.objects.create(
                message=message,
                file=uploaded_file,
                original_name=uploaded_file.name,
                file_size=uploaded_file.size,
                file_type=file_type
            )
            files_data.append(build_file_payload(chat_file))

        # 如果有檔案但沒有內容，設定訊息類型
        if files_data and not content:
            if all(f['is_image'] for f in files_data):
                message.message_type = 'image'
            else:
                message.message_type = 'file'
            message.save()

    # 更新聊天室的更新時間
    room.updated_at = timezone.now()
    room.save()

    # 刪除超過 50 條的舊訊息（實現燒掉效果）
    old_messages = room.messages.filter(is_deleted=False).order_by('-created_at')[MAX_MESSAGES_PER_ROOM:]
    for old_msg in old_messages:
        old_msg.is_deleted = True
        old_msg.save()

    # 獲取發送者資訊
    sender_name = get_display_name(user)

    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'message_type': message.message_type,
            'sender_id': user.id,
            'sender_name': sender_name,
            'created_at': message.created_at.strftime('%p %I:%M').replace('AM', '上午').replace('PM', '下午'),
            'files': files_data,
        }
    })


@login_required
def get_messages(request, room_id):
    """獲取訊息 API（用於輪詢）"""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    user = request.user

    if not room.can_user_access(user):
        return JsonResponse({'success': False, 'error': '您沒有權限查看訊息'})

    # 獲取最後一條訊息 ID
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except:
        last_id = 0

    # 獲取新訊息
    new_messages = room.messages.filter(
        id__gt=last_id,
        is_deleted=False
    ).order_by('created_at')

    messages_data = []
    for msg in new_messages:
        sender_name = get_display_name(msg.sender)

        files_data = []
        for f in msg.files.all():
            files_data.append(build_file_payload(f))

        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'message_type': msg.message_type,
            'sender_id': msg.sender.id if msg.sender else None,
            'sender_name': sender_name,
            'created_at': msg.created_at.strftime('%p %I:%M').replace('AM', '上午').replace('PM', '下午'),
            'files': files_data,
            'is_self': msg.sender == user if msg.sender else False,
        })

    # 更新最後讀取時間
    membership = room.members.filter(user=user, is_active=True).first()
    if membership:
        membership.last_read_at = timezone.now()
        membership.save()

    return JsonResponse({
        'success': True,
        'messages': messages_data,
    })


@login_required
@require_http_methods(["POST"])
def invite_members(request, room_id):
    """邀請成員 API"""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    user = request.user

    # 檢查是否是管理員
    membership = room.members.filter(user=user, is_active=True).first()
    if not membership or (membership.role != 'admin' and room.creator != user):
        return JsonResponse({'success': False, 'error': '您沒有權限邀請成員'})

    user_ids = request.POST.getlist('user_ids')
    invited_count = 0

    for user_id in user_ids:
        try:
            invited_user = User.objects.get(id=user_id)
            _, created = ChatRoomMember.objects.get_or_create(
                room=room,
                user=invited_user,
                defaults={'role': 'member'}
            )
            if created:
                invited_count += 1
                # 建立系統訊息
                ChatMessage.objects.create(
                    room=room,
                    sender=None,
                    message_type='system',
                    content=f'{get_display_name(invited_user)} 已被邀請加入聊天室'
                )
        except User.DoesNotExist:
            pass

    return JsonResponse({
        'success': True,
        'invited_count': invited_count,
    })


@login_required
@require_http_methods(["POST"])
def leave_room(request, room_id):
    """離開聊天室 API"""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    user = request.user

    membership = room.members.filter(user=user, is_active=True).first()
    if membership:
        membership.is_active = False
        membership.save()

        # 建立系統訊息
        ChatMessage.objects.create(
            room=room,
            sender=None,
            message_type='system',
            content=f'{get_display_name(user)} 已離開聊天室'
        )

    return JsonResponse({'success': True})


@login_required
def search_users(request):
    """搜尋用戶 API"""
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'users': []})

    users = User.objects.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
    ).filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(full_name__icontains=query) |
        Q(profile__emp_name__icontains=query)
    ).filter(is_active=True).exclude(id=request.user.id)[:10]

    users_data = []
    for u in users:
        name = get_display_name(u)
        users_data.append({
            'id': u.id,
            'username': u.username,
            'name': name,
        })

    return JsonResponse({'users': users_data})


@login_required
def download_logs(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    if not room.can_user_access(request.user):
        return JsonResponse({'success': False, 'error': '無權限'})

    try:
        logs = ChatFileDownloadLog.objects.filter(
            file__message__room=room
        ).select_related('file', 'downloaded_by').order_by('-downloaded_at')[:200]
    except (OperationalError, ProgrammingError):
        return JsonResponse({'success': False, 'error': '下載記錄資料表尚未建立，請先執行資料庫遷移。'})

    logs_data = []
    for log in logs:
        downloaded_at = timezone.localtime(log.downloaded_at).strftime('%Y-%m-%d %H:%M')
        logs_data.append({
            'id': log.id,
            'file_id': log.file.id,
            'file_name': log.file.original_name,
            'downloaded_by': get_display_name(log.downloaded_by) if log.downloaded_by else '未知',
            'downloaded_at': downloaded_at,
            'download_url': f"{reverse('sinochat:file_access', args=[log.file.id])}?download=1",
        })

    return JsonResponse({'success': True, 'logs': logs_data})


@login_required
def file_access(request, file_id):
    chat_file = get_object_or_404(ChatFile, id=file_id)
    room = chat_file.message.room

    if not room.can_user_access(request.user):
        return HttpResponseForbidden('Access denied')

    content_type = chat_file.file_type or mimetypes.guess_type(chat_file.original_name)[0] or 'application/octet-stream'
    as_attachment = request.GET.get('download') == '1'
    if as_attachment:
        try:
            ChatFileDownloadLog.objects.create(
                file=chat_file,
                downloaded_by=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception:
            pass
    return FileResponse(
        chat_file.file.open('rb'),
        as_attachment=as_attachment,
        filename=chat_file.original_name,
        content_type=content_type,
    )
