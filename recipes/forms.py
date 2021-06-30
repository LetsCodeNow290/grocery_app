from django import forms
from .models import *


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = '__all__'
        exclude = ['linked_recipe']


# class RecipeDeleteForm(forms.ModelForm):
#     class Meta:
#         model = Recipe
