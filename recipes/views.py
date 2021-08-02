from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import *
from django.forms.models import model_to_dict
from groceries.models import GroceryList
from django_filters.views import FilterView
from django.contrib import messages


def start_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST or None)
        validation = Recipe.objects.all()
        if form.is_valid():
            recipe_name = form.cleaned_data.get('recipe_name')
            # validation for duplicate recipes. May not work. Needs to be tested
            for obj in validation:
                if obj.recipe_name.lower() == recipe_name.lower():
                    messages.error(request, 'That recipe already exists')
                    return redirect(f'/recipe_list/{obj.pk}')
                else:
                    continue
            form.save()
            return redirect(f'/recipe/{form.save().pk}/add_ingredient')
    else:
        form = RecipeForm()
    return render(request, 'recipes/recipe_form.html', {'form': form})


def add_ingredient(request, pk):
    if request.method == 'POST':
        form = IngredientForm(request.POST or None)
        validation = Recipe.objects.get(pk=pk).ingredients.all()
        if form.is_valid:
            form.save(commit=False)
            for obj in validation:
                if str(obj) == str(form.cleaned_data.get('ingredient_name')):
                    messages.error(
                        request, f'{str(obj)} is already in the recipe')
                    return redirect(f'/recipe/{pk}/add_ingredient')
            form.save()
            Recipe.objects.get(pk=pk).ingredients.add(
                Ingredient.objects.get(pk=form.save().pk))
        return redirect(f'/recipe/{pk}/add_ingredient')

    else:
        form = IngredientForm()
        data = Recipe.objects.get(pk=pk)
    return render(request, 'recipes/ingredient_form.html', {'form': form, 'data': data})


def recipe_to_list(request, pk):
    if request.method == 'POST':
        obj = get_object_or_404(Recipe, pk=pk)
        form = RecipeToList(request.POST or None)
        if form.is_valid():
            form.cleaned_data['choose_a_list'].list_recipes.add(obj)
            messages.success(request,
                             f'{obj} added to {form.cleaned_data["choose_a_list"]}')
        return redirect('/recipe_list/')
    else:
        form = RecipeToList()
    return render(request, 'recipes/recipe_to_list_form.html', {'form': form})


class RecipeFilterList(FilterView):
    model = Recipe
    filterset_class = RecipeFilter
    context_object_name = 'recipes'
    template_name = 'recipe_filter'
    paginate_by = 10


class RecipeUpdate(UpdateView):
    model = Recipe
    fields = [
        'recipe_name',
        'recipe_category',
        'recipe_rating',
        'recipe_image',
        'recipe_instructions',
        'recipe_location',
        'location_page_number'
    ]
    success_url = "/recipe_list"
    template_name_suffix = '_update_form'

    def form_valid(self, form):
        form.instance.recipe_name = form.cleaned_data.get(
            "recipe_name").capitalize()
        return super().form_valid(form)


class RecipeDelete(DeleteView):
    model = Recipe
    success_url = "/recipe_list"
    template_name_suffix = '_delete'


class RecipeDetail(DetailView):
    model = Recipe
