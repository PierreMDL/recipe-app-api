from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


class PublicTagsAPITests(TestCase):
    """Tests the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required_for_tags(self):
        """Tests that authentication is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Tests the authorized user available tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="salut@modulo.fr",
            password="pass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieving_tags_successful(self):
        """Tests that retrieving tags by authenticated user is successful"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_authenticated_user(self):
        """Tests that the tags retrieved are only the user's"""
        self.user2 = get_user_model().objects.create_user(
            email="coucou@modulo.fr",
            password="mdp_acceptable"
        )
        Tag.objects.create(user=self.user2, name="Entremets")
        tag = Tag.objects.create(user=self.user, name="Barbaque")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)

    def test_tag_creation(self):
        """Tests that tags are created correctly"""
        payload = {"name": "Test tag"}
        self.client.post(TAGS_URL, payload)

        tag_exists = Tag.objects.filter(
            name=payload["name"],
            user=self.user
        ).exists()

        self.assertTrue(tag_exists)

    def test_tag_invalid_name_not_created(self):
        """Tests that a non-empty string is passed as a tag name"""
        payload = {"name": ""}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
