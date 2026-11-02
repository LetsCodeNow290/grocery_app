from django import forms
from urllib.parse import urlsplit
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

    comments = forms.CharField(label='Notes / original browser copy', required=False, max_length=100000,
                               widget=forms.Textarea(attrs={'rows': 6}))

    class Meta(RecipeForm.Meta):
        fields = ['source_url', 'recipe_name', 'recipe_category',
                  'ingredient_text', 'recipe_instructions', 'comments']
        exclude = []

    def clean_recipe_name(self):
        name = self.cleaned_data['recipe_name']
        if Recipe.objects.filter(recipe_name__iexact=name).exists():
            raise forms.ValidationError('This recipe already exists. Choose a different name.')
        return name

    def clean_source_url(self):
        return clean_recipe_source_url(self.cleaned_data['source_url'])


def clean_recipe_source_url(url):
    if not url:
        raise forms.ValidationError('Keep the recipe source URL for attribution.')
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or parts.username is not None or parts.password is not None:
        raise forms.ValidationError('Use an HTTP or HTTPS source URL without login credentials.')
    return url


class RecipeBrowserImportForm(forms.Form):
    source_url = forms.URLField(label='Original recipe page URL', max_length=2048)
    content = forms.CharField(
        label='Recipe copied from your browser', required=False, max_length=100000,
        widget=forms.Textarea(attrs={
            'rows': 12,
            'placeholder': 'Recipe title\n\nIngredients\n…\n\nDirections\n…',
            'spellcheck': 'false',
        }), help_text='Paste the title, ingredients, and directions. Review and correct them next.')
    content_file = forms.FileField(
        label='Or upload a saved page or text file', required=False,
        widget=forms.FileInput(attrs={'accept': '.html,.htm,.json,.txt'}),
        help_text='Optional: a UTF-8 HTML, JSON-LD, or text file, up to 2 MB. Paste or upload, not both.')

    def clean_source_url(self):
        return clean_recipe_source_url(self.cleaned_data['source_url'])

    def clean(self):
        from .importer import MAX_BYTES
        data = super().clean()
        if self.errors:
            return data
        pasted = data.get('content', '')
        uploaded = data.get('content_file')
        if bool(pasted) == bool(uploaded):
            raise forms.ValidationError('Paste recipe content or choose a saved file (one or the other).')
        if uploaded:
            if not uploaded.name.lower().endswith(('.html', '.htm', '.json', '.txt')):
                self.add_error('content_file', 'Choose an HTML, JSON-LD (.json), or text file.')
                return data
            if uploaded.size > MAX_BYTES:
                self.add_error('content_file', 'The file is too large (maximum 2 MB).')
                return data
            raw = uploaded.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                self.add_error('content_file', 'The file is too large (maximum 2 MB).')
                return data
            try:
                pasted = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                self.add_error('content_file', 'Save the file as UTF-8 text, or paste the visible recipe instead.')
                return data
        if not pasted.strip():
            raise forms.ValidationError('The supplied content is empty. Copy the recipe text and try again.')
        data['browser_content'] = pasted
        return data
