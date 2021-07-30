from django.db import models
from components.models import *
from PIL import Image


class Recipe(models.Model):
    recipe_name = models.CharField(max_length=100)
    recipe_category = models.ForeignKey(
        'components.RecipeCategory', on_delete=models.CASCADE, related_name='recipe_category')
    recipe_image = models.ImageField(
        blank=True, null=True, default="default.jpg", upload_to="recipe_pics/")
    recipe_instructions = models.TextField(blank=True, null=True)
    recipe_location = models.ForeignKey(
        'components.RecipeBook', on_delete=models.CASCADE, related_name='recipe_location', blank=True, null=True)
    location_page_number = models.IntegerField(blank=True, null=True)
    ingredients = models.ManyToManyField('Ingredient', blank=True)

    def __str__(self):
        return self.recipe_name

    # These next lines are meant to store the files at a smaller size, but it wouldn't work
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.recipe_image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.recipe_image.path)


class Ingredient(models.Model):
    ingredient_name = models.ForeignKey(
        'components.Food', on_delete=models.CASCADE, related_name='ingredient_name')
    # linked_recipe = models.ForeignKey(
    #     'Recipe', on_delete=models.CASCADE, related_name='linked_recipe')
    # linked_recipe = models.CharField(max_length=100)
    ingredient_quantity = models.FloatField()
    quantity_unit = models.ForeignKey(
        'components.MeasuringUnit', on_delete=models.CASCADE, related_name='quantity_unit')

    def __str__(self):
        return self.ingredient_name.food_name
