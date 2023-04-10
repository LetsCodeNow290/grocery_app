from django import forms
from .models import *


class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        food_name_field = str(cleaned_data.get('food_name')).title()
        if Food.objects.filter(food_name=food_name_field).exists():
            raise forms.ValidationError("This entry already exists in the database")
        return cleaned_data
    


class RecipeCategoryForm(forms.ModelForm):
    class Meta:
        model = RecipeCategory
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        recipe_cat_name_field = str(cleaned_data.get('recipe_category_name')).title()
        if RecipeCategory.objects.filter(recipe_category_name=recipe_cat_name_field).exists():
            raise forms.ValidationError("This entry already exists in the database")
        return cleaned_data
    

class FoodCategoryForm(forms.ModelForm):
    class Meta:
        model = FoodCategory
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        food_cat_name_field = str(cleaned_data.get('food_category_name')).title()
        if FoodCategory.objects.filter(food_category_name=food_cat_name_field).exists():
            raise forms.ValidationError("This entry already exists in the database")
        return cleaned_data
    

class RecipeBookForm(forms.ModelForm):
    class Meta:
        model = RecipeBook
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        book_name_field = str(cleaned_data.get('book_name')).title()
        if RecipeBook.objects.filter(book_name=book_name_field).exists():
            raise forms.ValidationError("This entry already exists in the database")
        return cleaned_data
    
class AisleForm(forms.ModelForm):
    class Meta:
        model = Aisle
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        aisle_name_field = str(cleaned_data.get('aisle_name')).title()
        if Aisle.objects.filter(aisle_name=aisle_name_field).exists():
            raise forms.ValidationError("This entry already exists in the database")
        return cleaned_data