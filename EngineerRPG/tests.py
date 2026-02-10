from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AdminWhitelist, CharacterClass, GuildPost, RPGTeam, RPGTeamMember, UserProfile


class GuildHallViewsTest(TestCase):
    def setUp(self):
        self.character_class = CharacterClass.objects.create(
            code='CIVIL',
            name='Civil',
            description='Civil class',
        )

    def _create_profile(self, username, role='ADVENTURER', whitelist_role=None):
        user = User.objects.create_user(username=username, password='test-pass-123')
        profile = getattr(user, 'rpg_profile', None)
        if profile is None:
            profile = UserProfile.objects.create(
                user=user,
                employee_id=f'EMP-{username}',
                character_class=self.character_class,
                role=role,
            )
        else:
            profile.employee_id = f'EMP-{username}'
            profile.character_class = self.character_class
            profile.role = role
            profile.save(update_fields=['employee_id', 'character_class', 'role'])
        if whitelist_role:
            AdminWhitelist.objects.create(user=user, role=whitelist_role)
        return user, profile

    def test_guild_dashboard_renders_for_logged_in_user(self):
        user, profile = self._create_profile('viewer')
        team_user, team_member_profile = self._create_profile('member')
        RPGTeam.objects.create(
            name='Alpha',
            created_by=user,
            leader=user,
            is_active=True,
        )
        team = RPGTeam.objects.get(name='Alpha')
        RPGTeamMember.objects.create(team=team, user_profile=team_member_profile, role='MEMBER')

        GuildPost.objects.create(
            author=profile,
            title='公告測試',
            content='公告內容',
            category='ANNOUNCEMENT',
        )
        GuildPost.objects.create(
            author=profile,
            title='交流測試',
            content='交流內容',
            category='GENERAL',
        )

        self.client.login(username='viewer', password='test-pass-123')
        response = self.client.get(reverse('engineer_rpg:guild_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '公告測試')
        self.assertContains(response, '交流測試')
        self.assertContains(response, team_user.username)

    def test_guild_announcement_create_rejects_adventurer(self):
        user, _ = self._create_profile('adventurer')
        self.client.login(username=user.username, password='test-pass-123')

        response = self.client.post(
            reverse('engineer_rpg:guild_announcement_create'),
            {'title': 'Nope', 'content': 'No permission'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('engineer_rpg:guild_dashboard'))
        self.assertFalse(GuildPost.objects.filter(title='Nope', category='ANNOUNCEMENT').exists())

    def test_guild_announcement_create_for_officer(self):
        user, _ = self._create_profile('officer', role='ADVENTURER', whitelist_role='OFFICER')
        self.client.login(username=user.username, password='test-pass-123')

        response = self.client.post(
            reverse('engineer_rpg:guild_announcement_create'),
            {'title': '可發布公告', 'content': '有權限'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('engineer_rpg:guild_announcement_list'))
        self.assertTrue(GuildPost.objects.filter(title='可發布公告', category='ANNOUNCEMENT').exists())

    def test_profile_role_admin_without_whitelist_cannot_create_announcement(self):
        user, _ = self._create_profile('role_admin_only', role='ADMIN')
        self.client.login(username=user.username, password='test-pass-123')

        response = self.client.post(
            reverse('engineer_rpg:guild_announcement_create'),
            {'title': '不應建立', 'content': '沒有白名單'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('engineer_rpg:guild_dashboard'))
        self.assertFalse(GuildPost.objects.filter(title='不應建立', category='ANNOUNCEMENT').exists())

    def test_member_profile_detail_renders(self):
        viewer_user, _ = self._create_profile('viewer2')
        _, target_profile = self._create_profile('target')
        self.client.login(username=viewer_user.username, password='test-pass-123')

        response = self.client.get(
            reverse('engineer_rpg:member_profile_detail', kwargs={'member_id': target_profile.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, target_profile.user.username)
