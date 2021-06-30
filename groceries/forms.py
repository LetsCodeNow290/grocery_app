from django import forms
from .models import *


class ChooseItemForm(forms.ModelForm):
    class Meta:
        model = ChooseItem
        fields = '__all__'


class GroceryListForm(forms.ModelForm):
    class Meta:
        model = GroceryList
        fields = ['list_recipes']


class DateInput(forms.DateInput):
    input_type = 'date'


class NewGroceryListForm(forms.ModelForm):
    class Meta:
        model = GroceryList
        fields = ['list_name']
        widgets = {'list_name': DateInput(), }
