import tempfile
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from components.models import Food, FoodCategory, RecipeBook, RecipeCategory
from .models import Ingredient, Recipe


class RecipeRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = RecipeCategory.objects.create(recipe_category_name='dinner')
        cls.food = Food.objects.create(food_name='milk', food_category=
            FoodCategory.objects.create(food_category_name='dairy'), food_aisle=None)
        cls.recipe = Recipe.objects.create(recipe_name='milk soup', recipe_category=cls.category,
                                           recipe_image='')

    def test_recipe_and_book_save_without_default_image_files(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            recipe = Recipe.objects.create(recipe_name='new soup', recipe_category=self.category)
            book = RecipeBook.objects.create(book_name='new book')
            recipe.save()
            book.save()
            self.assertEqual(recipe.recipe_name, 'New Soup')
            self.assertEqual(book.book_name, 'New Book')

    def test_create_recipe_with_image_upload(self):
        image = BytesIO()
        Image.new('RGB', (450, 400)).save(image, format='PNG')
        upload = SimpleUploadedFile('soup.png', image.getvalue(), content_type='image/png')
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            response = self.client.post(reverse('start_recipe'), {
                'recipe_name': 'new soup', 'recipe_category': self.category.pk,
                'recipe_rating': 'Excellent', 'recipe_image': upload})
            recipe = Recipe.objects.get(recipe_name='New Soup')
            self.assertRedirects(response, reverse('add_ingredients', args=[recipe.pk]))
            with Image.open(recipe.recipe_image.path) as saved:
                self.assertEqual(saved.size, (450, 400))

    def test_duplicate_recipe_does_not_create_row(self):
        self.client.post(reverse('start_recipe'), {'recipe_name': 'MILK SOUP',
            'recipe_category': self.category.pk, 'recipe_rating': 'Excellent'})
        self.assertEqual(Recipe.objects.count(), 1)

    def test_add_fractional_ingredient(self):
        response = self.client.post(reverse('add_ingredients', args=[self.recipe.pk]), {
            'ingredient_name': self.food.pk, 'whole_number_quantitiy': '1',
            'fraction_quantity': '0.5', 'quantity_unit': 'cup(s)'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.recipe.ingredients.get().ingredient_quantity, 1.5)
        self.assertEqual(self.client.post(reverse('add_ingredients', args=[self.recipe.pk]), {
            'ingredient_name': self.food.pk, 'whole_number_quantitiy': '1',
            'fraction_quantity': '0.5', 'quantity_unit': 'cup(s)'}).status_code, 200)
        self.assertEqual(self.recipe.ingredients.count(), 1)

    def test_filter_by_food_uses_ingredients_food_relation(self):
        self.recipe.ingredients.add(Ingredient.objects.create(ingredient_name=self.food,
                                   ingredient_quantity=1, quantity_unit='cup(s)'))
        Recipe.objects.create(recipe_name='other soup', recipe_category=self.category)
        response = self.client.get(reverse('recipe_list'), {'ingredients': self.food.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['recipes']), [self.recipe])

    def test_recipe_pages_render_without_image(self):
        for name, args in [('start_recipe', []), ('recipe_list', []),
                           ('recipe_detail', [self.recipe.pk]), ('recipe_update', [self.recipe.pk]),
                           ('recipe_delete', [self.recipe.pk]), ('add_ingredients', [self.recipe.pk]),
                           ('recipe_to_list', [self.recipe.pk])]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_recipe_edit_and_delete(self):
        response = self.client.post(reverse('recipe_update', args=[self.recipe.pk]), {
            'recipe_name': 'updated soup', 'recipe_category': self.category.pk,
            'recipe_rating': 'Excellent'})
        self.assertEqual(response.status_code, 302)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.recipe_name, 'Updated Soup')
        self.assertEqual(self.client.post(reverse('recipe_delete', args=[self.recipe.pk])).status_code, 302)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_invalid_ingredient_displays_errors_and_missing_recipe_is_404(self):
        response = self.client.post(reverse('add_ingredients', args=[self.recipe.pk]), {
            'ingredient_name': self.food.pk, 'whole_number_quantitiy': '0',
            'fraction_quantity': '0', 'quantity_unit': 'cup(s)'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(self.recipe.ingredients.exists())
        self.assertEqual(self.client.get(reverse('add_ingredients', args=[99999])).status_code, 404)

    def test_filtered_pagination_keeps_filter_and_limits_results(self):
        for number in range(12):
            Recipe.objects.create(recipe_name=f'Soup {number}', recipe_category=self.category)
        response = self.client.get(reverse('recipe_list'), {
            'recipe_category': self.category.pk, 'page': 2})
        self.assertEqual(len(response.context['recipes']), 3)
        self.assertContains(response, f'recipe_category={self.category.pk}&amp;page=1')

    def test_invalid_recipe_list_selection_displays_errors(self):
        response = self.client.post(reverse('recipe_to_list', args=[self.recipe.pk]),
                                    {'choose_a_list': '99999'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
