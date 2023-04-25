from django import forms
from .models import *

class SessionStoreForm(forms.Form):
    choose_a_store = forms.ModelChoiceField(GroceryStore.objects.all().order_by('store_name'))

class FoodAisleStoreForm(forms.ModelForm):
    class Meta:
        model = FoodAisle
        fields = '__all__'