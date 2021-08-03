# Generated by Django 3.0.5 on 2021-08-02 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0010_auto_20210731_1911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='recipe_rating',
            field=models.CharField(blank=True, choices=[("Don't make this again", "Don't make this again"), ('Not bad', 'Not bad'), ('Pretty good', 'Pretty good'), ('Excellent', 'Excellent')], default='good', max_length=50, null=True),
        ),
    ]