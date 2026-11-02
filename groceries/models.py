from django.db import models
from recipes.units import UNITS, conversion_factor, add_quantities
from components.models import Food
from recipes.models import Recipe
from datetime import datetime as dt
from natsort import natsorted




class ChooseItem(models.Model):
    item_name = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='item_name')
    item_quantity = models.FloatField()
    item_notes = models.TextField(blank=True)
    item_quantity_unit = models.CharField(max_length=20, choices=UNITS, default='other')

    def __str__(self):
        return self.item_name.food_name
    

class GroceryList(models.Model):
    list_name = models.DateField()
    list_items = models.ManyToManyField(
        ChooseItem, related_name='items_list', blank=True, through='GroceryListItems')
    list_recipes = models.ManyToManyField(
        Recipe, related_name='recipe_list', blank=True)

    def __str__(self):
        return 'List for ' + str(self.list_name)


    def make_list(self):
        items = self.list_items.select_related('item_name__food_aisle', 'item_name__food_category').order_by('pk')
        new_list = []
        identities = []
        for item in items:
            for index, (food_id, unit, notes) in enumerate(identities):
                factor = conversion_factor(item.item_quantity_unit, unit)
                if food_id == item.item_name_id and factor is not None and notes == item.item_notes:
                    new_list[index]['quantity'] = add_quantities(
                        new_list[index]['quantity'], item.item_quantity, factor)
                    break
            else:
                identities.append((item.item_name_id, item.item_quantity_unit, item.item_notes))
                new_list.append({
                    'food_name': item.item_name.food_name,
                    'aisle': item.item_name.food_aisle.aisle_name if item.item_name.food_aisle else 'Unassigned',
                    'food_category': item.item_name.food_category.food_category_name,
                    'quantity': item.item_quantity, 'quantity_unit_name': item.item_quantity_unit, 'notes': item.item_notes})
        # sort list by aisle
        temp_list = natsorted(new_list, key=lambda x: x['food_name'])
        final_list = natsorted(temp_list, key=lambda x: x['aisle'])
        return final_list
    



class GroceryListItems(models.Model):
    # Retain the original join table and its data from migration 0001.
    choose_item = models.ForeignKey(ChooseItem, on_delete=models.CASCADE)
    grocery_list = models.ForeignKey(GroceryList, on_delete=models.CASCADE)
