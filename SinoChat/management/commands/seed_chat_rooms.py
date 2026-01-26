import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from SinoChat.models import ChatRoom, ChatRoomMember, ChatMessage

class Command(BaseCommand):
    help = 'Seed initial chat rooms for SinoChat'

    def handle(self, *args, **options):
        # 獲取或建立管理員用戶
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {admin_user.username}'))

        # 1. 建立 General Room (公開)
        general, created = ChatRoom.objects.get_or_create(
            name='General Room',
            defaults={
                'description': 'Sinotech 聊天室大廳 - 歡迎大家在此交流',
                'creator': admin_user,
                'visibility': 'public',
                'avatar_color': '#C41E3A'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created room: {general.name}'))
            ChatRoomMember.objects.get_or_create(room=general, user=admin_user, defaults={'role': 'admin'})
            ChatMessage.objects.create(
                room=general,
                sender=None,
                message_type='system',
                content='系統已自動建立大廳聊天室'
            )

        # 2. 建立 Tech Talk (公開)
        tech, created = ChatRoom.objects.get_or_create(
            name='Tech Talk 吹水區',
            defaults={
                'description': '技術交流與開發心得分享',
                'creator': admin_user,
                'visibility': 'public',
                'avatar_color': '#2196F3'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created room: {tech.name}'))
            ChatRoomMember.objects.get_or_create(room=tech, user=admin_user, defaults={'role': 'admin'})
            ChatMessage.objects.create(
                room=tech,
                sender=None,
                message_type='system',
                content='技術交流區已開張'
            )

        # 3. 建立 Project Alpha (私人)
        alpha, created = ChatRoom.objects.get_or_create(
            name='Project Alpha 密室',
            defaults={
                'description': '專案機密討論區',
                'creator': admin_user,
                'visibility': 'private',
                'avatar_color': '#4CAF50'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created room: {alpha.name}'))
            ChatRoomMember.objects.get_or_create(room=alpha, user=admin_user, defaults={'role': 'admin'})
            ChatMessage.objects.create(
                room=alpha,
                sender=None,
                message_type='system',
                content='機密討論室已建立，僅限邀約成員'
            )

        self.stdout.write(self.style.SUCCESS('SinoChat seeding completed!'))
