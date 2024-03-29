# Generated by Django 3.0.5 on 2023-03-29 18:33

import components.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Aisle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aisle_name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='FoodCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_category_name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='RecipeBook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_name', models.CharField(max_length=100)),
                ('recipe_book_image', models.ImageField(blank=True, default='default_book.jpg', null=True, upload_to='recipe_book_pics/')),
            ],
            options={
                'ordering': ['book_name'],
            },
        ),
        migrations.CreateModel(
            name='RecipeCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe_category_name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['recipe_category_name'],
            },
        ),
        migrations.CreateModel(
            name='Food',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_name', models.CharField(max_length=100)),
                ('food_aisle', models.ForeignKey(blank=True, default=components.models.Aisle.get_default_pk, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='food_aisle', to='components.Aisle')),
                ('food_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='food_category', to='components.FoodCategory')),
            ],
            options={
                'ordering': ['food_name'],
            },
        ),
    ]
