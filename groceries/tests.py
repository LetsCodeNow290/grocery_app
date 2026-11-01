import csv
import io
from datetime import date
from django.test import TestCase
from django.urls import reverse
from components.models import Aisle, Food, FoodCategory, RecipeCategory
from recipes.models import Ingredient, Recipe
from .models import ChooseItem, GroceryList, GroceryListItems
from .services import add_item, add_recipe


class GroceryWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = FoodCategory.objects.create(food_category_name='produce')
        cls.aisle = Aisle.objects.create(aisle_name='2')
        cls.food = Food.objects.create(food_name='tomatoes', food_category=cls.category,
                                       food_aisle=cls.aisle)
        cls.recipe = Recipe.objects.create(recipe_name='soup', recipe_category=
            RecipeCategory.objects.create(recipe_category_name='dinner'))
        cls.recipe.ingredients.add(Ingredient.objects.create(
            ingredient_name=cls.food, ingredient_quantity=1.5, quantity_unit='cup(s)'))
        cls.grocery_list = GroceryList.objects.create(list_name=date(2026, 11, 1))

    def test_create_list_once(self):
        response = self.client.post(reverse('choose_list'), {'list_name': '2026-11-08'})
        self.assertEqual(GroceryList.objects.count(), 2)
        self.assertRedirects(response, reverse('add_to_list', args=[GroceryList.objects.latest('pk').pk]))

    def test_invalid_list_displays_errors(self):
        response = self.client.post(reverse('choose_list'), {'list_name': 'invalid'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['new_list_form'].errors)
        self.assertEqual(GroceryList.objects.count(), 1)

    def test_manual_items_merge_without_orphans(self):
        url = reverse('add_to_list', args=[self.grocery_list.pk])
        data = {'item_name': self.food.pk, 'item_quantity': '0.75', 'item_quantity_unit': 'cup(s)'}
        for _ in range(2):
            self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(ChooseItem.objects.count(), 1)
        self.assertEqual(self.grocery_list.list_items.get().item_quantity, 1.5)

    def test_invalid_item_renders_bound_form(self):
        response = self.client.post(reverse('add_to_list', args=[self.grocery_list.pk]),
                                    {'item_quantity': '-1'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['item_form'].errors)
        self.assertFalse(ChooseItem.objects.exists())

    def test_recipe_adds_ingredients_from_both_entry_points_once(self):
        self.client.post(reverse('recipe_to_list', args=[self.recipe.pk]),
                         {'choose_a_list': self.grocery_list.pk})
        self.client.post(reverse('add_to_list', args=[self.grocery_list.pk]),
                         {'list_recipes': self.recipe.pk})
        self.assertEqual(self.grocery_list.list_items.get().item_quantity, 1.5)
        self.assertEqual(self.grocery_list.list_recipes.count(), 1)
        self.assertEqual(ChooseItem.objects.count(), 1)

    def test_recipe_form_entry_adds_ingredients(self):
        response = self.client.post(reverse('add_to_list', args=[self.grocery_list.pk]),
                                    {'list_recipes': self.recipe.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.grocery_list.list_items.get().item_quantity, 1.5)

    def test_recipe_merges_with_manual_item(self):
        add_item(self.grocery_list, self.food, 2, 'cup(s)')
        add_recipe(self.grocery_list, self.recipe)
        self.assertEqual(self.grocery_list.list_items.get().item_quantity, 3.5)

    def test_units_are_kept_separate(self):
        add_item(self.grocery_list, self.food, 1, 'pound(s)')
        add_recipe(self.grocery_list, self.recipe)
        self.assertEqual(len(self.grocery_list.make_list()), 2)

    def test_legacy_join_table_and_duplicate_aggregation(self):
        for quantity in [0.5, 1]:
            item = ChooseItem.objects.create(item_name=self.food, item_quantity=quantity,
                                             item_quantity_unit='cup(s)')
            GroceryListItems.objects.create(grocery_list=self.grocery_list, choose_item=item)
        self.assertEqual(self.grocery_list.make_list()[0]['quantity'], 1.5)
        self.assertEqual(GroceryListItems._meta.db_table, 'groceries_grocerylistitems')

    def test_missing_aisle_and_natural_sort(self):
        aisle10 = Aisle.objects.create(aisle_name='10')
        for name, aisle in [('zucchini', aisle10), ('apple', None)]:
            food = Food.objects.create(food_name=name, food_category=self.category, food_aisle=aisle)
            add_item(self.grocery_list, food, 1, 'other')
        add_recipe(self.grocery_list, self.recipe)
        self.assertEqual([x['aisle'] for x in self.grocery_list.make_list()], ['2', '10', 'Unassigned'])

    def test_csv_preserves_fractional_quantities(self):
        add_recipe(self.grocery_list, self.recipe)
        response = self.client.get(reverse('print_list', args=[self.grocery_list.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].endswith('List.csv"'))
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertIn(['2', 'Tomatoes', '1.5 cup(s)'], rows)
        self.assertIn(['Soup'], rows)

    def edit_data(self, item, quantity='4', delete=None):
        data = {'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '1',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-id': str(item.pk), 'form-0-item_quantity': quantity}
        if delete:
            data['delete'] = str(delete)
        return data

    def test_edit_quantity(self):
        item = add_item(self.grocery_list, self.food, 1, 'other')
        response = self.client.post(reverse('grocery_detail_and_remove', args=[self.grocery_list.pk]),
                                    self.edit_data(item))
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.item_quantity, 4)

    def test_invalid_edit_shows_errors(self):
        item = add_item(self.grocery_list, self.food, 1, 'other')
        response = self.client.post(reverse('grocery_detail_and_remove', args=[self.grocery_list.pk]),
                                    self.edit_data(item, quantity='-1'))
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.item_quantity, 1)

    def test_cannot_delete_another_lists_item(self):
        own = add_item(self.grocery_list, self.food, 1, 'other')
        other_list = GroceryList.objects.create(list_name=date(2026, 11, 2))
        other = add_item(other_list, self.food, 2, 'other')
        self.client.post(reverse('grocery_detail_and_remove', args=[self.grocery_list.pk]),
                         self.edit_data(own, delete=other.pk))
        self.assertTrue(other_list.list_items.filter(pk=other.pk).exists())

    def test_remove_item(self):
        item = add_item(self.grocery_list, self.food, 1, 'other')
        self.client.post(reverse('grocery_detail_and_remove', args=[self.grocery_list.pk]),
                         self.edit_data(item, delete=item.pk))
        self.assertFalse(ChooseItem.objects.filter(pk=item.pk).exists())

    def test_shared_legacy_item_survives_removal(self):
        item = add_item(self.grocery_list, self.food, 1, 'other')
        other_list = GroceryList.objects.create(list_name=date(2026, 11, 2))
        other_list.list_items.add(item)
        self.client.post(reverse('grocery_detail_and_remove', args=[self.grocery_list.pk]),
                         self.edit_data(item, delete=item.pk))
        self.assertTrue(other_list.list_items.filter(pk=item.pk).exists())

    def test_shared_legacy_item_is_copied_before_addition_or_edit(self):
        item = add_item(self.grocery_list, self.food, 1, 'other')
        other_list = GroceryList.objects.create(list_name=date(2026, 11, 2))
        other_list.list_items.add(item)
        add_item(self.grocery_list, self.food, 2, 'other')
        item.refresh_from_db()
        self.assertEqual(item.item_quantity, 1)
        self.assertEqual(self.grocery_list.list_items.get().item_quantity, 3)
        # Re-share to exercise the quantity editor's copy behavior.
        self.grocery_list.list_items.clear()
        self.grocery_list.list_items.add(item)
        self.client.post(reverse('grocery_detail_and_remove', args=[self.grocery_list.pk]),
                         self.edit_data(item))
        item.refresh_from_db()
        self.assertEqual(item.item_quantity, 1)
        self.assertEqual(self.grocery_list.list_items.get().item_quantity, 4)

    def test_missing_list_returns_404(self):
        for name in ['add_to_list', 'print_list', 'grocery_detail_and_remove']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=[99999])).status_code, 404)

    def test_grocery_pages_render(self):
        add_recipe(self.grocery_list, self.recipe)
        for name, args in [('home', []), ('home_admin', []), ('choose_list', []),
                           ('add_to_list', [self.grocery_list.pk]),
                           ('grocery_detail_and_remove', [self.grocery_list.pk])]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)
