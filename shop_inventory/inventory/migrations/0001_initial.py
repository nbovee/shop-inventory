# Generated by Django 4.2.13 on 2024-07-25 02:51

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, unique=True)),
                ('variant', models.CharField(max_length=30)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, unique=True)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('barcode', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('quantity', models.PositiveIntegerField()),
                ('base_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.baseitem')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.location')),
            ],
            options={
                'unique_together': {('base_item', 'location')},
            },
        ),
    ]
