# Generated by Django 3.0.6 on 2020-05-19 21:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('circles', '0021_auto_20200519_1628'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taggedvolunteerrequest',
            old_name='volunteer',
            new_name='content_object',
        ),
    ]