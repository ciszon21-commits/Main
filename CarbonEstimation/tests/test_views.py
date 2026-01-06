import json
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from CarbonEstimation.models import MainCategory, ComponentItem, Scenario, ScenarioData

@override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = MainCategory.objects.create(code="T01", name="Test Cat")
        self.item = ComponentItem.objects.create(
            category=self.category,
            item_no="T1001",
            work_item="Test Item",
            unit="kg"
        )
        self.scenario = Scenario.objects.create(
            project_number="P-Test",
            project_name="Test Project",
            scenario_name="Test Scenario",
            creator=self.user
        )

    def test_calculator_view(self):
        response = self.client.get(reverse('calculator'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'carbon_estimation/calculator.html')
        self.assertIn('data', response.context)

    def test_create_scenario_api(self):
        url = reverse('create_scenario')
        data = {
            'project_number': 'NEW-001',
            'project_name': 'New Project',
            'scenario_name': 'New Scenario',
            'category_id': self.category.id,
            'data': [
                {'component_item_id': self.item.id, 'quantity': 100}
            ]
        }
        
        # Test anonymous creation
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Scenario.objects.filter(project_number='NEW-001').exists())
        
        # Test authenticated creation
        self.client.force_login(self.user)
        data['project_number'] = 'NEW-002'
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        scenario = Scenario.objects.get(project_number='NEW-002')
        self.assertEqual(scenario.creator, self.user)
        self.assertTrue(ScenarioData.objects.filter(scenario=scenario).exists())

    def test_save_category_data_api(self):
        url = reverse('save_category', args=[self.scenario.id])
        data = {
            'category_id': self.category.id,
            'data': [
                {'component_item_id': self.item.id, 'quantity': 200}
            ]
        }
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        scenario_data = ScenarioData.objects.get(scenario=self.scenario, component_item=self.item)
        self.assertEqual(scenario_data.quantity, 200)

    def test_update_scenario_api(self):
        self.client.force_login(self.user)
        url = reverse('update_scenario', args=[self.scenario.id])
        data = {
            'scenario_name': 'Updated Name'
        }
        response = self.client.put(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.scenario_name, 'Updated Name')

    def test_update_scenario_permission(self):
        other_user = User.objects.create_user(username='other', password='password')
        self.client.force_login(other_user)
        url = reverse('update_scenario', args=[self.scenario.id])
        data = {'scenario_name': 'Hacker Update'}
        response = self.client.put(
            url,
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_scenario_api(self):
        self.client.force_login(self.user)
        url = reverse('delete_scenario', args=[self.scenario.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Scenario.objects.filter(id=self.scenario.id).exists())

    def test_load_scenario_api(self):
        ScenarioData.objects.create(
            scenario=self.scenario,
            category=self.category,
            component_item=self.item,
            quantity=10.0
        )
        url = reverse('load_scenario', args=[self.scenario.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['scenario']['id'], self.scenario.id)
        self.assertIn(str(self.item.id), data['data'])

    def test_manage_collaborators_api(self):
        other_user = User.objects.create_user(username='other', password='password')
        self.client.force_login(self.user)
        url = reverse('manage_collaborators', args=[self.scenario.id])
        
        # Add collaborator
        response = self.client.post(
            url,
            json.dumps({'action': 'add', 'username': 'other'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(other_user, self.scenario.collaborators.all())

        # Remove collaborator
        response = self.client.post(
            url,
            json.dumps({'action': 'remove', 'username': 'other'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_user, self.scenario.collaborators.all())

    def test_scenario_list_view(self):
        response = self.client.get(reverse('home')) # 'home' is mapped to scenario_list in CarbonEstimation/urls.py
        self.assertEqual(response.status_code, 200)
        # Assuming scenario_list.html renders a list
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.scenario, response.context['scenarios'])

    def test_search_users(self):
        self.client.force_login(self.user)
        other_user = User.objects.create_user(username='searchtarget', password='password')
        url = reverse('search_users')
        response = self.client.get(url, {'q': 'search'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['users']), 1)
        self.assertEqual(data['users'][0]['username'], 'searchtarget')
