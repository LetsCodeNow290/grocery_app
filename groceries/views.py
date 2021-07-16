from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import *
from django.forms.models import model_to_dict
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.forms.models import model_to_dict


def choose_list(request):
    if request.method == 'POST':
        form_new_list = NewGroceryListForm(request.POST or None)
        if form_new_list.is_valid:
            form_new_list.save()
            # See formatted string below. This is how to pass the pk of a new object to the url
            return redirect(f'/add_to_list/{form_new_list.save().pk}')
    else:
        new_list_form = NewGroceryListForm()
        try:
            list_of_lists = GroceryList.objects.all().order_by('-id')[:5]
        except:
            list_of_lists = None
    return render(request, 'groceries/choose_list.html', {'new_list_form': new_list_form, 'list_of_lists': list_of_lists})

# the 'pk' argument is added to the function so I can access the correct List object


def add_to_list_main(request, pk):
    if request.method == 'POST':
        obj = get_object_or_404(GroceryList, pk=pk)
        form_recipe = GroceryListForm(request.POST or None, instance=obj)
        form_item = ChooseItemForm(request.POST or None)
        # The try statement below is done so I can submit only one form at a time
        try:
            if form_recipe.is_valid:
                form_recipe.save(commit=False)
                # This next line adds a recipe object to the GroceryList object m2m field
                GroceryList.objects.get(pk=pk).list_recipes.add(Recipe.objects.get(recipe_name=form_recipe.cleaned_data.get('list_recipes')[0])
                                                                )
                the_list_name = GroceryList.objects.get(pk=pk).list_name
                messages.success(
                    request, f'The recipe has been added to the {the_list_name}')
                return HttpResponseRedirect(request.path_info)
        except:
            if form_item.is_valid:
                form_item.save()
                GroceryList.objects.get(pk=pk).list_items.add(
                    ChooseItem.objects.get(pk=form_item.save().pk))
                return HttpResponseRedirect(request.path_info)

    else:
        # This try statement makes the ingredient list
        try:
            obj = GroceryList.make_list(
                GroceryList.objects.get(pk=pk))
            ingredients = {}
            for item in obj:
                print(item)
                try:
                    ingredients[item['food_name']
                                ] = f"{item['food_name']} x {int(item['quantity'])}"
                except:
                    ingredients[item['food_name']
                                ] = f"{item['food_name']} x {item['quantity']}"

        except:

            ingredients = None
        # This try is used only for the list object name
        try:
            list_name = GroceryList.objects.get(pk=pk)
        except:
            list_name = None
        # This try statement makes a list of the chosen recipes
        try:
            recipe_list = GroceryList.objects.get(pk=pk).list_recipes.all()
        except:
            recipe_list = None
        recipe_form = GroceryListForm()
        item_form = ChooseItemForm()
    return render(request, 'groceries/add_to_list.html', {'recipe_list': recipe_list, 'recipe_form': recipe_form, 'item_form': item_form, 'ingredients': ingredients, 'list_name': list_name})


def print_list(request, pk):
    obj = GroceryList.make_list(GroceryList.objects.get(pk=pk))
    new_list = []
    for item in obj:
        try:
            new_quantity = f'{int(item["quantity"])} {item["quantity_unit_name"]}'
        except:
            new_quantity = f'{item["quantity"]} {item["quantity_unit_name"]}'
        new_list.append(
            {'aisle': item['aisle'], 'food_name': item['food_name'], 'quantity': new_quantity})
    recipe_list = [{'Recipes': str(x)} for x in GroceryList.objects.get(
        pk=pk).list_recipes.all()]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="csv_test.csv'

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
