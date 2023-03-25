# Generated by Django 3.0.5 on 2023-03-23 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0012_auto_20210803_0939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='recipe_rating',
            field=models.CharField(blank=True, choices=[("Don't make this again", "Don't make this again"), ("Haven't Made it Yet", "Haven't Made it yet"), ('Not bad', 'Not bad'), ('Pretty good', 'Pretty good'), ('Excellent', 'Excellent')], default='good', max_length=50, null=True),
        ),
    ]
