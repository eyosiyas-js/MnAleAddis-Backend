# Generated by Django 3.0.5 on 2021-12-10 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_survey_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyresponse',
            name='timestamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
