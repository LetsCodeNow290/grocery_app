from django.db import models
from PIL import Image


class MeasuringUnit(models.Model):
    unit_name = models.CharField(max_length=20)

    def __str__(self):
        return self.unit_name


class Food(models.Model):
    food_name = models.CharField(max_length=100)
    food_category = models.ForeignKey(
        'FoodCategory', on_delete=models.CASCADE, related_name='food_category')
    food_aisle = models.ForeignKey(
        'Aisle', on_delete=models.CASCADE, related_name='food_aisle', blank=True, null=True)

    def __str__(self):
        return self.food_name

    class Meta():
        ordering = ['food_aisle']


class RecipeCategory(models.Model):
    recipe_category_name = models.CharField(max_length=100)

    def __str__(self):
        return self.recipe_category_name


class FoodCategory(models.Model):
    food_category_name = models.CharField(max_length=30)

    def __str__(self):
        return self.food_category_name


class Aisle(models.Model):
    aisle_name = models.CharField(max_length=20)

    def __str__(self):
        return self.aisle_name


class RecipeBook(models.Model):
    book_name = models.CharField(max_length=100)
    recipe_book_image = models.ImageField(
        blank=True, null=True, default="default_book.jpg", upload_to="recipe_book_pics/")

    def __str__(self):
        return self.book_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.recipe_book_image.path)
        #img = img.rotate(-90)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.recipe_book_image.path)
