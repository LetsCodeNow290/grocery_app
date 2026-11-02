from django.db import models
from recipes.units import UNITS
from components.models import *

RECIPE_RATING = (
    ("Don't make this again", "Don't make this again"),
    ("Haven't Made it Yet", "Haven't Made it yet"),
    ("Not bad", "Not bad"),
    ("Pretty good", "Pretty good"),
    ("Excellent", "Excellent"),
)


class Recipe(models.Model):
    recipe_name = models.CharField(max_length=100)
    recipe_category = models.ForeignKey(
        'components.RecipeCategory', on_delete=models.CASCADE, related_name='recipe_category')
    recipe_image = models.ImageField(
        blank=True, null=True, default="default.jpg", upload_to="recipe_pics/")
    recipe_instructions = models.TextField(blank=True, null=True)
    source_url = models.URLField(max_length=2048, blank=True)
    ingredient_text = models.TextField(blank=True, help_text=(
        'Original ingredient lines are retained alongside confirmed grocery-list ingredients.'))
    ingredient_review_exclusions = models.JSONField(default=list, blank=True, editable=False)
    recipe_location = models.ForeignKey(
        'components.RecipeBook', on_delete=models.CASCADE, related_name='recipe_location', blank=True, null=True)
    location_page_number = models.IntegerField(blank=True, null=True)
    ingredients = models.ManyToManyField('Ingredient', blank=True)
    recipe_rating = models.CharField(blank=True, null=True,
                                     default='good', choices=RECIPE_RATING, max_length=50)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.recipe_name

    def save(self, *args, **kwargs):
        self.recipe_name = self.recipe_name.title()
        super().save(*args, **kwargs)




class Ingredient(models.Model):
    ingredient_name = models.ForeignKey(
        'components.Food', on_delete=models.CASCADE, related_name='ingredient_name')
    ingredient_quantity = models.FloatField()
    quantity_unit = models.CharField(max_length=20, choices=UNITS)

    original_text = models.TextField(blank=True)
    preparation_notes = models.TextField(blank=True)
    quantity_max = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.ingredient_name.food_name

    class Meta():
        ordering = ['ingredient_name']
