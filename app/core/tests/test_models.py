from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email="salut@modulo.fr", password="pass123"):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    def test_create_user_model(self):
        """Test creation of user model with email successful"""
        email = "paulo@modulo.fr"
        password = "TestPass1234"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_super_user_model(self):
        """Test creation of super user"""
        user = get_user_model().objects.create_superuser(
            "admin@modulo.fr",
            "passTest1234"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_new_user_email_normalized(self):
        """Test new email is normalized"""
        email = "paulo@MODULO.FR"
        user = get_user_model().objects.create_user(email, "1234")

        self.assertEqual(user.email, email.lower())

    def test_email_address_provided(self):
        """Test an error is given if user doesn't provide email address"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', "1234")

    def test_tag_str_value(self):
        """Tests that the string cast of Tag object is returned correctly"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name="Vegan"
        )

        self.assertEqual(str(tag), tag.name)
