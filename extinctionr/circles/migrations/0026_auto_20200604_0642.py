# Generated by Django 3.0.6 on 2020-06-04 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('circles', '0025_auto_20200604_0638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='volunteerrequest',
            name='updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]