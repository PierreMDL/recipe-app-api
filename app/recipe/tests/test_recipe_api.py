import os
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

from PIL import Image


RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_ingredient(user, name="Cinnamon"):
    return Ingredient.objects.create(user=user, name=name)


def sample_tag(user, name="Main Course"):
    return Tag.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    default_values = {
        "title": "Sample title",
        "time_in_minutes": 15,
        "price": 5.00
    }
    default_values.update(params)

    return Recipe.objects.create(user=user, **default_values)


class PublicRecipeAPITests(TestCase):
    """Tests the API public access of the recipes"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required_for_retrieving_recipes(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Tests the API private access of the recipes"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="salut@modulo.fr",
            password="password123"
        )
        self.client.force_authenticate(self.user)

    def test_auth_user_successfully_retrieving_recipes(self):
        """Test that a user can retrieve their recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_auth_user_only_retrieves_their_own_recipes(self):
        """Test that a user can only retrieve their own recipes"""
        user2 = get_user_model().objects.create_user(
            email="test@modulo.fr",
            password="otherpass123"
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_recipe_detail_successful(self):
        """Tests that a user can retrieve a recipe's detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        res = self.client.get(detail_url(recipe_id=recipe.id))
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_creating_recipe_successful(self):
        """Tests that a user can create a recipe"""
        payload = {
            "title": "Chocolate cheesecake",
            "price": 5.00,
            "time_in_minutes": 30
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_adding_tags_successful(self):
        """Test that a user can add tags to their recipe"""
        tag1 = sample_tag(user=self.user)
        tag2 = sample_tag(user=self.user)
        payload = {
            "title": "Avocado cheesecake",
            "price": 20.00,
            "time_in_minutes": 45,
            "tags": [tag1.id, tag2.id]
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_adding_ingredients_successful(self):
        """Tests that a user can add ingredients to their recipe"""
        ingredient1 = sample_ingredient(user=self.user)
        ingredient2 = sample_ingredient(user=self.user)
        payload = {
            "title": "Red curry prawns soup",
            "price": 25.00,
            "time_in_minutes": 15,
            "ingredients": [ingredient1.id, ingredient2.id]
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_recipe_update_successful(self):
        """Test that a partial recipe update is successful using patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Chicken")

        payload = {
            "title": "Chicken Massala",
            "tags": [new_tag.id]
        }

        self.client.patch(detail_url(recipe_id=recipe.id), payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_recipe_update_successful(self):
        """Test that a full recipe update is successful using put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            "title": "Spaghetti Carbonara",
            "time_in_minutes": 12,
            "price": 7.50
        }

        self.client.put(detail_url(recipe_id=recipe.id), payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.time_in_minutes, payload["time_in_minutes"])
        self.assertEqual(recipe.price, payload["price"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)


class RecipeUploadImageTests(TestCase):
    """Tests upload of images for the recipes"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="salut@modulo.fr",
            password="password123"
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe_successful(self):
        """Test that a valid image can be uploaded successfully"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_image_fails(self):
        """Test that an invalid image cannot be uploaded"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {"image": "notimage"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Tests that the filters by tags works"""
        recipe1 = sample_recipe(user=self.user, title="Red thai curry")
        tag1 = sample_tag(user=self.user, name="Vegan")
        recipe1.tags.add(tag1)
        recipe2 = sample_recipe(user=self.user, title="Aubergine with tahini")
        tag2 = sample_tag(user=self.user, name="Vegetarian")
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title="Steak and mushrooms")

        res = self.client.get(
            RECIPES_URL,
            {"tags": f"{tag1.id},{tag2.id}"}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Tests that the filters by ingredients works"""
        recipe1 = sample_recipe(user=self.user, title="Posh beans on toast")
        ingredient1 = sample_ingredient(user=self.user, name="Feta cheese")
        recipe1.ingredients.add(ingredient1)
        recipe2 = sample_recipe(user=self.user, title="Chicken Cacciatore")
        ingredient2 = sample_ingredient(user=self.user, name="Chicken")
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title="Fish and chips")

        res = self.client.get(
            RECIPES_URL,
            {"ingredients": f"{ingredient1.id},{ingredient2.id}"}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
