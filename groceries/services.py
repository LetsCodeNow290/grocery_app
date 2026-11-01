"""Shared, atomic grocery-list operations used by both recipe entry points."""
from django.db import transaction
from .models import ChooseItem, GroceryList


@transaction.atomic
def add_item(grocery_list, food, quantity, unit):
    GroceryList.objects.select_for_update().get(pk=grocery_list.pk)
    item = grocery_list.list_items.filter(
        item_name=food, item_quantity_unit=unit).order_by('pk').first()
    if item:
        # Legacy data can share an item across lists. Copy before editing.
        if item.items_list.exclude(pk=grocery_list.pk).exists():
            grocery_list.list_items.remove(item)
            item = ChooseItem.objects.create(
                item_name=food, item_quantity=item.item_quantity,
                item_quantity_unit=unit)
            grocery_list.list_items.add(item)
        item.item_quantity += quantity
        item.save(update_fields=['item_quantity'])
    else:
        item = ChooseItem.objects.create(
            item_name=food, item_quantity=quantity, item_quantity_unit=unit)
        grocery_list.list_items.add(item)
    return item


@transaction.atomic
def add_recipe(grocery_list, recipe):
    GroceryList.objects.select_for_update().get(pk=grocery_list.pk)
    # Re-submitting a recipe must not double the shopping quantities.
    if grocery_list.list_recipes.filter(pk=recipe.pk).exists():
        return False
    for ingredient in recipe.ingredients.select_related('ingredient_name'):
        add_item(grocery_list, ingredient.ingredient_name,
                 ingredient.ingredient_quantity, ingredient.quantity_unit)
    grocery_list.list_recipes.add(recipe)
    return True
