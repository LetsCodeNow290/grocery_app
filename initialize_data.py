#! /usr/bin/python3

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grocery_app.settings")
import django
django.setup()
from app_components.models import *
from app_stores.models import GroceryStore
from app_recipes.models import *
import random
import os
import re

def clean_data(item):
    return re.sub(r'^\s+|\s+\\n|\s+$', "", item)

# try:
#     pass
    # For Linux/Mac
    # base = f'{os.getcwd()}/InitialData'

    # with open(f'{base}/aisles.txt', 'r') as af:
    #     for line in af:
    #         if Aisle.objects.filter(aisle_name=line):
    #             continue
    #         else:
    #             Aisle(aisle_name=line).save()
    # with open(f'{base}/food_cat.txt', 'r') as af:
    #     for line in af:
    #         if FoodCategory.objects.filter(food_category_name=line):
    #             continue
    #         else:
    #             FoodCategory(food_category_name=line).save()
    # with open(f'{base}/recipe_cat.txt', 'r') as af:
    #     for line in af:
    #         if RecipeCategory.objects.filter(recipe_category_name=line):
    #             continue
    #         else:
    #             RecipeCategory(recipe_category_name=line).save()

    # with open(f'{base}/recipe_book.txt', 'r') as af:
    #     for line in af:
    #         if RecipeBook.objects.filter(book_name=line):
    #             continue
    #         else:
    #             RecipeBook(book_name=line).save()
    # with open(f'{base}/food.txt', 'r') as af:
    #     for line in af:
    #         if line != "":
    #             line = line.split(',')
    #             line[1] = line[1].lstrip()
    #             if Food.objects.filter(food_name=line[0]):
    #                 continue
    #             else:
    #                 Food(food_name=line[0], food_category=FoodCategory.objects.get(
    #                     food_category_name=line[1])).save()
#except:
    # For Windows
base = f'{os.getcwd()}\\InitialData'

with open(f'{base}\\aisles.txt', 'r') as af:
    for line in af:
        line = clean_data(line)
        if Aisle.objects.filter(aisle_name=line):
            continue
        else:
            Aisle(aisle_name=line).save()
with open(f'{base}\\food_cat.txt', 'r') as af:
    for line in af:
        line = clean_data(line)
        if FoodCategory.objects.filter(food_category_name=line):
            continue
        else:
            FoodCategory(food_category_name=line).save()
with open(f'{base}\\recipe_cat.txt', 'r') as af:
    for line in af:
        line = clean_data(line)
        if RecipeCategory.objects.filter(recipe_category_name=line):
            continue
        else:
            RecipeCategory(recipe_category_name=line).save()

with open(f'{base}\\recipe_book.txt', 'r') as af:
    for line in af:
        line = clean_data(line)
        if RecipeBook.objects.filter(book_name=line):
            continue
        else:
            RecipeBook(book_name=line).save()
with open(f'{base}\\food.txt', 'r') as af:
    for line in af:
        line = line.split(',')
        line[0] = clean_data(line[0])
        line[1] = clean_data(line[1])
        if Food.objects.filter(food_name=line[0]):
            continue
        else:
            Food(food_name=line[0], food_category=FoodCategory.objects.get(food_category_name=line[1])).save()

with open(f'{base}\\stores.txt', 'r') as af:
    for line in af:
        line = line.split(',')
        line[0] = clean_data(line[0])
        line[1] = clean_data(line[1])
        if GroceryStore.objects.filter(store_name=line[0]):
            continue
        else:
            GroceryStore(store_name=line[0], store_address=line[1]).save()

# Populate Recipes
recipe_names = ['Chicken Stuff', "Beef Stuff", "Pork Stuff", "Pasta Stuff"]

new_recipe_pk = []
for index in range(len(recipe_names)):
    main_ingred = recipe_names[index].split(" ")[0]
    recipe = Recipe(recipe_name=recipe_names[index], recipe_category=RecipeCategory.objects.order_by("?").first())
    recipe.save()
    recipe_obj = Recipe.objects.get(pk=recipe.pk)
    for item in range(random.randint(3,9)):
        unit = 'other'
        if item == 0:
            main = Food.objects.filter(food_name__icontains=main_ingred).order_by("?").first()
            ingred = Ingredient(ingredient_name=main, ingredient_quantity=random.randint(1,7), quantity_unit=unit)
            ingred.save()
            recipe_obj.ingredients.add(ingred.pk)
        else:
            ingred = Ingredient(ingredient_name=Food.objects.order_by("?").first(), ingredient_quantity=random.randint(1,7), quantity_unit=unit)
            ingred.save()
            recipe_obj.ingredients.add(ingred.pk)