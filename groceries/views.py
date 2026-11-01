import csv
from django import forms
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ChooseItemForm, GroceryListForm, NewGroceryListForm, RemoveItemFromList
from .models import ChooseItem, GroceryList
from .services import add_item


def choose_list(request):
    form = NewGroceryListForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        grocery_list = form.save()
        return redirect('add_to_list', pk=grocery_list.pk)
    return render(request, 'groceries/choose_list.html', {
        'new_list_form': form,
        'list_of_lists': GroceryList.objects.order_by('-id')[:5],
    })


def add_to_list_main(request, pk):
    grocery_list = get_object_or_404(GroceryList, pk=pk)
    recipe_form = GroceryListForm(instance=grocery_list)
    item_form = ChooseItemForm()
    if request.method == 'POST':
        if 'list_recipes' in request.POST:
            recipe_form = GroceryListForm(request.POST, instance=grocery_list)
            if recipe_form.is_valid():
                recipe_form.save()
                messages.success(request, 'Recipe ingredients are on the list.')
                return redirect('add_to_list', pk=pk)
        else:
            item_form = ChooseItemForm(request.POST)
            if item_form.is_valid():
                data = item_form.cleaned_data
                add_item(grocery_list, data['item_name'], data['item_quantity'],
                         data['item_quantity_unit'])
                messages.success(request, 'Item added to the list.')
                return redirect('add_to_list', pk=pk)
    return render(request, 'groceries/add_to_list.html', {
        'recipe_list': grocery_list.list_recipes.all(),
        'recipe_form': recipe_form, 'item_form': item_form,
        'item_list': grocery_list.list_items.all(),
        'ingredients': grocery_list.make_list(), 'list_name': grocery_list,
    })


def print_list(request, pk):
    grocery_list = get_object_or_404(GroceryList, pk=pk)
    obj = grocery_list.make_list()
    new_list = []
    for item in obj:
        new_quantity = f'{item["quantity"]:g} {item["quantity_unit_name"]}'
        new_list.append(
            {'aisle': item['aisle'], 'food_name': item['food_name'], 'quantity': new_quantity})
    recipe_list = [{'Recipes': str(x)} for x in grocery_list.list_recipes.all()]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{grocery_list.list_name}List.csv"'

    recipe_fieldnames = ['Recipes']
    recipe_writer = csv.DictWriter(response, fieldnames=recipe_fieldnames)

    recipe_writer.writeheader()
    for recipe in recipe_list:
        recipe_writer.writerow(recipe)

    fieldnames = ['aisle', 'food_name', 'quantity']
    writer = csv.DictWriter(response, fieldnames=fieldnames)

    writer.writeheader()
    for item in new_list:
        writer.writerow(item)
    return response


# This formset allows the following view to modify individual items in a many 2 many field
GroceryListRemoveFormset = forms.modelformset_factory(
    ChooseItem,
    form = RemoveItemFromList,
    fields = ['item_quantity',],
    extra = 0
)

def grocery_detail_and_remove(request, pk):
    grocery_list = get_object_or_404(GroceryList, pk=pk)
    items = grocery_list.list_items.order_by('pk')
    formset = GroceryListRemoveFormset(
        request.POST if request.method == 'POST' else None, queryset=items)
    if request.method == 'POST' and formset.is_valid():
        with transaction.atomic():
            GroceryList.objects.select_for_update().get(pk=pk)
            # Only edit/delete items belonging to this list. Preserve shared rows.
            checked = set(request.POST.getlist('delete'))
            for form in formset.forms:
                item = form.instance
                if not items.filter(pk=item.pk).exists():
                    continue
                if str(item.pk) in checked:
                    grocery_list.list_items.remove(item)
                    if not item.items_list.exists():
                        item.delete()
                elif form.has_changed():
                    if item.items_list.exclude(pk=pk).exists():
                        grocery_list.list_items.remove(item)
                        item.pk = None
                        item.save()
                        grocery_list.list_items.add(item)
                    else:
                        form.save()
        return redirect('grocery_detail_and_remove', pk=pk)
    return render(request, 'groceries/remove_from_list.html', {
        'grocery_list': grocery_list, 'individual_form': formset,
        'items_list': items, 'list_name': grocery_list,
    })
