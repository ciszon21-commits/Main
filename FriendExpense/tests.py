from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import ExpenseGroup, Member, Expense, ExpenseItem

class ExpenseItemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        self.group = ExpenseGroup.objects.create(name='Test Group', created_by=self.user)
        self.member1 = Member.objects.create(group=self.group, name='Member1')
        self.member2 = Member.objects.create(group=self.group, name='Member2')

    def test_create_expense_with_items(self):
        url = reverse('friend_expense:expense_create', kwargs={'group_pk': self.group.pk})
        data = {
            'description': 'Test Expense',
            'amount': '30.00',
            'paid_by': self.member1.pk,
            'expense_date': '2023-10-01T12:00',
            'split_members': [self.member1.pk, self.member2.pk],
            'split_equally': 'on',
            'item_names[]': ['Item A', 'Item B'],
            'item_amounts[]': ['10.00', '20.00']
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) # Should redirect
        
        # Check expense created
        expense = Expense.objects.first()
        self.assertIsNotNone(expense)
        self.assertEqual(expense.description, 'Test Expense')
        self.assertEqual(expense.amount, 30.00)
        
        # Check items created
        items = expense.items.all().order_by('name')
        self.assertEqual(items.count(), 2)
        self.assertEqual(items[0].name, 'Item A')
        self.assertEqual(items[0].amount, 10.00)
        self.assertEqual(items[1].name, 'Item B')
        self.assertEqual(items[1].amount, 20.00)

    def test_update_expense_with_items(self):
        # Create initial expense
        expense = Expense.objects.create(
            group=self.group,
            paid_by=self.member1,
            description='Old Expense',
            amount=10.00
        )
        ExpenseItem.objects.create(expense=expense, name='Old Item', amount=10.00)
        
        url = reverse('friend_expense:expense_update', kwargs={'pk': expense.pk})
        data = {
            'description': 'Updated Expense',
            'amount': '50.00',
            'paid_by': self.member1.pk,
            'expense_date': '2023-10-01T12:00',
            'split_members': [self.member1.pk],
            'split_equally': 'on',
            'item_names[]': ['New Item A', 'New Item B'],
            'item_amounts[]': ['25.00', '25.00']
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Reload expense
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 50.00)
        
        # Check items updated
        items = expense.items.all().order_by('name')
        self.assertEqual(items.count(), 2)
        self.assertEqual(items[0].name, 'New Item A')
        self.assertEqual(items[0].amount, 25.00)
        self.assertEqual(items[1].name, 'New Item B')
        self.assertEqual(items[1].amount, 25.00)

    def test_view_pages_render(self):
        """Test that key pages render without errors"""
        # Group list
        response = self.client.get(reverse('friend_expense:group_list'))
        self.assertEqual(response.status_code, 200)

        # Group detail
        response = self.client.get(reverse('friend_expense:group_detail', kwargs={'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group')

        # Expense create
        response = self.client.get(reverse('friend_expense:expense_create', kwargs={'group_pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Create an expense for testing update view
        expense = Expense.objects.create(
            group=self.group,
            paid_by=self.member1,
            description='Render Test Expense',
            amount=100.00
        )
        
        # Expense update
        response = self.client.get(reverse('friend_expense:expense_update', kwargs={'pk': expense.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Render Test Expense')
