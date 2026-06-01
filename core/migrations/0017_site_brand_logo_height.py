from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_active_pack_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='brand_logo_height',
            field=models.PositiveSmallIntegerField(
                default=32,
                help_text='Logo height in pixels in the navbar (16–120).',
            ),
        ),
    ]
