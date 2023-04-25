#! /usr/bin/python3

import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grocery_app.settings")
django.setup()
from app_components.models import *
from app_stores.models import GroceryStore
from app_recipes.models import *
import random

def remove_dups():
    obj_list = [food.food_name for food in Food.objects.all()]
    dup_list = [count for count, food in enumerate(obj_list) if food in obj_list[:count]]
    a_list = [food for food in Food.objects.all()]
    final_list = [a_list[food] for food in dup_list]
    for food in final_list:
        Food.objects.get(pk=food.pk).delete()

recipe_names = ['Chicken Stuff', "Beef Stuff", "Pork Stuff", "Pasta Stuff"]
for name in recipe_names:
    if Recipe.objects.filter(recipe_name=name):
        Recipe.objects.filter(recipe_name=name).delete()
    else:
        continue

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
