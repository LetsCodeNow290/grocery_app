from django.db import models
from app_components.models import *
from PIL import Image

RECIPE_RATING = (
    ("Don't make this again", "Don't make this again"),
    ("Haven't Made it Yet", "Haven't Made it yet"),
    ("Not bad", "Not bad"),
    ("Pretty good", "Pretty good"),
    ("Excellent", "Excellent"),
)


class Recipe(models.Model):
    recipe_name = models.CharField(max_length=100)
    recipe_category = models.ForeignKey('app_components.RecipeCategory', on_delete=models.CASCADE, related_name='recipe_category')
    recipe_image = models.ImageField(blank=True, null=True, default="default.jpg", upload_to="recipe_pics/")
    recipe_instructions = models.TextField(blank=True, null=True)
    recipe_location = models.ForeignKey('app_components.RecipeBook', on_delete=models.CASCADE, related_name='recipe_location', blank=True, null=True)
    location_page_number = models.IntegerField(blank=True, null=True)
    ingredients = models.ManyToManyField('Ingredient', blank=True)
    recipe_rating = models.CharField(blank=True, null=True,default='good', choices=RECIPE_RATING, max_length=50)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.recipe_name
    
    # This bit allows the instructions to have line breaks. Right now it works after each sentence
    @property
    def recipe_instructions_list(self):
        return self.recipe_instructions.splitlines()

    # These next lines are meant to store the files at a smaller size, but it wouldn't work
    def save(self, *args, **kwargs):
        self.recipe_name = self.recipe_name.title()
        super().save(*args, **kwargs)

        img = Image.open(self.recipe_image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.recipe_image.path)
        super().save(*args, **kwargs)

UNITS = [
    ('teaspoon(s)', 'teaspoon(s)'),
    ('TABLESPOON(s)','TABLESPOON(s)'),
    ('cup(s)', 'cup(s)'),
    ('pint(s)', 'pint(s)'),
    ('quart(s)', 'quart(s)'),
    ('gallon(s)', 'gallon(s)'),
    ('ounce(s)', 'ounce(s)'),
    ('pound(s)', 'pound(s)'),
    ('vegetable or fruit', 'vegetable or fruit'),
    ('other', 'other'),
]

class Ingredient(models.Model):
    ingredient_name = models.ForeignKey('app_components.Food', on_delete=models.CASCADE, related_name='ingredient_name')
    ingredient_quantity = models.FloatField()
    quantity_unit = models.CharField(max_length=20, choices=UNITS)

    def __str__(self):
        return self.ingredient_name.food_name

    class Meta():
        ordering = ['ingredient_name']
