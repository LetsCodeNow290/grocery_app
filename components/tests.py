from django.test import TestCase
from django.urls import reverse
from .models import Aisle, Food, FoodCategory, RecipeBook, RecipeCategory


class CatalogRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aisle = Aisle.objects.create(aisle_name='1')
        cls.category = FoodCategory.objects.create(food_category_name='dairy')
        cls.food = Food.objects.create(food_name='milk', food_category=cls.category, food_aisle=cls.aisle)
        cls.book = RecipeBook.objects.create(book_name='family book', recipe_book_image='')
        cls.recipe_category = RecipeCategory.objects.create(recipe_category_name='dinner')

    def test_catalog_pages_render(self):
        for prefix, obj in [('aisle', self.aisle), ('food', self.food),
                            ('food_cat', self.category), ('recipe_book', self.book),
                            ('recipe_cat', self.recipe_category)]:
            for name, args in [(prefix, []), (prefix + '_list', []),
                               (prefix + '_update', [obj.pk]), (prefix + '_delete', [obj.pk])]:
                with self.subTest(name=name):
                    self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_create_and_update_food(self):
        response = self.client.post(reverse('food'), {'food_name': 'cream',
            'food_category': self.category.pk, 'food_aisle': self.aisle.pk})
        self.assertEqual(response.status_code, 302)
        food = Food.objects.get(food_name='Cream')
        response = self.client.post(reverse('food_update', args=[food.pk]), {
            'food_name': 'heavy cream', 'food_category': self.category.pk, 'food_aisle': ''})
        self.assertEqual(response.status_code, 302)
        food.refresh_from_db()
        self.assertEqual(food.food_name, 'Heavy Cream')
        self.assertIsNone(food.food_aisle)

    def test_duplicate_food_shows_error(self):
        response = self.client.post(reverse('food'), {'food_name': 'MILK',
            'food_category': self.category.pk, 'food_aisle': self.aisle.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Food.objects.count(), 1)
