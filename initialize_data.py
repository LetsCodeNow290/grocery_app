#! /usr/bin/python3

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grocery_app.settings")
import django
django.setup()
from app_components.models import *
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