from django.shortcuts import render, reverse, redirect
from .models import *
from .forms import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from natsort import natsorted
from django.core.paginator import Paginator


class AddFood(CreateView):
    model = Food
    form_class = FoodForm
    #fields = ['food_name', 'food_category', 'food_aisle']
    success_url = '/home_admin'

   
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


class AddRecipeCategory(CreateView):
    model = RecipeCategory
    form_class = RecipeCategoryForm
    success_url = '/home_admin'



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
        kwargs['object_all'] = RecipeCategory.objects.order_by("recipe_category_name")
        return super().get_context_data(**kwargs)


class AddFoodCategory(CreateView):
    model = FoodCategory
    form_class = FoodCategoryForm
    success_url = '/home_admin'



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
        kwargs['object_all'] = FoodCategory.objects.order_by("food_category_name")
        return super().get_context_data(**kwargs)


class AddRecipeBook(CreateView):
    model = RecipeBook
    form_class = RecipeBookForm
    success_url = '/home_admin'



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
        kwargs['object_all'] = RecipeBook.objects.order_by("book_name")
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
    obj_list = [(f"{Aisle.objects.filter(aisle_name=aisle)[0]}", Aisle.objects.filter(aisle_name=aisle)[0]) for aisle in natural_list]
    p = Paginator(tuple(obj_list), 10)
    page = request.GET.get('page')
    aisles = p.get_page(page)
    current_page = request.GET.get('page', 1)
    return render(request, 'app_components/aisle_list.html', {'obj_list':obj_list, 'aisles': aisles, 'current_page':current_page})


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
    form_class = AisleForm
    success_url = '/home_admin'



    def get_context_data(self, **kwargs):
        natural_list = natsorted([str(x) for x in Aisle.objects.all()])
        obj_list = [
            f"{Aisle.objects.filter(aisle_name=x)[0]}" for x in natural_list]
        kwargs['object_list'] = obj_list
        return super().get_context_data(**kwargs)
