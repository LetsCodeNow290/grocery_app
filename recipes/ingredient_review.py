"""The shared import-review formset and atomic persistence boundary."""
from django.core.exceptions import ValidationError
from django.db import transaction
from components.models import Food, FoodCategory
from .models import Ingredient, Recipe
from .ingredient_processing import food_index, ingredient_lines, ingredient_suggestions, normalize_food_name


def matching_formset(text, data=None):
    from .forms import IngredientMatchFormSet
    lines = ingredient_lines(text)
    index = food_index(Food.objects.all())
    return IngredientMatchFormSet(data, prefix='ingredients', expected_lines=lines,
                                  initial=ingredient_suggestions(text, index), form_kwargs={'index': index})


def resolve_food(data, index):
    if data.get('food'):
        return data['food']
    key = normalize_food_name(data['new_food_name'])
    matches = index.get(key, [])
    if len(matches) > 1:
        raise ValidationError('Several foods now match this name. Refresh suggestions and choose an existing food.')
    if matches:
        return matches[0]
    category = data.get('new_food_category')
    if category is None:
        category, _ = FoodCategory.objects.get_or_create(food_category_name='Imported')
    food, _ = Food.objects.get_or_create(normalized_import_name=key, defaults={
        'food_name': data['new_food_name'].strip(), 'food_category': category,
        'food_aisle': data.get('new_food_aisle'),
    })
    if normalize_food_name(food.food_name) != key:
        raise ValidationError('A food was renamed during review. Refresh suggestions and select the intended food.')
    index.setdefault(key, []).append(food)
    return food


@transaction.atomic
def save_ingredient_review(recipe, formset):
    # Never replace existing structured/manual ingredients, including concurrent edits.
    locked = Recipe.objects.select_for_update().get(pk=recipe.pk)
    if locked.ingredients.exists():
        raise ValidationError('This recipe already has structured ingredients. They have been kept unchanged.')
    if [form.cleaned_data['original_text'] for form in formset] != ingredient_lines(locked.ingredient_text):
        raise ValidationError('The ingredient text changed. Refresh and review it again before saving.')
    index = food_index(Food.objects.all())
    excluded = []
    for form in formset:
        data = form.cleaned_data
        if data.get('reference_only'):
            excluded.append({'original_text': data['original_text'], 'notes': data.get('preparation_notes', '')})
            continue
        food = resolve_food(data, index)
        ingredient = Ingredient.objects.create(
            ingredient_name=food, ingredient_quantity=data['quantity'], quantity_unit=data['unit'],
            quantity_max=data.get('quantity_max'), original_text=data['original_text'],
            preparation_notes=data.get('preparation_notes', ''))
        recipe.ingredients.add(ingredient)
    recipe.ingredient_review_exclusions = excluded
    recipe.save(update_fields=['ingredient_review_exclusions'])
