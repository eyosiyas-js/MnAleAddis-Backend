# Generated by Django 3.0.5 on 2021-12-12 19:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import djongo.models.fields
import location_field.models.plain


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0030_auto_20211212_2234'),
    ]

    operations = [
        migrations.CreateModel(
            name='GraduationEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('price', models.FloatField(default=0)),
                ('description', models.CharField(max_length=250)),
                ('startDate', models.DateTimeField()),
                ('venue', models.CharField(default='', max_length=200)),
                ('location', location_field.models.plain.PlainLocationField(default='', max_length=63)),
                ('phones', djongo.models.fields.JSONField()),
                ('image_url', models.URLField(blank=True)),
                ('maxNoOfAttendees', models.IntegerField(default=100)),
                ('noOfViews', models.IntegerField(default=0)),
                ('isHidden', models.BooleanField(default=False)),
                ('eventkey', models.CharField(max_length=20)),
                ('minPercentageToPay', models.FloatField()),
                ('createdBy', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
