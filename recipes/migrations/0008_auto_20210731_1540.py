# Generated by Django 3.0.5 on 2021-07-31 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_recipe_recipe_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='recipe_rating',
            field=models.IntegerField(choices=[(1, "Don't make this again"), (2, 'Not bad'), (3, 'Pretty good'), (4, 'Excellent')], default=3),
        ),
    ]
