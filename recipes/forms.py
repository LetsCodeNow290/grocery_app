from django import forms
from .models import *
from components.models import RecipeCategory, Food
from groceries.models import GroceryList
import django_filters


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'
        exclude = ['ingredients', ]


class AddFoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = '__all__'




class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeFilter(django_filters.FilterSet):
    # The below code changes the default filter label to "ALL"
    recipe_category = django_filters.ModelChoiceFilter(queryset=RecipeCategory.objects.all(), empty_label="All")
    ingredients = django_filters.ModelChoiceFilter(queryset=Food.objects.all(), empty_label="All")

class RecipeToList(forms.Form):
    choose_a_list = forms.ModelChoiceField(
        GroceryList.objects.all().order_by('-id'), empty_label=None)
