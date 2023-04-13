from django.db import models
from app_components.models import *

class FoodAisle(models.Model):
    food_name_for_store = models.ForeignKey(
        'app_components.Food', 
        on_delete=models.CASCADE, 
        related_name='food_name_for_store'
        )
    aisle_in_store = models.ForeignKey(
        'app_components.Aisle', 
        on_delete=models.CASCADE, 
        related_name='food_aisle', 
        blank=True, 
        null=True, 
        default=Aisle.get_default_pk
        )



class GroceryStore(models.Model):
    store_name = models.CharField(max_length=100)
    store_address = models.CharField(max_length=200)
    food_aisle_relationship = models.ManyToManyField(
        FoodAisle, 
        related_name='food_aisle_relationship', 
        blank=True
        )

# Complete this function to return and aisle with a corresponding food name
    def return_aisle(self, food_name):
        if food_name in self.food_aisle_relationship.all():
            return
