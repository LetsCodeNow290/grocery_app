# Generated by Django 3.0.5 on 2021-06-28 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_auto_20210628_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='recipe_image',
            field=models.ImageField(blank=True, default='default.jpg', null=True, upload_to='recipe_pics/'),
        ),
    ]
