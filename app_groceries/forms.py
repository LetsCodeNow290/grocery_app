from django import forms
from .models import *
from app_recipes.models import Recipe
from django.db.models import F




class ChooseItemForm(forms.ModelForm):
    class Meta:
        model = ChooseItem
        fields = '__all__'



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


# class RemoveItemByRecipe(forms.ModelForm):
#     class Meta:
#         model = GroceryList
#         fields = ['list_recipes']

#     # This line removes the field label
#     def __init__(self, *args, **kwargs):
#         super(RemoveItemByRecipe, self).__init__(*args, **kwargs)
#         for key, field in self.fields.items():
#             field.label = ""

#     # This line allows the form to submit as valid no matter what. This is very sloppy and I need to work on making this better in the future.
#     def is_valid(self) -> bool:
#         return True
    
class RemoveItemByRecipe(forms.ModelForm):
    class Meta:
        model = GroceryListRecipe
        fields = ['recipe_quantity']

    # This line removes the field label
    def __init__(self, *args, **kwargs):
        super(RemoveItemByRecipe, self).__init__(*args, **kwargs)
        for key, field in self.fields.items():
            field.label = ""

    # # This line allows the form to submit as valid no matter what. This is very sloppy and I need to work on making this better in the future.
    # def is_valid(self) -> bool:
    #     return True
    
'''This form will allow me to update and delete recipes with the new GroceryListRecipe model'''
class GroceryListForm(forms.ModelForm):
    class Meta:
        model = GroceryList
        fields = []

    # Use a ModelMultipleChoiceField for the many-to-many relationship with GroceryListRecipe
    list_recipes = forms.ModelChoiceField(
        queryset=Recipe.objects.all().order_by('recipe_name'),
        
    )
    
    def __init__(self, *args, **kwargs):
        super(GroceryListForm, self).__init__(*args, **kwargs)
        # If you want to show only the recipe names in the form instead of the default rendered widget
        self.fields['list_recipes'].choices = [(recipe.id, recipe.recipe_name) for recipe in Recipe.objects.all()]

    def save(self, commit=True):
        grocery_list = super(GroceryListForm, self).save(commit=False)
        if commit:
            grocery_list.save()

        grocery_list_recipe = self.cleaned_data.get("list_recipes")
        # Add selected recipes to GroceryListRecipe
        
        #Update recipe quantity if in current Grocery List
        if GroceryListRecipe.objects.filter(grocery_list=grocery_list, recipe_from_list=grocery_list_recipe):
            GroceryListRecipe.objects.filter(grocery_list=grocery_list, recipe_from_list=grocery_list_recipe).update(recipe_quantity=F('recipe_quantity') + 1)

        #Create recipe otherwise
        else:
            GroceryListRecipe(grocery_list=grocery_list, recipe_from_list=grocery_list_recipe).save()

        # Create ChooseItem objects for each ingredient in each recipe
        
        for ingredient in grocery_list_recipe.ingredients.all():
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
            if created:
                grocery_list.list_items.add(ChooseItem.objects.get(pk=choose_item.pk))

        return grocery_list
