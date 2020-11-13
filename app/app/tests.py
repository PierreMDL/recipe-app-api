from django.test import TestCase

from app.calc import add, substract


class CalcTests(TestCase):
    def test_add(self):
        """Tests that numbers are correctly added"""
        self.assertEqual(add(3, 4), 7)

    def test_substract(self):
        """Tests that numbers are correctly substracted"""
        self.assertEqual(substract(11, 5), 6)
