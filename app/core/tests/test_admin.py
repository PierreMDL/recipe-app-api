from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_super_user(
            email="paulo@modulo.fr",
            password="test1234"
        )
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email="test@toutou.fr",
            password="cucou",
            name="Test utilisateur"
        )

    def test_users_listed(self):
        """Tests that users are correctly listed on user page"""
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.email)
        self.assertContains(res, self.user.name)

    def test_user_change_page(self):
        """Tests that the user edit page works"""
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_user_add_page(self):
        """Tests that the user add page works"""
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
