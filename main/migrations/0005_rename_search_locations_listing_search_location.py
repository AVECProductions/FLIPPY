# Generated by Django 5.0.1 on 2025-03-30 19:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_rename_search_location_listing_search_locations'),
    ]

    operations = [
        migrations.RenameField(
            model_name='listing',
            old_name='search_locations',
            new_name='search_location',
        ),
    ]
