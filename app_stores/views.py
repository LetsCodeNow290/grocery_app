from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.forms.models import model_to_dict
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect



# Must ceate a view that creates a store, a view to add the store to session data, and a view to make food/aisle relationships in stroes.

def choose_store(request):
    if request.method == "POST":
        form = SessionStoreForm(request.POST or None)
        if form.is_valid():
            form_store_name = form.cleaned_data.get("choose_a_store")
            request.session["store_pk"] = form_store_name.id
            request.session["store_name"] = form_store_name.store_name
            request.session["store_address"] = form_store_name.store_address
            return redirect("home")
    else:
        form = SessionStoreForm()
    return render(request, "app_stores/choose_store.html", {"form": form})


class CreateStore(CreateView):
    model = GroceryStore
    fields = [
        "store_name",
        "store_address",
    ]
    template_name_suffix = '_add'
    success_url = reverse_lazy('choose_store')

    def get_context_data(self, **kwargs):
        kwargs['all_stores'] = GroceryStore.objects.all()
        return super().get_context_data(**kwargs)

class UpdateStore(UpdateView):
    model = GroceryStore
    #complete this

class DeleteStore(DeleteView):
    model = GroceryStore
    #Complete this too

def store_food_to_aisle(request):
    if 'store_name' in request.session:
        store_pk = request.session['store_pk']
        validation_set = GroceryStore.objects.get(pk=store_pk)
        if request.method == "POST":
            food_to_aisle_form = FoodAisleStoreForm(request.POST or None)
            if food_to_aisle_form.is_valid():
                food_to_aisle_form.save(commit=False)
                form_food = food_to_aisle_form.cleaned_data.get('food_name_for_store')
                if validation_set.food_aisle_relationship.filter(food_name_for_store=form_food).exists():          
                    messages.error(request, f"{str(form_food)} is already in the database")
                    return redirect(request.path)
                food_to_aisle_form.save()
                GroceryStore.objects.get(pk=store_pk).food_aisle_relationship.add(FoodAisle.objects.get(pk=food_to_aisle_form.save().pk))
                return HttpResponseRedirect(request.path_info)
        else:
            food_to_aisle_form = FoodAisleStoreForm()
            quick_choose_store_form = None
            food_aisle_list = GroceryStore.objects.get(pk=store_pk).food_aisle_relationship.all()
        return render(request, "app_stores/food_to_aisle.html", {"quick_choose_store_form": quick_choose_store_form, 'food_to_aisle_form' : food_to_aisle_form, 'food_aisle_list' : food_aisle_list})
    else:
        if request.method == "POST":
            quick_choose_store_form = SessionStoreForm(request.POST or None)
            if quick_choose_store_form.is_valid():
                form_store_name = quick_choose_store_form.cleaned_data.get("choose_a_list")
                request.session["store_pk"] = form_store_name.id
                request.session["store_name"] = form_store_name.store_name
                request.session["store_address"] = form_store_name.store_address
                return HttpResponseRedirect(request.path_info)
        else:
            food_to_aisle_form = None
            quick_choose_store_form = SessionStoreForm()

        return render(request, "app_stores/food_to_aisle.html", {"quick_choose_store_form": quick_choose_store_form, 'food_to_aisle_form' : food_to_aisle_form})

