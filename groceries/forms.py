from django import forms
from .models import *
from recipes.models import Recipe




class ChooseItemForm(forms.ModelForm):
    item_quantity = forms.FloatField(min_value=0.001)
    class Meta:
        model = ChooseItem
        fields = '__all__'

class GroceryListForm(forms.ModelForm):

    list_recipes = forms.ModelChoiceField(
        Recipe.objects.all().order_by('recipe_name'))
    
    class Meta:
        model = GroceryList
        fields = ['list_recipes']
    
    def save(self, commit=True):
        if not commit:
            raise ValueError('Adding a recipe requires commit=True.')
        from .services import add_recipe
        add_recipe(self.instance, self.cleaned_data['list_recipes'])
        return self.instance


class DateInput(forms.DateInput):
    input_type = 'date'


class NewGroceryListForm(forms.ModelForm):
    class Meta:
        model = GroceryList
        fields = ['list_name']
        widgets = {'list_name': DateInput(), }

class RemoveItemFromList(forms.ModelForm):
    item_quantity = forms.FloatField(min_value=0)
    class Meta:
        model = ChooseItem
        fields = ['item_quantity']

    # This line removes the field label
    def __init__(self, *args, **kwargs):
        super(RemoveItemFromList, self).__init__(*args, **kwargs)
        for key, field in self.fields.items():
            field.label = ""

class RemoveItemByRecipe(forms.ModelForm):
    class Meta:
        model = GroceryList
        fields = ['list_recipes']

    # This line removes the field label
    def __init__(self, *args, **kwargs):
        super(RemoveItemByRecipe, self).__init__(*args, **kwargs)
        for key, field in self.fields.items():
            field.label = ""