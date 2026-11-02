"""Shared, atomic grocery-list operations used by both recipe entry points."""
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import ChooseItem, GroceryList
from recipes.units import conversion_factor, add_quantities


@transaction.atomic
def add_item(grocery_list, food, quantity, unit, notes=''):
    GroceryList.objects.select_for_update().get(pk=grocery_list.pk)
    candidates = grocery_list.list_items.filter(item_name=food, item_notes=notes).order_by('pk')
    item = next((candidate for candidate in candidates
                 if conversion_factor(unit, candidate.item_quantity_unit) is not None), None)
    if item:
        # Legacy data can share an item across lists. Copy before editing.
        if item.items_list.exclude(pk=grocery_list.pk).exists():
            grocery_list.list_items.remove(item)
            item = ChooseItem.objects.create(
                item_name=food, item_quantity=item.item_quantity,
                item_quantity_unit=item.item_quantity_unit, item_notes=item.item_notes)
            grocery_list.list_items.add(item)
        item.item_quantity = add_quantities(item.item_quantity, quantity,
                                            conversion_factor(unit, item.item_quantity_unit))
        item.save(update_fields=['item_quantity'])
    else:
        item = ChooseItem.objects.create(
            item_name=food, item_quantity=quantity, item_quantity_unit=unit, item_notes=notes)
        grocery_list.list_items.add(item)
    return item


@transaction.atomic
def add_recipe(grocery_list, recipe):
    GroceryList.objects.select_for_update().get(pk=grocery_list.pk)
    if recipe.ingredient_text.strip() and not recipe.ingredients.exists() and not recipe.ingredient_review_exclusions:
        raise ValidationError('Review this recipe’s ingredient matches before adding it to a grocery list.')
    # Re-submitting a recipe must not double the shopping quantities.
    if grocery_list.list_recipes.filter(pk=recipe.pk).exists():
        return False
    for ingredient in recipe.ingredients.select_related('ingredient_name'):
        add_item(grocery_list, ingredient.ingredient_name,
                 ingredient.quantity_max if ingredient.quantity_max is not None else ingredient.ingredient_quantity,
                 ingredient.quantity_unit, ingredient.preparation_notes)
    grocery_list.list_recipes.add(recipe)
    return True
