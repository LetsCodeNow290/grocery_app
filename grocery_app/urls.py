"""grocery_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from components.views import *
from home.views import *
from recipes.views import *
from groceries.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('aisle/', AddAisle.as_view(), name='aisle'),
    path('aisle/<int:pk>/delete', DeleteAisle.as_view(), name='aisle_delete'),
    path('aisle/<int:pk>/update', UpdateAisle.as_view(), name='aisle_update'),
    path('aisle/list', listAisle, name='aisle_list'),
    path('food/', AddFood.as_view(), name='food'),
    path('food/<int:pk>/delete', DeleteFood.as_view(), name='food_delete'),
    path('food/<int:pk>/update', UpdateFood.as_view(), name='food_update'),
    path('food/list', ListFood.as_view(), name='food_list'),
    path('food_cat/', AddFoodCategory.as_view(), name='food_cat'),
    path('food_cat/<int:pk>/delete',
         DeleteFoodCategory.as_view(), name='food_cat_delete'),
    path('food_cat/<int:pk>/update',
         UpdateFoodCategory.as_view(), name='food_cat_update'),
    path('food_cat/list', ListFoodCategory.as_view(), name='food_cat_list'),
    path('recipe_book/', AddRecipeBook.as_view(), name='recipe_book'),
    path('recipe_book/<int:pk>/delete',
         DeleteRecipeBook.as_view(), name='recipe_book_delete'),
    path('recipe_book/<int:pk>/update',
         UpdateRecipeBook.as_view(), name='recipe_book_update'),
    path('recipe_book/list', ListRecipeBook.as_view(), name='recipe_book_list'),
    path('recipe_cat/', AddRecipeCategory.as_view(), name='recipe_cat'),
    path('recipe_cat/<int:pk>/delete',
         DeleteRecipeCategory.as_view(), name='recipe_cat_delete'),
    path('recipe_cat/<int:pk>/update',
         UpdateRecipeCategory.as_view(), name='recipe_cat_update'),
    path('recipe_cat/list', ListRecipeCategory.as_view(), name='recipe_cat_list'),
    path('unit/', AddUnit.as_view(), name='unit'),
    path('unit/<int:pk>/delete', DeleteUnit.as_view(), name='unit_delete'),
    path('unit/<int:pk>/update', UpdateUnit.as_view(), name='unit_update'),
    path('unit/list', ListUnit.as_view(), name='unit_list'),
    path('home_admin/', admin_view, name='home_admin'),
    path('recipe/', start_recipe, name='start_recipe'),
    path('recipe/<int:pk>/add_ingredient',
         add_ingredient, name='add_ingredients'),
    path('recipe_list/', RecipeFilterList.as_view(), name='recipe_list'),
    path('recipe_list/<int:pk>/delete',
         RecipeDelete.as_view(), name='recipe_delete'),
    path('recipe_list/<int:pk>/update',
         RecipeUpdate.as_view(), name='recipe_update'),
    path('recipe_list/<int:pk>',
         RecipeDetail.as_view(), name='recipe_detail'),
    path('recipe_to_list/<int:pk>/',
         recipe_to_list, name='recipe_to_list'),
    path('choose_list/', choose_list, name='choose_list'),
    # notice the 'int:pk' statement below. This allows the pk to go into the url
    path('add_to_list/<int:pk>/', add_to_list_main, name='add_to_list'),
    path('add_to_list/<int:pk>/print_list', print_list, name='print_list'),
    path('', home_view, name='home'),
    path('recipe_update/', RecipeUpdate.as_view(), name='recipe_update'),
    path('grocery_detail_and_remove/<int:pk>',
         grocery_detail_and_remove, name='grocery_detail_and_remove'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
