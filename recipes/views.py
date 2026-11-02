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
        from django.core.exceptions import ValidationError
        try:
            add_recipe(form.cleaned_data['choose_a_list'], recipe)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, f'{recipe} added to {form.cleaned_data["choose_a_list"]}')
            if recipe.ingredient_review_exclusions:
                messages.warning(request, 'Reference-only ingredient lines were not added to the grocery list.')
            return redirect('recipe_list')
    return render(request, 'recipes/recipe_to_list_form.html', {'form': form, 'recipe': recipe})


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
        'source_url',
        'ingredient_text',
        'comments',
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


def recipe_import(request):
    from django.db import transaction
    from components.models import RecipeCategory
    from .forms import RecipeImportURLForm, RecipeImportReviewForm, RecipeBrowserImportForm
    from .importer import RecipeImportError, import_url, extract_browser_content

    url_form = RecipeImportURLForm()
    review_form = None
    browser_form = RecipeBrowserImportForm()
    browser_open = False
    browser_advanced_open = False
    review_hint = ''
    ingredient_formset = None
    from .ingredient_review import matching_formset, save_ingredient_review
    from django.core.exceptions import ValidationError
    if request.method == 'POST':
        if request.POST.get('step') in ('save', 'refresh_ingredients'):
            review_form = RecipeImportReviewForm(request.POST)
            refreshing = request.POST.get('step') == 'refresh_ingredients'
            try:
                ingredient_formset = matching_formset(
                    request.POST.get('ingredient_text', '')[:100001], None if refreshing else request.POST)
            except ValueError as error:
                review_form.is_valid()
                review_form.add_error('ingredient_text', str(error))
            if refreshing:
                review_hint = 'Ingredient suggestions refreshed. Check all lines before saving.'
            elif review_form.is_valid() and ingredient_formset is not None and ingredient_formset.is_valid():
                try:
                    with transaction.atomic():
                        recipe = review_form.save(commit=False)
                        if recipe.recipe_category_id is None:
                            recipe.recipe_category, _ = RecipeCategory.objects.get_or_create(
                                recipe_category_name='Imported')
                        recipe.recipe_rating = "Haven't Made it Yet"
                        recipe.save()
                        save_ingredient_review(recipe, ingredient_formset)
                except ValidationError as error:
                    review_form.add_error(None, error)
                else:
                    messages.success(request, 'Recipe and confirmed ingredients saved. You can add this recipe to a grocery list.')
                    return redirect('recipe_detail', pk=recipe.pk)
        elif request.POST.get('step') == 'browser':
            browser_open = True
            browser_advanced_open = bool(request.FILES)
            browser_form = RecipeBrowserImportForm(request.POST, request.FILES)
            if browser_form.is_valid():
                try:
                    draft = extract_browser_content(browser_form.cleaned_data['browser_content'])
                except RecipeImportError as error:
                    browser_form.add_error(None, str(error))
                else:
                    draft['source_url'] = browser_form.cleaned_data['source_url']
                    review_form = RecipeImportReviewForm(initial=draft)
                    if draft.get('comments'):
                        review_hint = ('Check the suggested fields. Your complete browser copy is kept in Notes.')
                        if not draft.get('ingredient_text'):
                            review_hint = ('Ingredient and instruction headings were not recognized. '
                                           'All copied text is kept in Instructions and Notes. '
                                           'Enter a recipe name and move ingredient lines into Ingredients before saving.')
        else:
            url_form = RecipeImportURLForm(request.POST)
            if url_form.is_valid():
                source_url = url_form.cleaned_data['url']
                try:
                    draft = import_url(source_url)
                except RecipeImportError as error:
                    url_form.add_error('url', str(error))
                    browser_open = True
                    browser_form = RecipeBrowserImportForm(initial={'source_url': source_url})
                else:
                    review_form = RecipeImportReviewForm(initial=draft)
    if review_form is not None and ingredient_formset is None and not review_form.is_bound:
        if not review_form.initial.get('comments'):
            review_form.initial['comments'] = review_form.initial.get('ingredient_text', '')
        try:
            ingredient_formset = matching_formset(review_form.initial.get('ingredient_text', ''))
        except ValueError as error:
            review_hint = str(error)
    return render(request, 'recipes/recipe_import.html', {
        'url_form': url_form, 'review_form': review_form,
        'browser_form': browser_form, 'browser_open': browser_open,
        'browser_advanced_open': browser_advanced_open, 'review_hint': review_hint,
        'ingredient_formset': ingredient_formset})


def process_recipe_ingredients(request, pk):
    from .ingredient_review import matching_formset, save_ingredient_review
    from django.core.exceptions import ValidationError
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe.ingredients.exists() or not recipe.ingredient_text.strip():
        messages.info(request, 'Existing ingredients are kept unchanged. There is no unprocessed ingredient text to review.')
        return redirect('recipe_detail', pk=pk)
    error = ''
    formset = None
    try:
        formset = matching_formset(recipe.ingredient_text, request.POST if request.method == 'POST' else None)
        if request.method == 'POST' and formset.is_valid():
            save_ingredient_review(recipe, formset)
            messages.success(request, 'Confirmed ingredients saved. This recipe is ready for grocery lists.')
            return redirect('recipe_detail', pk=pk)
    except (ValueError, ValidationError) as exception:
        error = str(exception)
    return render(request, 'recipes/recipe_ingredient_review.html', {
        'recipe': recipe, 'ingredient_formset': formset, 'processing_error': error})
