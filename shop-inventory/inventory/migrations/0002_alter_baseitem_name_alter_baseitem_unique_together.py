# Generated by Django 4.2.16 on 2024-11-26 04:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="baseitem",
            name="name",
            field=models.CharField(max_length=30),
        ),
        migrations.AlterUniqueTogether(
            name="baseitem",
            unique_together={("name", "variant")},
        ),
    ]
