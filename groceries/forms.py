from django import forms
from .models import *
from recipes.models import Recipe


class ChooseItemForm(forms.ModelForm):
    class Meta:
        model = ChooseItem
        fields = '__all__'


# class GroceryListForm(forms.ModelForm):
#     # def __init__(self, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)
#     #     self.fields['list_recipe'].required = True

#     class Meta:
#         model = GroceryList
#         fields = ['list_recipes']

class GroceryListForm(forms.Form):
    list_recipes = forms.ModelChoiceField(
        Recipe.objects.all().order_by('recipe_name'))


class DateInput(forms.DateInput):
    input_type = 'date'


class NewGroceryListForm(forms.ModelForm):
    class Meta:
        model = GroceryList
        fields = ['list_name']
        widgets = {'list_name': DateInput(), }
