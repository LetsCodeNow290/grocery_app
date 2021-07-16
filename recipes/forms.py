from django import forms
from .models import *
from groceries.models import GroceryList
import django_filters


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'
        exclude = ['ingredients', ]


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeFilter(django_filters.FilterSet):
    class Meta:
        model = Recipe
        fields = ['recipe_category', ]


class RecipeToListForm(forms.Form):
    choose_a_list = forms.ModelChoiceField(
        GroceryList.objects.all().order_by('-id'), empty_label=None)


class RecipeToList(forms.Form):
    choose_a_list = forms.ModelChoiceField(
        GroceryList.objects.all().order_by('-id'), empty_label=None)
