from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test the user API client (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Tests creating user with valid payload is successful"""
        payload = {
            "email": "salut@modulo.fr",
            "password": "Test123",
            "name": "Salut Toto"
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_already_exists(self):
        """Tests creating a user that already exists fails"""
        payload = {
            "email": "salut@modulo.fr",
            "password": "Crucru",
            "name": "Salut Couz"
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Tests creating user with password under 5 chars fails"""
        payload = {
            "email": "salut@modulo.fr",
            "password": "pw",
            "name": "Salut Monga"
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload["email"]
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Tests correct credentials result in token creation"""
        payload = {
            "email": "salut@modulo.fr",
            "password": "password123"
        }
        create_user(**payload)

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Tests incorrect credentials doesn't result in token creation"""
        create_user(email="salut@modulo.fr", password="password123")
        payload = {
            "email": "salut@modulo.fr",
            "password": "wrongpass",
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_unknown_user(self):
        """Tests unknown user doesn't result in token creation"""
        payload = {
            "email": "salut@modulo.fr",
            "password": "password123"
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_password_given(self):
        """Tests no password given doesn't result in token creation"""
        payload = {
            "email": "salut@modulo.fr",
            "password": ""
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Tests that authorization is required for user view"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Tests the user API Client that requires authentification"""

    def setUp(self):
        self.user = create_user(
            email="salut@modulo.fr",
            password="password123",
            name="Michel Salut"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_is_successful(self):
        """Tests authenticated user can retrieve profile successfully"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            "name": self.user.name,
            "email": self.user.email
        })

    def test_post_not_allowed_on_me(self):
        """Tests that POST method is not allowed on me url"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_successful(self):
        """Tests that an authenticated user can update their profile"""
        payload = {"name": "Michelle Salut", "password": "newpass123"}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
