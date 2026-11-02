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
    whole_number_quantitiy = forms.IntegerField(min_value=0)
    class Meta:
        model = Ingredient
        fields = 'ingredient_name', 'whole_number_quantitiy', 'fraction_quantity', 'quantity_unit'

    def clean(self):
        data = super().clean()
        whole = data.get('whole_number_quantitiy')
        fraction = data.get('fraction_quantity')
        if whole is not None and fraction is not None and whole + float(fraction) <= 0:
            raise forms.ValidationError('Ingredient quantity must be greater than zero.')
        return data


class RecipeFilter(django_filters.FilterSet):
    # The below code changes the default filter label to "ALL"
    recipe_category = django_filters.ModelChoiceFilter(queryset=RecipeCategory.objects.all(), empty_label="All")
    ingredients = django_filters.ModelChoiceFilter(field_name='ingredients__ingredient_name', queryset=Food.objects.all(), empty_label="All", distinct=True)

class RecipeToList(forms.Form):
    choose_a_list = forms.ModelChoiceField(
        GroceryList.objects.all().order_by('-id'), empty_label=None)


class RecipeImportURLForm(forms.Form):
    url = forms.URLField(label='Recipe website URL', max_length=2048,
                        widget=forms.URLInput(attrs={'placeholder': 'https://…'}))


class RecipeImportReviewForm(RecipeForm):
    recipe_category = forms.ModelChoiceField(
        queryset=RecipeCategory.objects.all(), required=False,
        empty_label='Imported (default category)')
    ingredient_text = forms.CharField(label='Ingredients', max_length=100000,
                                     widget=forms.Textarea(attrs={'rows': 12}))
    recipe_instructions = forms.CharField(label='Instructions', max_length=100000,
                                         widget=forms.Textarea(attrs={'rows': 12}))

    class Meta(RecipeForm.Meta):
        fields = ['source_url', 'recipe_name', 'recipe_category',
                  'ingredient_text', 'recipe_instructions']
        exclude = []

    def clean_recipe_name(self):
        name = self.cleaned_data['recipe_name']
        if Recipe.objects.filter(recipe_name__iexact=name).exists():
            raise forms.ValidationError('This recipe already exists. Choose a different name.')
        return name

    def clean_source_url(self):
        url = self.cleaned_data['source_url']
        if not url:
            raise forms.ValidationError('Keep the recipe source URL for attribution.')
        from urllib.parse import urlsplit
        if urlsplit(url).scheme not in ('http', 'https'):
            raise forms.ValidationError('Use an HTTP or HTTPS source URL.')
        return url
