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


class IngredientQuantityField(forms.FloatField):
    widget = forms.TextInput(attrs={'inputmode': 'decimal'})

    def to_python(self, value):
        from .ingredient_processing import parse_quantity
        if value in self.empty_values:
            return None
        try:
            return parse_quantity(value)
        except (ValueError, ZeroDivisionError, OverflowError):
            raise forms.ValidationError('Enter a positive amount such as 1.5, 1/2, or 1 1/2.')


class IngredientMatchForm(forms.Form):
    original_text = forms.CharField(max_length=100000, widget=forms.HiddenInput)
    quantity = IngredientQuantityField(label='Quantity', min_value=0.000001, max_value=1000000, required=False)
    quantity_max = IngredientQuantityField(label='Upper quantity (ranges only)', min_value=0.000001,
                                   max_value=1000000, required=False,
                                   help_text='Shopping uses this upper amount when a range is retained.')
    unit = forms.ChoiceField(choices=UNITS)
    food = forms.ModelChoiceField(queryset=Food.objects.all(), required=False,
                                 label='Existing food', empty_label='Create / reuse food named below')
    new_food_name = forms.CharField(label='New food name', max_length=100, required=False)
    new_food_category = forms.ModelChoiceField(queryset=FoodCategory.objects.all(), required=False,
                                              label='Category for new food', empty_label='Imported (default)')
    new_food_aisle = forms.ModelChoiceField(queryset=Aisle.objects.all(), required=False,
                                           label='Aisle for new food', empty_label='Unassigned')
    preparation_notes = forms.CharField(required=False, max_length=10000,
                                       widget=forms.Textarea(attrs={'rows': 2}))
    confirm_uncertain = forms.BooleanField(required=False, label='I checked the flagged details')
    reference_only = forms.BooleanField(required=False,
        label='Keep as reference only — do not add this line to grocery lists')

    def __init__(self, *args, index=None, **kwargs):
        from .ingredient_processing import parse_ingredient, normalize_food_name
        super().__init__(*args, **kwargs)
        self.index = index or {}
        self.original = self['original_text'].value() or ''
        parsed = parse_ingredient(self.original)
        self.warnings = parsed['warnings'][:]
        if len(self.index.get(normalize_food_name(parsed['food_name']), [])) > 1:
            self.warnings.append('Several foods match this name. Choose the intended existing food.')
        self.show_new_food = not self['food'].value()

    def clean(self):
        from .ingredient_processing import normalize_food_name
        data = super().clean()
        if data.get('reference_only'):
            return data
        if data.get('quantity') is None:
            self.add_error('quantity', 'Enter a quantity, or explicitly keep this line as reference only.')
        if data.get('quantity_max') is not None and data.get('quantity') is not None:
            if data['quantity_max'] < data['quantity']:
                self.add_error('quantity_max', 'The upper amount must be at least the lower amount.')
        if (self.warnings or data.get('quantity_max') is not None) and not data.get('confirm_uncertain'):
            self.add_error('confirm_uncertain', 'Confirm the flagged details or keep this line as reference only.')
        if not data.get('food'):
            name = data.get('new_food_name', '')
            key = normalize_food_name(name)
            if not key:
                self.add_error('new_food_name', 'Choose an existing food or enter a food name.')
            elif len(key) > 100:
                self.add_error('new_food_name', 'Choose a shorter food name.')
            elif len(self.index.get(key, [])) > 1:
                self.add_error('food', 'Several existing foods match. Select one; no duplicate will be created.')
        return data


class BaseIngredientMatchFormSet(forms.BaseFormSet):
    def __init__(self, *args, expected_lines=(), **kwargs):
        self.expected_lines = list(expected_lines)
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        submitted = [form['original_text'].value() for form in self.forms]
        if submitted != self.expected_lines:
            raise forms.ValidationError('Ingredient lines changed or are missing. Refresh ingredient suggestions and review every line before saving.')


IngredientMatchFormSet = forms.formset_factory(
    IngredientMatchForm, formset=BaseIngredientMatchFormSet, extra=0,
    max_num=200, absolute_max=200, validate_max=True)
