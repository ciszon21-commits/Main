"""
TeamKnowledgeHub 單元測試
測試涵蓋 Models、Forms 和 Views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import KnowledgeTeam, KnowledgeTeamMember, Topic, KnowledgeItem, ItemComment
from .forms import KnowledgeTeamForm, TopicForm, KnowledgeItemForm, ItemCommentForm


# ===== Model Tests =====

class KnowledgeTeamModelTestCase(TestCase):
    """知識團隊模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            description='這是測試團隊的說明',
            created_by=self.user
        )
    
    def test_team_creation(self):
        """測試團隊建立"""
        self.assertEqual(self.team.name, '測試團隊')
        self.assertEqual(self.team.description, '這是測試團隊的說明')
        self.assertEqual(self.team.created_by, self.user)
    
    def test_team_str_representation(self):
        """測試團隊字串表示"""
        self.assertEqual(str(self.team), '測試團隊')
    
    def test_is_creator(self):
        """測試 is_creator 方法"""
        self.assertTrue(self.team.is_creator(self.user))
        self.assertFalse(self.team.is_creator(self.other_user))
    
    def test_is_member_with_membership(self):
        """測試 is_member 方法 - 有成員資格"""
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.other_user,
            role='member'
        )
        self.assertTrue(self.team.is_member(self.other_user))
    
    def test_is_member_without_membership(self):
        """測試 is_member 方法 - 無成員資格"""
        self.assertFalse(self.team.is_member(self.other_user))
    
    def test_get_member_count(self):
        """測試 get_member_count 方法"""
        self.assertEqual(self.team.get_member_count(), 0)
        
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.assertEqual(self.team.get_member_count(), 1)
        
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.other_user,
            role='member'
        )
        self.assertEqual(self.team.get_member_count(), 2)


class KnowledgeTeamMemberModelTestCase(TestCase):
    """團隊成員模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.member = KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
    
    def test_member_creation(self):
        """測試成員建立"""
        self.assertEqual(self.member.team, self.team)
        self.assertEqual(self.member.user, self.user)
        self.assertEqual(self.member.role, 'creator')
    
    def test_member_str_representation(self):
        """測試成員字串表示"""
        expected = f'{self.team.name} - Test User'
        self.assertEqual(str(self.member), expected)
    
    def test_member_str_without_full_name(self):
        """測試成員字串表示 - 無全名"""
        user_no_name = User.objects.create_user(
            username='noname',
            password='testpass123'
        )
        member = KnowledgeTeamMember.objects.create(
            team=self.team,
            user=user_no_name,
            role='member'
        )
        expected = f'{self.team.name} - noname'
        self.assertEqual(str(member), expected)
    
    def test_unique_together_constraint(self):
        """測試 unique_together 約束"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            KnowledgeTeamMember.objects.create(
                team=self.team,
                user=self.user,
                role='member'
            )


class TopicModelTestCase(TestCase):
    """主題模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.topic = Topic.objects.create(
            team=self.team,
            name='測試主題',
            description='主題說明',
            order=0
        )
    
    def test_topic_creation(self):
        """測試主題建立"""
        self.assertEqual(self.topic.name, '測試主題')
        self.assertEqual(self.topic.team, self.team)
        self.assertEqual(self.topic.order, 0)
    
    def test_topic_str_representation(self):
        """測試主題字串表示"""
        expected = f'{self.team.name} - 測試主題'
        self.assertEqual(str(self.topic), expected)
    
    def test_get_item_count(self):
        """測試 get_item_count 方法"""
        self.assertEqual(self.topic.get_item_count(), 0)
        
        KnowledgeItem.objects.create(
            topic=self.topic,
            title='測試項目',
            created_by=self.user
        )
        self.assertEqual(self.topic.get_item_count(), 1)


class KnowledgeItemModelTestCase(TestCase):
    """知識項目模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.topic = Topic.objects.create(
            team=self.team,
            name='測試主題'
        )
        self.item = KnowledgeItem.objects.create(
            topic=self.topic,
            title='測試知識項目',
            content='<p>這是內容</p>',
            created_by=self.user
        )
    
    def test_item_creation(self):
        """測試項目建立"""
        self.assertEqual(self.item.title, '測試知識項目')
        self.assertEqual(self.item.topic, self.topic)
        self.assertEqual(self.item.created_by, self.user)
    
    def test_item_str_representation(self):
        """測試項目字串表示"""
        self.assertEqual(str(self.item), '測試知識項目')
    
    def test_get_comment_count(self):
        """測試 get_comment_count 方法"""
        self.assertEqual(self.item.get_comment_count(), 0)
        
        ItemComment.objects.create(
            item=self.item,
            author=self.user,
            content='測試留言'
        )
        self.assertEqual(self.item.get_comment_count(), 1)


class ItemCommentModelTestCase(TestCase):
    """項目留言模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.topic = Topic.objects.create(
            team=self.team,
            name='測試主題'
        )
        self.item = KnowledgeItem.objects.create(
            topic=self.topic,
            title='測試項目',
            created_by=self.user
        )
        self.comment = ItemComment.objects.create(
            item=self.item,
            author=self.user,
            content='這是一則測試留言'
        )
    
    def test_comment_creation(self):
        """測試留言建立"""
        self.assertEqual(self.comment.item, self.item)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, '這是一則測試留言')
    
    def test_comment_str_representation(self):
        """測試留言字串表示"""
        self.assertIn('testuser', str(self.comment))
        self.assertIn('這是一則測試留言', str(self.comment))
    
    def test_comment_str_truncation(self):
        """測試留言字串表示 - 長內容截斷"""
        long_content = 'a' * 50
        comment = ItemComment.objects.create(
            item=self.item,
            author=self.user,
            content=long_content
        )
        # 字串表示只顯示前30字元
        self.assertIn(long_content[:30], str(comment))


# ===== Form Tests =====

class KnowledgeTeamFormTestCase(TestCase):
    """知識團隊表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'name': '新團隊',
            'description': '團隊說明'
        }
        form = KnowledgeTeamForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_valid_form_without_description(self):
        """測試有效表單 - 無說明"""
        data = {
            'name': '新團隊',
            'description': ''
        }
        form = KnowledgeTeamForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_name(self):
        """測試無效表單 - 無名稱"""
        data = {
            'name': '',
            'description': '說明'
        }
        form = KnowledgeTeamForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class TopicFormTestCase(TestCase):
    """主題表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'name': '新主題',
            'description': '主題說明',
            'order': 1
        }
        form = TopicForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_valid_form_minimal(self):
        """測試有效表單 - 最小資料"""
        data = {
            'name': '新主題',
            'description': '',
            'order': 0
        }
        form = TopicForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_name(self):
        """測試無效表單 - 無名稱"""
        data = {
            'name': '',
            'description': '',
            'order': 0
        }
        form = TopicForm(data=data)
        self.assertFalse(form.is_valid())


class KnowledgeItemFormTestCase(TestCase):
    """知識項目表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'title': '新項目標題',
            'content': '<p>項目內容</p>'
        }
        form = KnowledgeItemForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_valid_form_without_content(self):
        """測試有效表單 - 無內容"""
        data = {
            'title': '新項目標題',
            'content': ''
        }
        form = KnowledgeItemForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_title(self):
        """測試無效表單 - 無標題"""
        data = {
            'title': '',
            'content': '內容'
        }
        form = KnowledgeItemForm(data=data)
        self.assertFalse(form.is_valid())


class ItemCommentFormTestCase(TestCase):
    """項目留言表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'content': '這是一則留言'
        }
        form = ItemCommentForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_content(self):
        """測試無效表單 - 無內容"""
        data = {
            'content': ''
        }
        form = ItemCommentForm(data=data)
        self.assertFalse(form.is_valid())


# ===== View Tests =====

class TeamViewTestCase(TestCase):
    """團隊視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        # 建立者也要加入成員
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
    
    def test_team_list_requires_login(self):
        """測試團隊列表需要登入"""
        response = self.client.get(reverse('knowledge:team_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_team_list_authenticated(self):
        """測試團隊列表 - 已登入"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('knowledge:team_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試團隊')
    
    def test_team_detail_requires_login(self):
        """測試團隊詳情需要登入"""
        response = self.client.get(
            reverse('knowledge:team_detail', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_team_detail_member_access(self):
        """測試團隊詳情 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:team_detail', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試團隊')
    
    def test_team_detail_non_member_denied(self):
        """測試團隊詳情 - 非成員被拒絕"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:team_detail', kwargs={'pk': self.team.pk})
        )
        # 應該重定向到團隊列表
        self.assertEqual(response.status_code, 302)
    
    def test_team_create_get(self):
        """測試建立團隊頁面 - GET"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('knowledge:team_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_team_create_post_valid(self):
        """測試建立團隊 - POST 有效資料"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('knowledge:team_create'), {
            'name': '新建團隊',
            'description': '新團隊說明'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(KnowledgeTeam.objects.filter(name='新建團隊').exists())
    
    def test_team_update_creator_only(self):
        """測試編輯團隊 - 只有建立者"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:team_update', kwargs={'pk': self.team.pk})
        )
        # 非建立者應被重定向
        self.assertEqual(response.status_code, 302)
    
    def test_team_update_by_creator(self):
        """測試編輯團隊 - 建立者存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:team_update', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_team_members_creator_only(self):
        """測試管理成員 - 只有建立者"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:team_members', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 302)


class MemberManagementViewTestCase(TestCase):
    """成員管理視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.creator = User.objects.create_user(
            username='creator',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member',
            password='testpass123'
        )
        self.new_user = User.objects.create_user(
            username='newuser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.creator
        )
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.creator,
            role='creator'
        )
    
    def test_search_users_requires_login(self):
        """測試搜尋使用者需要登入"""
        response = self.client.get(
            reverse('knowledge:search_users') + '?q=test'
        )
        self.assertEqual(response.status_code, 302)
    
    def test_search_users_short_query(self):
        """測試搜尋使用者 - 查詢太短"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('knowledge:search_users') + '?q=t'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['users'], [])
    
    def test_search_users_valid_query(self):
        """測試搜尋使用者 - 有效查詢"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('knowledge:search_users') + '?q=new'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['users']) >= 1)
    
    def test_add_member_requires_post(self):
        """測試新增成員需要 POST"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('knowledge:add_member', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 405)
    
    def test_add_member_creator_only(self):
        """測試新增成員 - 只有建立者"""
        self.client.login(username='member', password='testpass123')
        response = self.client.post(
            reverse('knowledge:add_member', kwargs={'pk': self.team.pk}),
            {'user_id': self.new_user.pk}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_add_member_success(self):
        """測試新增成員 - 成功"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('knowledge:add_member', kwargs={'pk': self.team.pk}),
            {'user_id': self.new_user.pk}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(
            KnowledgeTeamMember.objects.filter(
                team=self.team, user=self.new_user
            ).exists()
        )
    
    def test_add_member_duplicate(self):
        """測試新增成員 - 重複"""
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.new_user,
            role='member'
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('knowledge:add_member', kwargs={'pk': self.team.pk}),
            {'user_id': self.new_user.pk}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_remove_member_success(self):
        """測試移除成員 - 成功"""
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.new_user,
            role='member'
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('knowledge:remove_member', kwargs={
                'pk': self.team.pk,
                'user_id': self.new_user.pk
            })
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_remove_creator_denied(self):
        """測試移除建立者 - 被拒絕"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('knowledge:remove_member', kwargs={
                'pk': self.team.pk,
                'user_id': self.creator.pk
            })
        )
        self.assertEqual(response.status_code, 400)


class TopicViewTestCase(TestCase):
    """主題視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.topic = Topic.objects.create(
            team=self.team,
            name='測試主題'
        )
    
    def test_topic_create_requires_member(self):
        """測試建立主題需要成員身份"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:topic_create', kwargs={'team_pk': self.team.pk})
        )
        # 非成員應被重定向
        self.assertEqual(response.status_code, 302)
    
    def test_topic_create_member_access(self):
        """測試建立主題 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:topic_create', kwargs={'team_pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_topic_create_post_valid(self):
        """測試建立主題 - POST 有效資料"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('knowledge:topic_create', kwargs={'team_pk': self.team.pk}),
            {'name': '新主題', 'description': '', 'order': 1}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Topic.objects.filter(name='新主題').exists())
    
    def test_topic_update_member_access(self):
        """測試編輯主題 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:topic_update', kwargs={'pk': self.topic.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_topic_delete_creator_only(self):
        """測試刪除主題 - 只有建立者"""
        # 新增一個成員
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.other_user,
            role='member'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:topic_delete', kwargs={'pk': self.topic.pk})
        )
        # 非建立者應被重定向
        self.assertEqual(response.status_code, 302)
    
    def test_topic_delete_by_creator(self):
        """測試刪除主題 - 建立者存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:topic_delete', kwargs={'pk': self.topic.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_topic_delete_post(self):
        """測試刪除主題 - POST"""
        self.client.login(username='testuser', password='testpass123')
        topic_pk = self.topic.pk
        response = self.client.post(
            reverse('knowledge:topic_delete', kwargs={'pk': topic_pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Topic.objects.filter(pk=topic_pk).exists())


class KnowledgeItemViewTestCase(TestCase):
    """知識項目視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.topic = Topic.objects.create(
            team=self.team,
            name='測試主題'
        )
        self.item = KnowledgeItem.objects.create(
            topic=self.topic,
            title='測試項目',
            content='<p>內容</p>',
            created_by=self.user
        )
    
    def test_item_create_requires_member(self):
        """測試建立項目需要成員身份"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:item_create', kwargs={'topic_pk': self.topic.pk})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_item_create_member_access(self):
        """測試建立項目 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:item_create', kwargs={'topic_pk': self.topic.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_item_detail_member_access(self):
        """測試項目詳情 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:item_detail', kwargs={'pk': self.item.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試項目')
    
    def test_item_detail_non_member_denied(self):
        """測試項目詳情 - 非成員被拒絕"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:item_detail', kwargs={'pk': self.item.pk})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_item_update_member_access(self):
        """測試編輯項目 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:item_update', kwargs={'pk': self.item.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_item_delete_by_creator(self):
        """測試刪除項目 - 項目建立者"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:item_delete', kwargs={'pk': self.item.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_item_delete_post(self):
        """測試刪除項目 - POST"""
        self.client.login(username='testuser', password='testpass123')
        item_pk = self.item.pk
        response = self.client.post(
            reverse('knowledge:item_delete', kwargs={'pk': item_pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(KnowledgeItem.objects.filter(pk=item_pk).exists())


class CommentViewTestCase(TestCase):
    """留言視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = KnowledgeTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.topic = Topic.objects.create(
            team=self.team,
            name='測試主題'
        )
        self.item = KnowledgeItem.objects.create(
            topic=self.topic,
            title='測試項目',
            created_by=self.user
        )
        self.comment = ItemComment.objects.create(
            item=self.item,
            author=self.user,
            content='測試留言'
        )
    
    def test_add_comment_requires_post(self):
        """測試新增留言需要 POST"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('knowledge:add_comment', kwargs={'item_pk': self.item.pk})
        )
        # GET 請求會重定向
        self.assertEqual(response.status_code, 302)
    
    def test_add_comment_requires_member(self):
        """測試新增留言需要成員身份"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('knowledge:add_comment', kwargs={'item_pk': self.item.pk}),
            {'content': '新留言'}
        )
        # 非成員應被重定向
        self.assertEqual(response.status_code, 302)
    
    def test_add_comment_success(self):
        """測試新增留言 - 成功"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('knowledge:add_comment', kwargs={'item_pk': self.item.pk}),
            {'content': '新的測試留言'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ItemComment.objects.filter(content='新的測試留言').exists()
        )
    
    def test_delete_comment_by_author(self):
        """測試刪除留言 - 作者"""
        self.client.login(username='testuser', password='testpass123')
        comment_pk = self.comment.pk
        response = self.client.post(
            reverse('knowledge:delete_comment', kwargs={'pk': comment_pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ItemComment.objects.filter(pk=comment_pk).exists())
    
    def test_delete_comment_non_author_denied(self):
        """測試刪除留言 - 非作者被拒絕"""
        # 新增 other_user 為成員
        KnowledgeTeamMember.objects.create(
            team=self.team,
            user=self.other_user,
            role='member'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('knowledge:delete_comment', kwargs={'pk': self.comment.pk})
        )
        # 應被重定向，留言仍存在
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ItemComment.objects.filter(pk=self.comment.pk).exists())
