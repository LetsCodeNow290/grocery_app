from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, UpdateView, DeleteView
from django_filters.views import FilterView
from django.contrib import messages
from components.models import Food
from .models import Recipe
from .forms import RecipeForm, IngredientForm, AddFoodForm, RecipeToList, RecipeFilter
from groceries.services import add_recipe


def start_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            if Recipe.objects.filter(recipe_name__iexact=form.cleaned_data['recipe_name']).exists():
                form.add_error('recipe_name', 'This recipe already exists.')
            else:
                recipe = form.save()
                return redirect('add_ingredients', pk=recipe.pk)
    else:
        form = RecipeForm()
    return render(request, 'recipes/recipe_form.html', {'form': form})

def add_ingredient(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    form = IngredientForm()
    add_food = AddFoodForm()
    if request.method == 'POST':
        if 'ingredient_name' in request.POST:
            form = IngredientForm(request.POST)
            if form.is_valid():
                if recipe.ingredients.filter(
                        ingredient_name=form.cleaned_data['ingredient_name']).exists():
                    form.add_error('ingredient_name', 'This food is already in the recipe.')
                else:
                    ingredient = form.save(commit=False)
                    ingredient.ingredient_quantity = (
                        form.cleaned_data['whole_number_quantitiy'] +
                        float(form.cleaned_data['fraction_quantity']))
                    ingredient.save()
                    recipe.ingredients.add(ingredient)
                    return redirect('add_ingredients', pk=pk)
        else:
            add_food = AddFoodForm(request.POST)
            if add_food.is_valid():
                name = add_food.cleaned_data['food_name'].title()
                if Food.objects.filter(food_name__iexact=name).exists():
                    add_food.add_error('food_name', 'This food already exists.')
                else:
                    food = add_food.save()
                    messages.success(request, f'{food} was added to the database')
                    return redirect('add_ingredients', pk=pk)
    return render(request, 'recipes/ingredient_form.html', {
        'form': form, 'data': recipe, 'add_food': add_food})


def recipe_to_list(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    form = RecipeToList(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        add_recipe(form.cleaned_data['choose_a_list'], recipe)
        messages.success(request, f'{recipe} added to {form.cleaned_data["choose_a_list"]}')
        return redirect('recipe_list')
    return render(request, 'recipes/recipe_to_list_form.html', {'form': form})


class RecipeFilterList(FilterView):
    model = Recipe
    filterset_class = RecipeFilter
    context_object_name = 'recipes'
    template_name = 'recipes/recipe_filter.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['current_page'] = self.request.GET.get('page', 1)
        return super().get_context_data(**kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('recipe_name')


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
