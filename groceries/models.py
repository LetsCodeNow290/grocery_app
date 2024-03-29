from django.db import models
from components.models import Food
from recipes.models import Recipe
from datetime import datetime as dt
from natsort import natsorted


UNITS = [
    ('teaspoon(s)', 'teaspoon(s)'),
    ('TABLESPOON(s)','TABLESPOON(s)'),
    ('cup(s)', 'cup(s)'),
    ('pint(s)', 'pint(s)'),
    ('quart(s)', 'quart(s)'),
    ('gallon(s)', 'gallon(s)'),
    ('ounce(s)', 'ounce(s)'),
    ('pound(s)', 'pound(s)'),
    ('vegetable or fruit', 'vegetable or fruit'),
    ('other', 'other'),
]

class ChooseItem(models.Model):
    item_name = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='item_name')
    item_quantity = models.FloatField()
    item_quantity_unit = models.CharField(max_length=20, choices=UNITS, default='other')

    def __str__(self):
        return self.item_name.food_name
    

class GroceryList(models.Model):
    list_name = models.DateField()
    list_items = models.ManyToManyField(
        ChooseItem, related_name='items_list', blank=True)
    list_recipes = models.ManyToManyField(
        Recipe, related_name='recipe_list', blank=True)

    def __str__(self):
        return 'List for ' + str(self.list_name)


    def make_list(self):
        grocery_items = self.list_items.all()  # m2m sets
        grocery_item_list = [{
            'food_name': item.item_name.food_name, 
            "aisle": item.item_name.food_aisle.aisle_name,
            "food_category": item.item_name.food_category.food_category_name, 
            'quantity': item.item_quantity, 
            'quantity_unit_name': item.item_quantity_unit
            } for item in grocery_items]
        #final_list = natsorted(grocery_item_list, key=lambda x: x['aisle'])
        
        #dictionary to index the new_list
        names = {}
        new_list = []
        for item in grocery_item_list:
            if (item['food_name'],item['quantity_unit_name']) in names:
                new_list[names[(item['food_name'],item['quantity_unit_name'])]]['quantity'] += item['quantity']   
            else:
                new_list.append(item.copy())
                names[(item['food_name'],item['quantity_unit_name'])] = len(new_list)-1
        # sort list by aisle
        temp_list = natsorted(new_list, key=lambda x: x['food_name'])
        final_list = natsorted(temp_list, key=lambda x: x['aisle'])
        return final_list
    

