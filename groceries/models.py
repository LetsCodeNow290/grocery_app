from django.db import models
from components.models import Food, MeasuringUnit
from recipes.models import Recipe, Ingredient
from datetime import datetime as dt


class ChooseItem(models.Model):
    item_name = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='item_name')
    item_quantity = models.FloatField()
    item_quantity_unit = models.ForeignKey(
        MeasuringUnit, on_delete=models.CASCADE, related_name='item_quantity_unit')

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
        recipes = self.list_recipes.all()  # m2m sets
        recipe_object_list = []
        # This loop extracts the ingredients from each recipe and places them into a list
        for recipe in recipes:
            for ingred in recipe.ingredients.all():
                recipe_object_list.append(ingred)
        # generator to create a list of standardized dictionaries for recipe ingredients
        recipe_full_list = [{'food_name': item.ingredient_name.food_name, "aisle": item.ingredient_name.food_aisle.aisle_name, "food_category": item.ingredient_name.food_category.food_category_name,
                             'quantity': item.ingredient_quantity, 'quantity_unit_name': item.quantity_unit.unit_name} for item in recipe_object_list]
        # Generator to create a list of standardized dictionaries of indivdual grocery items
        grocery_item_list = [{'food_name': item.item_name.food_name, "aisle": item.item_name.food_aisle.aisle_name,
                              "food_category": item.item_name.food_category.food_category_name, 'quantity': item.item_quantity, 'quantity_unit_name': item.item_quantity_unit.unit_name} for item in grocery_items]
        temp_list = recipe_full_list + grocery_item_list
        # dictionary to index the new_list
        names = {}
        new_list = []
        for item in temp_list:
            if item['food_name'] in names:
                new_list[names[item['food_name']]
                         ]['quantity'] += item['quantity']
            else:
                new_list.append(item.copy())
                # this number is the list index number i.e. {'food_name': 1}
                names[item['food_name']] = len(new_list)-1
        # sort list by aisle
        final_list = sorted(new_list, key=lambda x: x['aisle'])
        # convert list to dictionary
        final_dict = {count: item for count, item in enumerate(final_list)}
        return final_list
