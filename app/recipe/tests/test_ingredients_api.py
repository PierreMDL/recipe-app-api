from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


class PublicIngredientsAPITests(TestCase):
    """Tests the public access to ingredient API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required_for_ingredients(self):
        """Test that authentication is required for retrieving ingr list"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Tests the private access to ingredient API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="salut@modulo.fr",
            password="testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_auth_user_retrieving_ingredients(self):
        """Tests that an authenticated user's ingredients can be retrieved"""
        Ingredient.objects.create(user=self.user, name="Salt")
        Ingredient.objects.create(user=self.user, name="Turmeric")

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_only_auth_user_ingredients_retrieved(self):
        """Tests that only auth user's ingredients are retrieved"""
        self.user2 = get_user_model().objects.create_user(
            email="test@modulo.fr",
            password="other123"
        )
        Ingredient.objects.create(user=self.user2, name="Kale")
        ingredient = Ingredient.objects.create(user=self.user, name="Newt")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)

    def test_user_creates_ingredient_successful(self):
        """Tests that a user can successfully create an ingredient"""
        payload = {"name": "Rhubarb"}
        self.client.post(INGREDIENTS_URL, payload)
        ingredient_exists = Ingredient.objects.all().filter(
            user=self.user,
            name=payload["name"]
        ).exists()

        self.assertTrue(ingredient_exists)

    def test_ingredient_blank_name_fails(self):
        """Tests that the user cannot enter a blank name for the ingredient"""
        payload = {"name": ""}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
