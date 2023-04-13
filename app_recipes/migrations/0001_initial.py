# Generated by Django 3.0.5 on 2023-04-11 17:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_components', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ingredient_quantity', models.FloatField()),
                ('quantity_unit', models.CharField(choices=[('teaspoon(s)', 'teaspoon(s)'), ('TABLESPOON(s)', 'TABLESPOON(s)'), ('cup(s)', 'cup(s)'), ('pint(s)', 'pint(s)'), ('quart(s)', 'quart(s)'), ('gallon(s)', 'gallon(s)'), ('ounce(s)', 'ounce(s)'), ('pound(s)', 'pound(s)'), ('vegetable or fruit', 'vegetable or fruit'), ('other', 'other')], max_length=20)),
                ('ingredient_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredient_name', to='app_components.Food')),
            ],
            options={
                'ordering': ['ingredient_name'],
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe_name', models.CharField(max_length=100)),
                ('recipe_image', models.ImageField(blank=True, default='default.jpg', null=True, upload_to='recipe_pics/')),
                ('recipe_instructions', models.TextField(blank=True, null=True)),
                ('location_page_number', models.IntegerField(blank=True, null=True)),
                ('recipe_rating', models.CharField(blank=True, choices=[("Don't make this again", "Don't make this again"), ("Haven't Made it Yet", "Haven't Made it yet"), ('Not bad', 'Not bad'), ('Pretty good', 'Pretty good'), ('Excellent', 'Excellent')], default='good', max_length=50, null=True)),
                ('comments', models.TextField(blank=True, null=True)),
                ('ingredients', models.ManyToManyField(blank=True, to='app_recipes.Ingredient')),
                ('recipe_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe_category', to='app_components.RecipeCategory')),
                ('recipe_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recipe_location', to='app_components.RecipeBook')),
            ],
        ),
    ]