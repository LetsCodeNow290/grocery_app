from django.test import TestCase
from .models import *
from app_components.models import *


class BuildRecipeTest(TestCase):
    def setUp(self):
        FoodCategory.objects.create(food_category_name='meat')
        FoodCategory.objects.create(food_category_name='vegetable')
        FoodCategory.objects.create(food_category_name='bean')
        FoodCategory.objects.create(food_category_name='drink')
        FoodCategory.objects.create(food_category_name='egg')
        FoodCategory.objects.create(food_category_name='grain')
        FoodCategory.objects.create(food_category_name='pasta')
        RecipeCategory.objects.create(recipe_category_name='dinner-asian')
        RecipeCategory.objects.create(recipe_category_name='dinner-generic')
        RecipeCategory.objects.create(recipe_category_name='dinner-mexican')
        RecipeCategory.objects.create(recipe_category_name='dinner-one pot')
        RecipeCategory.objects.create(recipe_category_name='breakfast')
        RecipeCategory.objects.create(recipe_category_name='lunch')
        RecipeBook.objects.create(book_name='good_book')
        RecipeBook.objects.create(book_name='great_book')
        RecipeBook.objects.create(book_name='okay_book')
        Aisle.objects.create(aisle_name='1')
        Aisle.objects.create(aisle_name='2')
        Aisle.objects.create(aisle_name='3')
        Aisle.objects.create(aisle_name='produce')
        Aisle.objects.create(aisle_name='dairy')
        Food.objects.create(food_name='chicken-breast',
                            food_category=FoodCategory.objects.get(food_category_name='meat'), food_aisle=Aisle.objects.get(aisle_name='1'))
        Food.objects.create(food_name='chicken-thigh',
                            food_category=FoodCategory.objects.get(food_category_name='meat'), food_aisle=Aisle.objects.get(aisle_name='1'))
        Food.objects.create(food_name='bean-black',
                            food_category=FoodCategory.objects.get(food_category_name='bean'), food_aisle=Aisle.objects.get(aisle_name='1'))
        Food.objects.create(food_name='bean-red',
                            food_category=FoodCategory.objects.get(food_category_name='bean'), food_aisle=Aisle.objects.get(aisle_name='1'))
        Food.objects.create(
            food_name='rice', food_category=FoodCategory.objects.get(food_category_name='grain'), food_aisle=Aisle.objects.get(aisle_name='2'))
        Food.objects.create(
            food_name='eggs', food_category=FoodCategory.objects.get(food_category_name='egg'), food_aisle=Aisle.objects.get(aisle_name='3'))
        Food.objects.create(
            food_name='milk', food_category=FoodCategory.objects.get(food_category_name='dairy'), food_aisle=Aisle.objects.get(aisle_name='dairy'))
        Food.objects.create(food_name='cheese',
                            food_category=FoodCategory.objects.get(food_category_name='dairy'), food_aisle=Aisle.objects.get(aisle_name='dairy'))
        Food.objects.create(food_name='pasta-bow tie',
                            food_category=FoodCategory.objects.get(food_category_name='pasta'), food_aisle=Aisle.objects.get(aisle_name='3'))
        Food.objects.create(food_name='danimal',
                            food_category=FoodCategory.objects.get(food_category_name='dairy'), food_aisle=Aisle.objects.get(aisle_name='dairy'))
        Food.objects.create(food_name='chicken-nugget',
                            food_category=FoodCategory.objects.get(food_category_name='meat'), food_aisle=Aisle.objects.get(aisle_name='2'))
