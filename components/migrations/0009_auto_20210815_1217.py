# Generated by Django 3.0.5 on 2021-08-15 16:17

import components.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0008_food_food_aisle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='food',
            name='food_name',
            field=models.CharField(max_length=100, validators=[components.models.food_de_dup_validation]),
        ),
    ]
