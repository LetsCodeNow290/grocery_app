from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import *

admin.site.register(Session)
admin.site.register(Aisle)
admin.site.register(Food)
admin.site.register(FoodCategory)
admin.site.register(RecipeBook)
admin.site.register(RecipeCategory)