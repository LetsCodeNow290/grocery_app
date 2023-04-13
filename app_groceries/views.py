from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import *
from django.forms.models import model_to_dict
from django.contrib import messages
from django.http import HttpResponse
import csv

# this method name is misleading, it also allows the user to make a new list
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
    return render(request, 'app_groceries/choose_list.html', {'new_list_form': new_list_form, 'list_of_lists': list_of_lists})

# the 'pk' argument is added to the function so I can access the correct List object


def add_to_list_main(request, pk):
    if request.method == 'POST':
        list_obj = get_object_or_404(GroceryList, pk=pk)
        form_recipe = GroceryListForm(request.POST or None, instance=list_obj)
        form_item = ChooseItemForm(request.POST or None)
        if form_recipe.is_valid() or form_item.is_valid():
            #This next line adds a recipe object to the GroceryList object m2m field
            if form_recipe.is_valid():
                form_recipe.save()
                # Adding and updating ingredients happens in the save method of the GroceryListForm
                messages.success(request, f'The recipe {form_recipe.cleaned_data.get("list_recipes")} has been added to the {GroceryList.objects.get(pk=pk).list_name}')
            if form_item.is_valid():
                form_item.save()
                # The rest of this statement updates the "list_items" field if it already exists
                item_obj = ChooseItem.objects.get(pk=form_item.save().pk)
                
                print(f"ChooseItem objects {ChooseItem.objects.all()}")
                created = True
                for item in list_obj.list_items.all():
                    if item.item_name == item_obj.item_name and item.item_quantity_unit == item_obj.item_quantity_unit:
                        item.item_quantity += item_obj.item_quantity
                        item.save()
                        item_obj.delete()
                        created = False
                if created == True:
                    list_obj.list_items.add(ChooseItem.objects.get(pk=form_item.save().pk))
                print(f"GroceryList objects {list_obj.list_items.all()}")
                messages.success(request, f'{form_item.save().item_name.food_name} was added to the List')
            return HttpResponseRedirect(request.path_info)
    else:
        # This try statement makes the ingredient list
     
        try:
            ingredients = GroceryList.make_list(
                GroceryList.objects.get(pk=pk))
        except Exception as e:
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
        try:
            item_list = GroceryList.objects.get(pk=pk).list_items.all()
        except:
            item_list = None
        recipe_form = GroceryListForm()
        item_form = ChooseItemForm()
    return render(request, 'app_groceries/add_to_list.html', {'recipe_list': recipe_list, 'recipe_form': recipe_form,'item_list': item_list ,'item_form': item_form, 'ingredients': ingredients, 'list_name': list_name})


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
    response['Content-Disposition'] = f'attachment; filename="{GroceryList.objects.get(pk=pk).list_name}List.csv'

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

GroceryListRemoveByRecipeFormset = forms.modelformset_factory(
    GroceryList,
    form = RemoveItemByRecipe,
    fields = ['list_recipes',],
    extra = 0
)

def grocery_detail_and_remove(request, pk):
    '''This view removes items from a grocery list'''
    grocery_list = get_object_or_404(GroceryList, pk=pk)
    if request.method == "POST":
        individual_form = GroceryListRemoveFormset(request.POST, queryset=ChooseItem.objects.filter(items_list=grocery_list))
        # This next part creates a list of item that are marked for deletion
        checked_items = request.POST.getlist("delete")
        if individual_form.is_valid():
            individual_form.save()
            # This next part iterates through the deletion list and deletes the m2m relationship and then deletes the ChooseItem object
            for check in checked_items:
                grocery_list.list_items.remove(ChooseItem.objects.get(pk=check))
                ChooseItem.objects.filter(pk=check).delete()
        return HttpResponseRedirect(request.path_info)
    else:
        try:
            items_list = ChooseItem.objects.filter(items_list=grocery_list)
        except:
            items_list = None
        try:
            list_name = GroceryList.objects.get(pk=pk)
        except:
            list_name = None
        individual_form = GroceryListRemoveFormset(queryset=ChooseItem.objects.filter(items_list=grocery_list))
        recipe_form = GroceryListRemoveByRecipeFormset(queryset=GroceryList.objects.get(pk=pk).list_recipes.all())
    return render(request, 'app_groceries/remove_from_list.html', {"grocery_list":grocery_list,"individual_form":individual_form, 'recipe_form': recipe_form, 'items_list': items_list, 'list_name': list_name})


