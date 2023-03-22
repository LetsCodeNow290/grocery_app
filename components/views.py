from django.shortcuts import render, reverse, redirect, HttpResponseRedirect
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from natsort import natsorted
from itertools import chain
from django.core.paginator import Paginator
from django.contrib import messages

# Figure out how to add validation so a duplicate entry cannot exist
class AddFood(CreateView):
    model = Food
    fields = ['food_name', 'food_category', 'food_aisle']
    success_url = '/home_admin'

    # This function capitolizes every entry. This helps with sorting in the list view
    def form_valid(self, form):
        form.instance.food_name = form.cleaned_data.get(
            "food_name").capitalize()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = Food.objects.order_by(
            'food_name')
        return super().get_context_data(**kwargs)


class DeleteFood(DeleteView):
    model = Food
    template_name_suffix = '_delete'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            try:
                return f"/food/list?page={self.request.GET.get('next', 1)}"
            except:
                return f"/food/list?page={self.request.GET.get('next', 1) - 1}"
        else:
            return '/food/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)



class UpdateFood(UpdateView):
    model = Food
    fields = ['food_name', 'food_category', 'food_aisle']
    template_name_suffix = '_update'
    
    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/food/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/food/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)

class ListFood(ListView):
    model = Food
    template_name_suffix = '_list'
    paginate_by = 10
    ordering = ['food_name']

    def get_context_data(self, **kwargs):
        kwargs['current_page'] = self.request.GET.get('page', 1)
        kwargs['object_all'] = Food.objects.order_by("food_name")
        return super().get_context_data(**kwargs)


class DetailFood(DetailView):
    model = Food
    template_name_suffix = '_detail'


class AddUnit(CreateView):
    model = MeasuringUnit
    fields = ['unit_name']
    success_url = '/home_admin'

    def form_valid(self, form):
        form.instance.unit_name = form.cleaned_data.get(
            "unit_name").capitalize()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = MeasuringUnit.objects.order_by(
            'unit_name')
        return super().get_context_data(**kwargs)


class DeleteUnit(DeleteView):
    model = MeasuringUnit
    template_name_suffix = '_delete'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/unit/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/unit/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)



class UpdateUnit(UpdateView):
    model = MeasuringUnit
    fields = ['unit_name']
    template_name_suffix = '_update'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/unit/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/unit/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)



class ListUnit(ListView):
    model = MeasuringUnit
    template_name_suffix = '_list'
    paginate_by = 5
    ordering = ['unit_name']

    def get_context_data(self, **kwargs):
        kwargs['current_page'] = self.request.GET.get('page', 1)
        return super().get_context_data(**kwargs)


class AddRecipeCategory(CreateView):
    model = RecipeCategory
    fields = ['recipe_category_name']
    success_url = '/home_admin'

    def form_valid(self, form):
        form.instance.recipe_category_name = form.cleaned_data.get(
            "recipe_category_name").capitalize()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = RecipeCategory.objects.order_by(
            'recipe_category_name')
        return super().get_context_data(**kwargs)


class DeleteRecipeCategory(DeleteView):
    model = RecipeCategory
    template_name_suffix = '_delete'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/recipe_cat/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/recipe_cat/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class UpdateRecipeCategory(UpdateView):
    model = RecipeCategory
    fields = ['recipe_category_name']
    template_name_suffix = '_update'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/recipe_cat/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/recipe_cat/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class ListRecipeCategory(ListView):
    model = RecipeCategory
    template_name_suffix = '_list'
    paginate_by = 5
    ordering = ['recipe_category_name']

    def get_context_data(self, **kwargs):
        kwargs['current_page'] = self.request.GET.get('page', 1)
        return super().get_context_data(**kwargs)


class AddFoodCategory(CreateView):
    model = FoodCategory
    fields = ['food_category_name']
    success_url = '/home_admin'

    def form_valid(self, form):
        form.instance.food_category_name = form.cleaned_data.get(
            "food_category_name").capitalize()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = FoodCategory.objects.order_by(
            'food_category_name')
        return super().get_context_data(**kwargs)


class DeleteFoodCategory(DeleteView):
    model = FoodCategory
    template_name_suffix = '_delete'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/food_cat/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/food_cat/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class UpdateFoodCategory(UpdateView):
    model = FoodCategory
    fields = ['food_category_name']
    template_name_suffix = '_update'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/food_cat/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/food_cat/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class ListFoodCategory(ListView):
    model = FoodCategory
    template_name_suffix = '_list'
    paginate_by = 5
    ordering = ['food_category_name']

    def get_context_data(self, **kwargs):
        kwargs['current_page'] = self.request.GET.get('page', 1)
        return super().get_context_data(**kwargs)


class AddRecipeBook(CreateView):
    model = RecipeBook
    fields = ['book_name', 'recipe_book_image']
    success_url = '/home_admin'

    def form_valid(self, form):
        form.instance.book_name = form.cleaned_data.get(
            "book_name").capitalize()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = RecipeBook.objects.order_by(
            'book_name')
        return super().get_context_data(**kwargs)


class UpdateRecipeBook(UpdateView):
    model = RecipeBook
    fields = ['book_name', 'recipe_book_image']
    template_name_suffix = '_update'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/recipe_book/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/recipe_book/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class DeleteRecipeBook(DeleteView):
    model = RecipeBook
    template_name_suffix = '_delete'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/recipe_book/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/recipe_book/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class ListRecipeBook(ListView):
    model = RecipeBook
    template_name_suffix = '_list'
    paginate_by = 5
    ordering = ['book_name']

    def get_context_data(self, **kwargs):
        kwargs['current_page'] = self.request.GET.get('page', 1)
        return super().get_context_data(**kwargs)


class UpdateAisle(UpdateView):
    model = Aisle
    fields = ['aisle_name']
    template_name_suffix = '_update'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/aisle/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/aisle/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


# This function 'naturally' sorts the list that contains numbers and words. I couldn't make it work with ListView
# Using the union() function re-sorts the objects using the pk
# To access the 'obj_list' info in the template, use .object_list
def listAisle(request):
    natural_list = natsorted([str(x) for x in Aisle.objects.all()])
    obj_list = [(f"{Aisle.objects.filter(aisle_name=x)[0]}", Aisle.objects.filter(
        aisle_name=x)[0]) for x in natural_list]
    p = Paginator(tuple(obj_list), 5)
    page = request.GET.get('page')
    aisles = p.get_page(page)
    current_page = request.GET.get('page', 1)
    return render(request, 'components/aisle_list.html', {'aisles': aisles, 'current_page':current_page})


class DeleteAisle(DeleteView):
    model = Aisle
    template_name_suffix = '_delete'

    def get_success_url(self, **kwargs):
        if self.request.GET.get('next'):
            return f"/aisle/list?page={self.request.GET.get('next', 1)}"
        else:
            return '/aisle/list'

    def get_context_data(self, **kwargs):
        kwargs['last_page'] = self.request.GET.get('next', 1)
        return super().get_context_data(**kwargs)


class AddAisle(CreateView):
    model = Aisle
    fields = ['aisle_name']
    success_url = '/home_admin'

    def form_valid(self, form):
        form.instance.aisle_name = form.cleaned_data.get(
            "aisle_name").capitalize()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        natural_list = natsorted([str(x) for x in Aisle.objects.all()])
        obj_list = [
            f"{Aisle.objects.filter(aisle_name=x)[0]}" for x in natural_list]
        kwargs['object_list'] = obj_list
        return super().get_context_data(**kwargs)
