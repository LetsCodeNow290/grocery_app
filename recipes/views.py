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
        if form.is_valid():
            form.save()
            return redirect(f'/recipe/{form.save().pk}/add_ingredient')
        else:
            if ValidationError:
                print(form.errors.values())
                messages.error(request, form.errors)
    else:
        form = RecipeForm()
    return render(request, 'recipes/recipe_form.html', {'form': form})


def add_ingredient(request, pk):
    if request.method == 'POST':
        form = IngredientForm(request.POST or None)
        add_food = AddFoodForm(request.POST or None)
        recipe_validation = Recipe.objects.get(pk=pk).ingredients.all()
        food_validation = Food.objects.all()
        if form.is_valid() or add_food.is_valid():
            if form.is_valid():
                form.save(commit=False)
                for obj in recipe_validation:
                    if str(obj) == str(form.cleaned_data.get('ingredient_name')):
                        messages.error(
                            request, f'{str(obj)} is already in the recipe')
                        return redirect(f'/recipe/{pk}/add_ingredient')
                form.save()
                Recipe.objects.get(pk=pk).ingredients.add(
                Ingredient.objects.get(pk=form.save().pk))
            if add_food.is_valid():
                add_food.save()
                messages.success(request, f"{add_food.cleaned_data.get('food_name')} was added to the database")
        elif ValidationError:
            messages.error(request, add_food.errors)
        return redirect(f'/recipe/{pk}/add_ingredient')

    else:
        form = IngredientForm()
        data = Recipe.objects.get(pk=pk)
        add_food = AddFoodForm()
    return render(request, 'recipes/ingredient_form.html', {'form': form, 'data': data, 'add_food':add_food})


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

    def get_context_data(self, **kwargs):
        kwargs['current_page'] = self.request.GET.get('page', 1)
        return super().get_context_data(**kwargs)


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
    template_name_suffix = '_update_form'

    # See paginator note on this. This part returns the user to the previous paginated page
    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/recipe_list?page={self.request.GET.get('next', 1)}"
        else:
            return '/recipe_list'

    def form_valid(self, form):
        form.instance.recipe_name = form.cleaned_data.get(
            "recipe_name").capitalize()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        kwargs['data'] = Recipe.objects.get(pk=self.kwargs.get('pk'))
        return super().get_context_data(**kwargs)


class RecipeDelete(DeleteView):
    model = Recipe
    #success_url = "/recipe_list"
    template_name_suffix = '_delete'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/recipe_list?page={self.request.GET.get('next', 1)}"
        else:
            return '/recipe_list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class RecipeDetail(DetailView):
    model = Recipe
