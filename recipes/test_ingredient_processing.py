from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from components.models import Food, FoodCategory, Aisle, RecipeCategory
from groceries.models import GroceryList, ChooseItem
from groceries.services import add_item, add_recipe
from .ingredient_processing import parse_ingredient, normalize_food_name, ingredient_lines, parse_quantity
from .ingredient_review import matching_formset, save_ingredient_review
from .models import Recipe, Ingredient
from .test_support import reviewed_payload


class ParsingTests(SimpleTestCase):
    def test_fractions_decimals_mixed_and_joined_metric(self):
        cases = [('½ cup flour', .5, 'cup(s)', 'flour'),
                 ('1½ cups flour', 1.5, 'cup(s)', 'flour'),
                 ('1 1/2 c. flour', 1.5, 'cup(s)', 'flour'),
                 ('1-1/2 cups flour', 1.5, 'cup(s)', 'flour'),
                 ('⅔ tsp. salt', 2/3, 'teaspoon(s)', 'salt'),
                 ('.25 tbsp butter', .25, 'TABLESPOON(s)', 'butter'),
                 ('2 T butter', 2, 'TABLESPOON(s)', 'butter'),
                 ('2 t salt', 2, 'teaspoon(s)', 'salt'),
                 ('250g flour', 250, 'gram(s)', 'flour'),
                 ('1.5 kg potatoes', 1.5, 'kilogram(s)', 'potatoes'),
                 ('200 ml milk', 200, 'milliliter(s)', 'milk'),
                 ('1 litre water', 1, 'liter(s)', 'water'),
                 ('2 fl oz milk', 2, 'fluid ounce(s)', 'milk'),
                 ('two tablespoons butter', 2, 'TABLESPOON(s)', 'butter'),
                 ('a pinch of salt', 1, 'pinch(es)', 'salt')]
        for text, amount, unit, food in cases:
            with self.subTest(text=text):
                parsed = parse_ingredient(text)
                self.assertAlmostEqual(parsed['quantity'], amount)
                self.assertEqual(parsed['unit'], unit)
                self.assertEqual(parsed['food_name'], food)
                self.assertEqual(parsed['original_text'], text)

    def test_ranges_keep_both_bounds_and_are_flagged(self):
        for text, low, high in [('1–2 cups flour', 1, 2), ('1/2 to 3/4 tsp salt', .5, .75),
                                ('1 1/2-2 tbsp butter', 1.5, 2)]:
            with self.subTest(text=text):
                parsed = parse_ingredient(text)
                self.assertEqual((parsed['quantity'], parsed['quantity_max']), (low, high))
                self.assertTrue(parsed['warnings'])

    def test_invalid_and_unknown_quantities_are_not_guessed(self):
        for text in ['salt, to taste', '0 cups flour', '1/0 cup milk', '3-1 cups milk',
                     'a few carrots', '1,5 cups flour', '-1 cup flour']:
            with self.subTest(text=text):
                parsed = parse_ingredient(text)
                self.assertIsNone(parsed['quantity'])
                self.assertTrue(parsed['warnings'])
                self.assertEqual(parsed['original_text'], text)

    def test_preparation_package_and_count_descriptions_are_preserved(self):
        parsed = parse_ingredient('2 (14 ounce) cans tomatoes, drained')
        self.assertEqual(parsed['food_name'], 'tomatoes')
        self.assertEqual(parsed['unit'], 'can(s)')
        self.assertIn('14 ounce', parsed['preparation_notes'])
        self.assertIn('drained', parsed['preparation_notes'])
        self.assertTrue(parsed['warnings'])
        parsed = parse_ingredient('1 cup finely chopped onions')
        self.assertEqual(parsed['food_name'], 'onions')
        self.assertIn('finely chopped', parsed['preparation_notes'])
        parsed = parse_ingredient('2 large eggs')
        self.assertEqual(parsed['food_name'], 'eggs')
        self.assertEqual(parsed['unit'], 'item(s)')
        self.assertIn('large', parsed['preparation_notes'])

    def test_approximate_and_additional_amounts_are_flagged(self):
        for text in ['about 1 cup flour', '1 cup flour plus more for dusting', '1 cup flour, plus extra']:
            parsed=parse_ingredient(text)
            self.assertEqual(parsed['quantity'],1)
            self.assertEqual(parsed['food_name'],'flour')
            self.assertTrue(parsed['warnings'])
            self.assertTrue(parsed['preparation_notes'])

    def test_normalization_is_conservative(self):
        for a,b in [('  Chicken - Breasts ', 'chicken breast'), ('Tomatoes', 'tomato'),
                    ('Crème fraîche', 'creme fraiche'), ("Confectioners’ sugar", 'confectioners sugar')]:
            self.assertEqual(normalize_food_name(a), normalize_food_name(b))
        for a,b in [('salted butter','unsalted butter'), ('bread flour','flour'), ('asparagus','asparagu')]:
            self.assertNotEqual(normalize_food_name(a), normalize_food_name(b))

    def test_manual_quantity_corrections_allow_fractions(self):
        for text, number in [('½', .5), ('1½', 1.5), ('1 1/2', 1.5), ('.5', .5)]:
            self.assertEqual(parse_quantity(text), number)
        for text in ['nan','inf','1/0','-1','0','1-2']:
            with self.assertRaises((ValueError, ZeroDivisionError)):
                parse_quantity(text)

    def test_line_limit_rejects_instead_of_truncating(self):
        with self.assertRaisesRegex(ValueError,'200'):
            ingredient_lines('\n'.join('1 cup flour' for _ in range(201)))


class IngredientReviewTests(TestCase):
    def setUp(self):
        self.category = FoodCategory.objects.create(food_category_name='baking')
        self.flour = Food.objects.create(food_name='flour', food_category=self.category, food_aisle=None)
        self.url = reverse('recipe_import')

    def payload(self, text='1 cup flour\n½ cup flour'):
        return reviewed_payload({'step':'save', 'recipe_name':'Imported meal',
            'recipe_category':'', 'source_url':'https://recipes.example/meal',
            'ingredient_text':text, 'recipe_instructions':'Mix and cook.'})

    def test_save_matches_existing_and_grocery_flow_needs_no_reentry(self):
        response = self.client.post(self.url, self.payload())
        recipe = Recipe.objects.get()
        self.assertRedirects(response, reverse('recipe_detail', args=[recipe.pk]))
        self.assertEqual(recipe.ingredients.count(),2)
        self.assertEqual(Food.objects.count(),1)
        self.assertEqual(recipe.ingredients.first().original_text,'1 cup flour')
        grocery_list = GroceryList.objects.create(list_name='2026-11-02')
        response = self.client.post(reverse('recipe_to_list',args=[recipe.pk]),{'choose_a_list':grocery_list.pk})
        self.assertEqual(response.status_code,302)
        self.assertEqual(grocery_list.list_items.get().item_quantity,1.5)
        self.client.post(reverse('add_to_list',args=[grocery_list.pk]),{'list_recipes':recipe.pk})
        self.assertEqual(grocery_list.list_items.get().item_quantity,1.5)

    def test_new_food_created_once_and_optional_category_aisle_used(self):
        aisle = Aisle.objects.create(aisle_name='3')
        data = self.payload('1 tbsp butter\n2 tablespoons butter')
        for i in range(2):
            data[f'ingredients-{i}-new_food_category'] = self.category.pk
            data[f'ingredients-{i}-new_food_aisle'] = aisle.pk
        self.client.post(self.url,data)
        butter = Food.objects.get(food_name='Butter')
        self.assertEqual(butter.food_category,self.category)
        self.assertEqual(butter.food_aisle,aisle)
        self.assertEqual(Food.objects.filter(food_name='Butter').count(),1)
        self.assertEqual(Recipe.objects.get().ingredients.count(),2)

    def test_edited_new_name_reuses_normalized_existing_food(self):
        data = self.payload('1 cup unknown flour')
        data['ingredients-0-new_food_name']=' FLOUR '
        self.client.post(self.url,data)
        self.assertEqual(Food.objects.count(),1)
        self.assertEqual(Recipe.objects.get().ingredients.get().ingredient_name,self.flour)

    def test_ambiguous_existing_foods_require_a_selection(self):
        Food.objects.create(food_name='Flour!',food_category=self.category,food_aisle=None)
        data = self.payload('1 cup flour')
        response = self.client.post(self.url,data)
        self.assertFalse(Recipe.objects.exists())
        self.assertContains(response,'Several existing foods match')
        data['ingredients-0-food']=self.flour.pk
        self.client.post(self.url,data)
        self.assertEqual(Recipe.objects.get().ingredients.get().ingredient_name,self.flour)
        self.assertEqual(Food.objects.count(),2)

    def test_range_requires_confirmation_and_shopping_uses_maximum(self):
        data = self.payload('1–2 cups flour')
        data.pop('ingredients-0-confirm_uncertain')
        response = self.client.post(self.url,data)
        self.assertContains(response,'Confirm the flagged details')
        self.assertFalse(Recipe.objects.exists())
        data['ingredients-0-confirm_uncertain']='on'
        self.client.post(self.url,data)
        recipe=Recipe.objects.get()
        ingredient=recipe.ingredients.get()
        self.assertEqual((ingredient.ingredient_quantity,ingredient.quantity_max),(1,2))
        grocery_list=GroceryList.objects.create(list_name='2026-11-02')
        add_recipe(grocery_list,recipe)
        self.assertEqual(grocery_list.list_items.get().item_quantity,2)

    def test_uncertain_line_is_never_silently_dropped(self):
        data = self.payload('Salt, to taste')
        data.pop('ingredients-0-reference_only')
        response=self.client.post(self.url,data)
        self.assertContains(response,'Enter a quantity')
        self.assertFalse(Recipe.objects.exists())
        data['ingredients-0-reference_only']='on'
        self.client.post(self.url,data)
        recipe=Recipe.objects.get()
        self.assertFalse(recipe.ingredients.exists())
        self.assertEqual(recipe.ingredient_review_exclusions[0]['original_text'],'Salt, to taste')
        self.assertContains(self.client.get(reverse('recipe_detail',args=[recipe.pk])),'Reference only')

    def test_correcting_unknown_amount_creates_real_ingredient(self):
        data=self.payload('Salt, to taste')
        data.pop('ingredients-0-reference_only')
        data['ingredients-0-quantity']='1/2'
        data['ingredients-0-unit']='teaspoon(s)'
        self.client.post(self.url,data)
        ingredient=Recipe.objects.get().ingredients.get()
        self.assertEqual(ingredient.ingredient_quantity,.5)
        self.assertEqual(ingredient.preparation_notes,'to taste')

    def test_invalid_ranges_and_invalid_food_ids_do_not_write(self):
        for key,value in [('ingredients-0-quantity_max','.25'),('ingredients-0-food','999999')]:
            data=self.payload('1–2 cups flour');data[key]=value
            response=self.client.post(self.url,data)
            self.assertEqual(response.status_code,200)
            self.assertFalse(Recipe.objects.exists())
            self.assertEqual(Food.objects.count(),1)

    def test_missing_rows_tampering_and_changed_text_are_rejected(self):
        for change in [{'ingredients-TOTAL_FORMS':'0'}, {'ingredients-0-original_text':'Changed'},
                       {'ingredient_text':'1 cup flour\n2 cups flour'}]:
            response=self.client.post(self.url,{**self.payload('1 cup flour'),**change})
            self.assertContains(response,'Ingredient lines changed or are missing')
            self.assertFalse(Recipe.objects.exists())

    def test_refresh_reparses_without_writing(self):
        data=self.payload('1 cup flour');data.update(step='refresh_ingredients',ingredient_text='2 tbsp butter')
        response=self.client.post(self.url,data)
        self.assertEqual(response.context['ingredient_formset'].forms[0].initial['quantity'],2)
        self.assertFalse(Recipe.objects.exists())
        self.assertEqual(Food.objects.count(),1)

    def test_atomic_rollback_includes_recipe_food_and_categories(self):
        data=self.payload('1 tbsp butter')
        with patch('recipes.ingredient_review.Ingredient.objects.create',side_effect=ValidationError('Test failure')):
            response=self.client.post(self.url,data)
        self.assertContains(response,'Test failure')
        self.assertFalse(Recipe.objects.exists())
        self.assertEqual(Food.objects.count(),1)
        self.assertEqual(FoodCategory.objects.count(),1)

    def test_prior_import_can_be_processed_once_without_changing_existing_lists(self):
        recipe=Recipe.objects.create(recipe_name='Old import',ingredient_text='1 cup flour',
                                     recipe_category=RecipeCategory.objects.create(recipe_category_name='old'),comments='Keep')
        grocery_list=GroceryList.objects.create(list_name='2026-11-02')
        item=add_item(grocery_list,self.flour,5,'cup(s)')
        data=self.payload('1 cup flour')
        response=self.client.post(reverse('process_recipe_ingredients',args=[recipe.pk]),data)
        self.assertEqual(response.status_code,302)
        self.assertEqual(recipe.ingredients.count(),1)
        self.client.post(reverse('process_recipe_ingredients',args=[recipe.pk]),data)
        self.assertEqual(recipe.ingredients.count(),1)
        item.refresh_from_db();recipe.refresh_from_db()
        self.assertEqual(item.item_quantity,5)
        self.assertEqual(recipe.comments,'Keep')

    def test_existing_manual_ingredients_are_not_replaced(self):
        recipe=Recipe.objects.create(recipe_name='Manual',ingredient_text='2 cups flour',
                                     recipe_category=RecipeCategory.objects.create(recipe_category_name='old'))
        ingredient=Ingredient.objects.create(ingredient_name=self.flour,ingredient_quantity=5,quantity_unit='cup(s)')
        recipe.ingredients.add(ingredient)
        self.client.post(reverse('process_recipe_ingredients',args=[recipe.pk]),self.payload('2 cups flour'))
        self.assertEqual(recipe.ingredients.get().ingredient_quantity,5)

    def test_renaming_import_created_food_frees_old_deduplication_key(self):
        food=Food.objects.create(food_name='butter',food_category=self.category,food_aisle=None,normalized_import_name='butter')
        food.food_name='Salted butter';food.save()
        self.assertIsNone(food.normalized_import_name)
        self.client.post(self.url,self.payload('1 tbsp butter'))
        self.assertEqual(Food.objects.get(food_name='Butter').normalized_import_name,'butter')

    def test_unprocessed_old_import_is_not_silently_added_without_items(self):
        recipe=Recipe.objects.create(recipe_name='Pending',ingredient_text='1 cup flour',
                                     recipe_category=RecipeCategory.objects.create(recipe_category_name='old'))
        grocery_list=GroceryList.objects.create(list_name='2026-11-02')
        response=self.client.post(reverse('recipe_to_list',args=[recipe.pk]), {'choose_a_list':grocery_list.pk})
        self.assertContains(response,'Review this recipe')
        self.assertFalse(grocery_list.list_recipes.exists())
        response=self.client.post(reverse('add_to_list',args=[grocery_list.pk]), {'list_recipes':recipe.pk})
        self.assertContains(response,'Review this recipe')
        self.assertFalse(grocery_list.list_recipes.exists())


class ConsolidationTests(TestCase):
    def setUp(self):
        category=FoodCategory.objects.create(food_category_name='baking')
        self.food=Food.objects.create(food_name='butter',food_category=category,food_aisle=None)
        self.grocery_list=GroceryList.objects.create(list_name='2026-11-02')

    def test_compatible_units_merge_and_decimals_remain_clean(self):
        add_item(self.grocery_list,self.food,1,'cup(s)')
        add_item(self.grocery_list,self.food,2,'TABLESPOON(s)')
        self.assertEqual(self.grocery_list.list_items.get().item_quantity,1.125)
        other=GroceryList.objects.create(list_name='2026-11-03')
        add_item(other,self.food,.1,'gram(s)');add_item(other,self.food,.2,'gram(s)')
        self.assertEqual(other.list_items.get().item_quantity,.3)

    def test_metric_scales_and_weight_scales_are_compatible(self):
        add_item(self.grocery_list,self.food,1,'kilogram(s)')
        add_item(self.grocery_list,self.food,500,'gram(s)')
        self.assertEqual(self.grocery_list.list_items.get().item_quantity,1.5)
        add_item(self.grocery_list,self.food,1,'pound(s)')
        add_item(self.grocery_list,self.food,8,'ounce(s)')
        self.assertEqual(self.grocery_list.list_items.get(item_quantity_unit='pound(s)').item_quantity,1.5)

    def test_incompatible_units_and_distinct_food_ids_stay_separate(self):
        for unit in ['cup(s)','gram(s)','milliliter(s)']:
            add_item(self.grocery_list,self.food,1,unit)
        other=Food.objects.create(food_name='butter',food_category=self.food.food_category,food_aisle=None)
        add_item(self.grocery_list,other,1,'cup(s)')
        self.assertEqual(len(self.grocery_list.make_list()),4)

    def test_legacy_rows_display_consolidation_without_deleting_data(self):
        for quantity,unit in [(1,'cup(s)'),(2,'TABLESPOON(s)')]:
            item=ChooseItem.objects.create(item_name=self.food,item_quantity=quantity,item_quantity_unit=unit)
            self.grocery_list.list_items.add(item)
        self.assertEqual(self.grocery_list.make_list()[0]['quantity'],1.125)
        self.assertEqual(self.grocery_list.list_items.count(),2)

    def test_different_package_sizes_are_not_merged_and_notes_are_retained(self):
        add_item(self.grocery_list,self.food,1,'can(s)','Package size: 14 oz')
        add_item(self.grocery_list,self.food,1,'can(s)','Package size: 28 oz')
        self.assertEqual(self.grocery_list.list_items.count(),2)
        self.assertEqual(len(self.grocery_list.make_list()),2)
        self.assertIn('14 oz',self.grocery_list.make_list()[0]['notes'])
