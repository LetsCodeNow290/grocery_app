# Generated by Django 3.0.5 on 2021-01-11 16:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0002_auto_20210111_1137'),
        ('recipes', '0002_auto_20201222_1442'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Ingredients',
            new_name='Ingredient',
        ),
    ]
