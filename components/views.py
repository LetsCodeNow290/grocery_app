from django.shortcuts import render
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

# for function based pagination, use the import below
# from django.core.paginator import Paginator
# use case: paginator_var = Paginator(Model.objects.all(), 4(items))
#   set up each page with page = request.GET.get('page')
#   put it all together with paged_paginator_var = paginator_var.get_page('page')
# replace context with the paged_paginator_var


class AddFood(CreateView):
    model = Food
    fields = ['food_name', 'food_category', 'food_aisle']
    success_url = '/home_admin'


class DeleteFood(DeleteView):
    model = Food
    success_url = '/food/list'
    template_name_suffix = '_delete'


class UpdateFood(UpdateView):
    model = Food
    fields = ['food_name', 'food_category', 'food_aisle']
    success_url = '/food/list'
    template_name_suffix = '_update'


class ListFood(ListView):
    model = Food
    template_name_suffix = '_list'


class DetailFood(DetailView):
    model = Food
    template_name_suffix = '_detail'


class AddUnit(CreateView):
    model = MeasuringUnit
    fields = ['unit_name']
    success_url = '/home_admin'


class DeleteUnit(DeleteView):
    model = MeasuringUnit
    success_url = '/unit/list'
    template_name_suffix = '_delete'


class UpdateUnit(UpdateView):
    model = MeasuringUnit
    fields = ['unit_name']
    success_url = '/unit/list'
    template_name_suffix = '_update'


class ListUnit(ListView):
    model = MeasuringUnit
    template_name_suffix = '_list'


class AddRecipeCategory(CreateView):
    model = RecipeCategory
    fields = ['recipe_category_name']
    success_url = '/home_admin'


class DeleteRecipeCategory(DeleteView):
    model = RecipeCategory
    success_url = '/recipe_cat/list'
    template_name_suffix = '_delete'


class UpdateRecipeCategory(UpdateView):
    model = RecipeCategory
    fields = ['recipe_category_name']
    success_url = '/recipe_cat/list'
    template_name_suffix = '_update'


class ListRecipeCategory(ListView):
    model = RecipeCategory
    template_name_suffix = '_list'


class AddFoodCategory(CreateView):
    model = FoodCategory
    fields = ['food_category_name']
    success_url = '/home_admin'


class DeleteFoodCategory(DeleteView):
    model = FoodCategory
    success_url = '/food_cat/list'
    template_name_suffix = '_delete'


class UpdateFoodCategory(UpdateView):
    model = FoodCategory
    fields = ['food_category_name']
    success_url = '/food_cat/list'
    template_name_suffix = '_update'


class ListFoodCategory(ListView):
    model = FoodCategory
    template_name_suffix = '_list'


class AddRecipeBook(CreateView):
    model = RecipeBook
    fields = ['book_name']
    success_url = '/home_admin'


class UpdateRecipeBook(UpdateView):
    model = RecipeBook
    fields = ['book_name']
    success_url = '/recipe_book/list'
    template_name_suffix = '_update'


class DeleteRecipeBook(DeleteView):
    model = RecipeBook
    success_url = '/recipe_book/list'
    template_name_suffix = '_delete'


class ListRecipeBook(ListView):
    model = RecipeBook
    template_name_suffix = '_list'


class UpdateAisle(UpdateView):
    model = Aisle
    fields = ['aisle_name']
    success_url = '/aisle/list'
    template_name_suffix = '_update'


class ListAisle(ListView):
    model = Aisle
    template_name_suffix = '_list'
    paginate_by = 5


class DeleteAisle(DeleteView):
    model = Aisle
    success_url = '/aisle/list'
    template_name_suffix = '_delete'


class AddAisle(CreateView):
    model = Aisle
    fields = ['aisle_name']
    success_url = '/home_admin'
