#! /usr/bin/python3

from components.models import *
import os

obj_list = {'MeasuringUnit': MeasuringUnit, 'Aisle': Aisle,
            'FoodCategory': FoodCategory, 'RecipeCategory': RecipeCategory}

with open('initial_data.txt', 'r') as f:
    for x in f:
        tmp = x.split(',')
        with open(f'{os.getcwd()}\InitialData\{tmp[1]}', 'r') as base_file:
            for line in base_file:
                # obj_list[tmp[0]].objects.create(tmp[2]=line).save()
                with open('start.txt', 'a') as start:
                    start.write(
                        f'{tmp[0]}({tmp[2]}={line}.save()\n')
