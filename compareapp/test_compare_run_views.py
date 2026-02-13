from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CompareProject, ComparisonMatch, ComparisonRun, GlobalKeyword, ProjectAccess


class ComparisonRunViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass12345',
        )
        self.client.force_login(self.owner)

    def test_project_index_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('compareapp:project_index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_compare_run_status_endpoint_returns_json_payload(self):
        project = CompareProject.objects.create(name='P1', plan_number='A-001', owner=self.owner)
        run = ComparisonRun.objects.create(
            project=project,
            status=ComparisonRun.Status.PENDING,
            quantity_tolerance=Decimal('0.01'),
            fuzzy_threshold=0.8,
            weighted_threshold=0.75,
        )

        url = reverse(
            'compareapp:compare_run_status',
            kwargs={'project_id': project.id, 'run_id': run.id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['run_id'], run.id)
        self.assertEqual(payload['status'], ComparisonRun.Status.PENDING)
        self.assertIn('detail_url', payload)

    def test_compare_match_annotation_endpoint_updates_verdict_and_note(self):
        project = CompareProject.objects.create(name='P2', plan_number='A-002', owner=self.owner)
        run = ComparisonRun.objects.create(
            project=project,
            status=ComparisonRun.Status.COMPLETED,
            quantity_tolerance=Decimal('0.01'),
            fuzzy_threshold=0.8,
            weighted_threshold=0.75,
        )
        match = ComparisonMatch.objects.create(
            run=run,
            method='weighted',
            rank=1,
            left_source_id='xml-1',
            right_source_id='sheet-1',
            left_name='Steel Bar',
            right_name='Steel Reinforcement',
            score=0.9,
            name_score=0.9,
            unit_score=1.0,
            quantity_score=1.0,
        )

        url = reverse(
            'compareapp:compare_match_annotation',
            kwargs={
                'project_id': project.id,
                'run_id': run.id,
                'match_id': match.id,
            },
        )
        response = self.client.post(
            url,
            data={'verdict': ComparisonMatch.Verdict.CORRECT, 'note': '人工確認 OK'},
        )

        self.assertEqual(response.status_code, 200)
        match.refresh_from_db()
        self.assertEqual(match.verdict, ComparisonMatch.Verdict.CORRECT)
        self.assertEqual(match.note, '人工確認 OK')

    def test_keyword_add_endpoint_creates_and_reuses_global_keyword(self):
        project = CompareProject.objects.create(name='P3', plan_number='A-003', owner=self.owner)
        url = reverse(
            'compareapp:keyword_add',
            kwargs={'project_id': project.id},
        )

        first = self.client.post(url, data={'term': '鋼筋', 'source': 'budget'})
        self.assertEqual(first.status_code, 200)
        first_payload = first.json()
        self.assertTrue(first_payload['created'])

        second = self.client.post(url, data={'term': '鋼筋', 'source': 'quantity'})
        self.assertEqual(second.status_code, 200)
        second_payload = second.json()
        self.assertFalse(second_payload['created'])

        keyword = GlobalKeyword.objects.get(normalized_term='鋼筋')
        self.assertEqual(keyword.selected_count, 2)
        self.assertTrue(keyword.is_active)

    def test_global_keyword_manage_page_supports_add_and_toggle(self):
        list_url = reverse('compareapp:global_keyword_manage')

        page = self.client.get(list_url)
        self.assertEqual(page.status_code, 200)

        add_response = self.client.post(
            list_url,
            data={
                'action': 'add',
                'term': '混凝土',
            },
        )
        self.assertEqual(add_response.status_code, 200)

        keyword = GlobalKeyword.objects.get(normalized_term='混凝土')
        self.assertTrue(keyword.is_active)

        toggle_response = self.client.post(
            list_url,
            data={
                'action': 'toggle',
                'keyword_id': keyword.id,
            },
        )
        self.assertEqual(toggle_response.status_code, 200)

        keyword.refresh_from_db()
        self.assertFalse(keyword.is_active)

    def test_project_index_only_shows_owned_or_shared_projects(self):
        user_model = get_user_model()
        other_user = user_model.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass12345',
        )
        shared_user = user_model.objects.create_user(
            username='shared',
            email='shared@example.com',
            password='pass12345',
        )

        own_project = CompareProject.objects.create(
            name='My Project',
            plan_number='PRJ-MY',
            owner=self.owner,
        )
        shared_project = CompareProject.objects.create(
            name='Shared Project',
            plan_number='PRJ-SHARED',
            owner=other_user,
        )
        hidden_project = CompareProject.objects.create(
            name='Hidden Project',
            plan_number='PRJ-HIDDEN',
            owner=other_user,
        )
        ProjectAccess.objects.create(
            project=shared_project,
            user=self.owner,
            role=ProjectAccess.Role.VIEWER,
        )

        response = self.client.get(reverse('compareapp:project_index'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn(own_project.name, content)
        self.assertIn(shared_project.name, content)
        self.assertNotIn(hidden_project.name, content)

        self.client.force_login(shared_user)
        response2 = self.client.get(reverse('compareapp:project_index'))
        content2 = response2.content.decode('utf-8')
        self.assertNotIn(own_project.name, content2)
        self.assertNotIn(shared_project.name, content2)

    def test_project_access_manage_can_share_project_to_other_user(self):
        user_model = get_user_model()
        target_user = user_model.objects.create_user(
            username='member1',
            email='member1@example.com',
            password='pass12345',
        )
        project = CompareProject.objects.create(
            name='P4',
            plan_number='A-004',
            owner=self.owner,
        )
        manage_url = reverse('compareapp:project_access_manage', kwargs={'project_id': project.id})

        add_response = self.client.post(
            manage_url,
            data={
                'action': 'add',
                'user_identity': target_user.username,
                'role': ProjectAccess.Role.EDITOR,
            },
        )
        self.assertEqual(add_response.status_code, 200)
        access = ProjectAccess.objects.get(project=project, user=target_user)
        self.assertEqual(access.role, ProjectAccess.Role.EDITOR)

        self.client.force_login(target_user)
        detail_url = reverse('compareapp:project_detail', kwargs={'project_id': project.id})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)

    def test_non_owner_cannot_manage_project_access(self):
        user_model = get_user_model()
        owner2 = user_model.objects.create_user(
            username='owner2',
            email='owner2@example.com',
            password='pass12345',
        )
        outsider = user_model.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='pass12345',
        )
        project = CompareProject.objects.create(
            name='P5',
            plan_number='A-005',
            owner=owner2,
        )
        ProjectAccess.objects.create(
            project=project,
            user=self.owner,
            role=ProjectAccess.Role.VIEWER,
        )

        manage_url = reverse('compareapp:project_access_manage', kwargs={'project_id': project.id})
        forbidden_response = self.client.get(manage_url)
        self.assertEqual(forbidden_response.status_code, 403)

        self.client.force_login(outsider)
        hidden_response = self.client.get(manage_url)
        self.assertEqual(hidden_response.status_code, 404)
