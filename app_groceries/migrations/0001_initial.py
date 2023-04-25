# Generated by Django 3.0.5 on 2023-04-24 18:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_recipes', '0001_initial'),
        ('app_stores', '0001_initial'),
        ('app_components', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChooseItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_quantity', models.FloatField()),
                ('item_quantity_unit', models.CharField(choices=[('teaspoon(s)', 'teaspoon(s)'), ('TABLESPOON(s)', 'TABLESPOON(s)'), ('cup(s)', 'cup(s)'), ('pint(s)', 'pint(s)'), ('quart(s)', 'quart(s)'), ('gallon(s)', 'gallon(s)'), ('ounce(s)', 'ounce(s)'), ('pound(s)', 'pound(s)'), ('vegetable or fruit', 'vegetable or fruit'), ('other', 'other')], default='other', max_length=20)),
                ('item_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item_name', to='app_components.Food')),
            ],
        ),
        migrations.CreateModel(
            name='GroceryList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('list_name', models.DateField()),
                ('list_items', models.ManyToManyField(blank=True, related_name='items_list', to='app_groceries.ChooseItem')),
            ],
        ),
        migrations.CreateModel(
            name='GroceryListRecipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe_quantity', models.PositiveIntegerField(default=1)),
                ('grocery_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_groceries.GroceryList')),
                ('recipe_from_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_recipes.Recipe')),
            ],
        ),
        migrations.AddField(
            model_name='grocerylist',
            name='list_recipes',
            field=models.ManyToManyField(blank=True, related_name='recipe_list', through='app_groceries.GroceryListRecipe', to='app_recipes.Recipe'),
        ),
        migrations.AddField(
            model_name='grocerylist',
            name='list_store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='list_store', to='app_stores.GroceryStore'),
        ),
    ]
