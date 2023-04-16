from django import forms
from .models import *
from app_components.models import RecipeCategory, Food
from app_groceries.models import GroceryList
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


QUANTITY_FRAC = [
    (0,'0'),
    (.75,'3/4'),
    (.66, '2/3'),
    (.5, '1/2'),
    (.33, '1/3'),
    (.25, '1/4'),
    (.125, '1/8'),
]

class IngredientForm(forms.ModelForm):
    fraction_quantity = forms.ChoiceField(choices=QUANTITY_FRAC)
    whole_number_quantitiy = forms.IntegerField()
    class Meta:
        model = Ingredient
        fields = 'ingredient_name', 'whole_number_quantitiy', 'fraction_quantity', 'quantity_unit'


class RecipeFilter(django_filters.FilterSet):
    # The below code changes the default filter label to "ALL"
    recipe_category = django_filters.ModelChoiceFilter(queryset=RecipeCategory.objects.all(), empty_label="All")
    ingredients = django_filters.ModelChoiceFilter(queryset=Food.objects.all(), empty_label="All")

class RecipeToList(forms.Form):
    choose_a_list = forms.ModelChoiceField(GroceryList.objects.all().order_by('-id'), empty_label=None)
