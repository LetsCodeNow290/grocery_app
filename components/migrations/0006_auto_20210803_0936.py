# Generated by Django 3.0.5 on 2021-08-03 13:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0005_auto_20210802_1613'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='measuringunit',
            options={'ordering': ['unit_name']},
        ),
        migrations.AlterModelOptions(
            name='recipecategory',
            options={'ordering': ['recipe_category_name']},
        ),
    ]