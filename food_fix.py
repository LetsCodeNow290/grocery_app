#! /usr/bin/python3

import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grocery_app.settings")
django.setup()
from app_components.models import *

def populate_foods():
    with open('InitialData\\food.txt', 'r') as file:
        for line in file:
            if line != "":
                line = line.split(',')
                try:
                    line[2] = line[2].lstrip()
                    line[2] = line[2].strip('\n')
                    food_filter = Food.objects.filter(food_name=line[0])
                    aisle_filter = Aisle.objects.filter(aisle_name=line[2])
                    if food_filter and aisle_filter:
                        food = Food.objects.get(food_name=line[0])
                        aisle = Aisle.objects.get(aisle_name=line[2])
                        food.aisle = aisle
                        food.save

                    else:
                        line[1] = line[1].lstrip()
                        try:
                            food_cat = FoodCategory.objects.get(food_category_name=line[1])
                            aisle_cat = Aisle.objects.get(aisle_name=line[2])
                        
                            Food.objects.create(food_name=line[0], food_category=food_cat, food_aisle=aisle_cat) 
                        except Exception as e:
                            print(e)
                            print(line)
                except IndexError as e:
                    # print(e)
                    # print(line)
                    continue

def remove_dups():
    obj_list = [food.food_name for food in Food.objects.all()]
    dup_list = [count for count, food in enumerate(obj_list) if food in obj_list[:count]]
    a_list = [food for food in Food.objects.all()]
    final_list = [a_list[food] for food in dup_list]
    for food in final_list:
        Food.objects.get(pk=food.pk).delete()





remove_dups()