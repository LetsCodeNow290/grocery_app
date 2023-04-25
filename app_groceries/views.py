from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import *
from app_stores.forms import SessionStoreForm
from app_stores.models import GroceryStore
from django.forms.models import model_to_dict
from django.contrib import messages
from django.http import HttpResponse
import csv

# this method name is misleading, it also allows the user to make a new list
def choose_list(request):
    if 'store_pk' not in request.session:
        messages.warning(request, "Please choose a store before starting or changing a grocery list")
        if request.method == "POST":
            form = SessionStoreForm(request.POST or None)
            if form.is_valid():
                form_store_name = form.cleaned_data.get("choose_a_list")
                request.session["store_pk"] = form_store_name.id
                request.session["store_name"] = form_store_name.store_name
                request.session["store_address"] = form_store_name.store_address
                return HttpResponseRedirect(request.path_info)
        else:
            form = SessionStoreForm()
        return render(request, "app_stores/choose_store.html", {"form": form})
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
    grocery_list = GroceryList.objects.get(pk=pk)
    grocery_list.list_store = GroceryStore.objects.get(pk=request.session["store_pk"])
    grocery_list.save(update_fields=["list_store"])
    if request.method == 'POST':
        list_obj = get_object_or_404(GroceryList, pk=pk)
        form_recipe = GroceryListForm(request.POST or None, instance=list_obj)
        form_item = ChooseItemForm(request.POST or None)
        if form_recipe.is_valid() or form_item.is_valid():
            #This next line adds a recipe object to the GroceryList object m2m field
            if form_recipe.is_valid():
                form_recipe.save()
                # Adding and updating ingredients happens in the save method of the GroceryListForm
                messages.success(request, f'The recipe {form_recipe.cleaned_data.get("list_recipes").recipe_name} has been added to the {GroceryList.objects.get(pk=pk).list_name}')
            if form_item.is_valid():
                form_item.save()
                # The rest of this statement updates the "list_items" field if it already exists
                item_obj = ChooseItem.objects.get(pk=form_item.save().pk)
                created = True
                for item in list_obj.list_items.all():
                    if item.item_name == item_obj.item_name and item.item_quantity_unit == item_obj.item_quantity_unit:
                        item.item_quantity += item_obj.item_quantity
                        item.save()
                        item_obj.delete()
                        created = False
                if created == True:
                    list_obj.list_items.add(ChooseItem.objects.get(pk=form_item.save().pk))
                messages.success(request, f'{form_item.save().item_name.food_name} was added to the List')
            return HttpResponseRedirect(request.path_info)
    else:
        # This try statement makes the ingredient list
     
        
        ingredients = GroceryList.make_list(GroceryList.objects.get(pk=pk))
        
        # This try is used only for the list object name
        try:
            list_name = GroceryList.objects.get(pk=pk)
        except:
            list_name = None
        # This try statement makes a list of the chosen recipes
        try:
            recipe_list = GroceryListRecipe.objects.filter(grocery_list=grocery_list)
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
    GroceryListRecipe,
    form = RemoveItemByRecipe,
    fields=['recipe_quantity'],
    extra=0
    )

def grocery_detail_and_remove(request, pk):
    '''This view removes items from a grocery list'''
    grocery_list = get_object_or_404(GroceryList, pk=pk)
    if request.method == "POST":
        individual_form = GroceryListRemoveFormset(request.POST, queryset=ChooseItem.objects.filter(items_list=grocery_list))
        recipe_form = GroceryListRemoveByRecipeFormset(request.POST, queryset=GroceryListRecipe.objects.filter(grocery_list=grocery_list))
        if individual_form.is_valid() or recipe_form.is_valid():
            if individual_form.is_valid():
                # This next part creates a list of item that are marked for deletion
                checked_items = request.POST.getlist("delete")
                individual_form.save()
                # This next part iterates through the deletion list and deletes the m2m relationship and then deletes the ChooseItem object
                for check in checked_items:
                    grocery_list.list_items.remove(ChooseItem.objects.get(pk=check))
                    ChooseItem.objects.filter(pk=check).delete()
            if recipe_form.is_valid():
                # This part goes through every recipe in the list no matter what
                for selection_recipe in recipe_form.cleaned_data:
                    list_recipe = GroceryListRecipe.objects.get(pk=selection_recipe["id"].pk)
                    if selection_recipe['recipe_quantity'] == list_recipe.recipe_quantity:
                        continue
                    elif selection_recipe['recipe_quantity'] > list_recipe.recipe_quantity:
                        # This part adds to the list
                        delta = selection_recipe["recipe_quantity"] - list_recipe.recipe_quantity
                        for _ in range(delta):
                            for ingredient in Recipe.objects.get(recipe_name=list_recipe).ingredients.all():
                                item_name = ingredient.ingredient_name
                                item_quantity = ingredient.ingredient_quantity
                                item_quantity_unit = ingredient.quantity_unit
                                choose_item = ChooseItem(item_name=item_name, item_quantity=item_quantity, item_quantity_unit=item_quantity_unit)
                                choose_item.save()
                                item_obj = ChooseItem.objects.get(pk=choose_item.pk)
                                created = True
                                for item in grocery_list.list_items.all():
                                    if item.item_name == item_obj.item_name and item.item_quantity_unit == item_obj.item_quantity_unit:
                                        item.item_quantity += item_obj.item_quantity
                                        item.save()
                                        item_obj.delete()
                                        created = False
                                if created:
                                    grocery_list.list_items.add(ChooseItem.objects.get(pk=choose_item.pk))
                    else:
                        # This part takes away from the list
                        delta = list_recipe.recipe_quantity - selection_recipe["recipe_quantity"]
                        for _ in range(delta):
                            for ingredient in Recipe.objects.get(recipe_name=list_recipe).ingredients.all():
                                choose_item_obj = grocery_list.list_items.get(item_name=Food.objects.get(food_name=ingredient), item_quantity_unit=ingredient.quantity_unit)
                                if choose_item_obj.item_quantity == ingredient.ingredient_quantity:
                                    # Delete statement
                                    grocery_list.list_items.remove(choose_item_obj)
                                    ChooseItem.objects.filter(pk=choose_item_obj.pk).delete()
                                else:
                                    # Update statement 
                                    choose_item_obj.item_quantity -= ingredient.ingredient_quantity
                                    choose_item_obj.save()
                recipe_form.save()
                for obj in GroceryListRecipe.objects.all():
                    if obj.recipe_quantity == 0:
                        obj.delete()
                checked_items = request.POST.getlist("delete")
                for recipe in checked_items:
                    for _ in range(GroceryListRecipe.objects.get(pk=recipe).recipe_quantity):
                        for item in Recipe.objects.get(pk=GroceryListRecipe.objects.get(pk=recipe).recipe_from_list.pk).ingredients.all():
                            # Delete/Update "list_item" and ChooseItem
                            choose_item_obj = grocery_list.list_items.get(item_name=Food.objects.get(food_name=item), item_quantity_unit=item.quantity_unit)
                            if choose_item_obj.item_quantity == item.ingredient_quantity:
                                # Delete statement
                                grocery_list.list_items.remove(choose_item_obj)
                                ChooseItem.objects.filter(pk=choose_item_obj.pk).delete()
                            else:
                                # Update statement 
                                choose_item_obj.item_quantity -= item.ingredient_quantity
                                choose_item_obj.save()
                    # Delete recipe from list
                    GroceryListRecipe.objects.get(pk=recipe).delete()     
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
        recipe_form = GroceryListRemoveByRecipeFormset(queryset=GroceryListRecipe.objects.filter(grocery_list=grocery_list))
        recipes_in_list = GroceryListRecipe.objects.filter(grocery_list=grocery_list)
    return render(request, 'app_groceries/remove_from_list.html', {"grocery_list":grocery_list,"individual_form":individual_form, 'recipe_form': recipe_form, 'recipes_in_list':recipes_in_list,'items_list': items_list, 'list_name': list_name})
