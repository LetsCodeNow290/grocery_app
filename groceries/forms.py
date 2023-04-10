from django import forms
from .models import *
from recipes.models import Recipe




class ChooseItemForm(forms.ModelForm):
    class Meta:
        model = ChooseItem
        fields = '__all__'

class GroceryListForm(forms.ModelForm):

    list_recipes = forms.ModelChoiceField(
        Recipe.objects.all().order_by('recipe_name'))
    
    class Meta:
        model = GroceryList
        fields = ['list_recipes']
    
    # This override automaticly creates then saves items to the object
    def save(self, commit=True):
        grocery_list = super(GroceryListForm, self).save(commit=False)
        if commit:
            grocery_list.save()

        # Create ChooseItem objects for each ingredient in each recipe
        grocery_list.list_recipes.add(self.cleaned_data.get('list_recipes'))
        for ingredient in self.cleaned_data.get('list_recipes').ingredients.all():
            item_name = ingredient.ingredient_name
            item_quantity = ingredient.ingredient_quantity
            item_quantity_unit = ingredient.quantity_unit
            choose_item = ChooseItem(item_name=item_name, item_quantity=item_quantity, item_quantity_unit=item_quantity_unit)
            choose_item.save()
            item_obj = ChooseItem.objects.get(pk=choose_item.pk)
            created = True
            for item in grocery_list.list_items.all():
                if item.item_name == item_obj.item_name and item.item_quantity_unit == item_obj.item_quantity_unit:
                    item.item_quantity += item_obj.item_quantity
                    item.save()
                    item_obj.delete()
                    created = False
            if created == True:
                grocery_list.list_items.add(ChooseItem.objects.get(pk=choose_item.pk))

        return grocery_list


class DateInput(forms.DateInput):
    input_type = 'date'


class NewGroceryListForm(forms.ModelForm):
    class Meta:
        model = GroceryList
        fields = ['list_name']
        widgets = {'list_name': DateInput(), }

class RemoveItemFromList(forms.ModelForm):
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