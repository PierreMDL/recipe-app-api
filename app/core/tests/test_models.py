from django.test import TestCase
from django.contrib.auth import get_user_model


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
