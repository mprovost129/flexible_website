from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sandbox', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sandboxsession',
            name='site_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
