# Generated by Django 3.0.5 on 2021-07-15 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20210628_1128'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingredient',
            name='linked_recipe',
        ),
        migrations.AddField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(blank=True, to='recipes.Ingredient'),
        ),
    ]