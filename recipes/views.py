from django.shortcuts import render, redirect
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import *
from django.forms.models import model_to_dict
from groceries.models import GroceryList


def start_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST or None)
        validation = Recipe.objects.all()
        if form.is_valid():
            recipe_name = form.cleaned_data.get('recipe_name')
            request.session['recipe_name'] = recipe_name
            # create a validation so there are no duplicate recipe names
            for obj in validation:
                if obj.recipe_name.lower() == recipe_name.lower():
                    pass  # create and error message here
                else:
                    continue
            form.save()
            return redirect('add_ingredients')
    else:
        form = RecipeForm()
    return render(request, 'recipes/recipe_form.html', {'form': form})


def add_ingredient(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST or None)
        if form.is_valid:
            instance = form.save(commit=False)
            instance.linked_recipe = request.session['recipe_name']
            instance.save()
        return redirect('add_ingredients')

    else:
        form = IngredientForm()
        data = request.session['recipe_name']
    return render(request, 'recipes/ingredient_form.html', {'form': form, 'data': data})


class RecipeList(ListView):
    model = Recipe
    paginate_by = 5
    ordering = ['recipe_name']


class RecipeUpdate(UpdateView):
    model = Recipe
    fields = [
        'recipe_name',
        'recipe_category',
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
