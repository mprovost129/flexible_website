from django.db import migrations, models


def default_navbar_config():
    return {
        'height_px': 76,
        'padding_x': 0.0,
        'padding_y': 0.4,
        'gap_px': 12,
        'brand_size_rem': 1.6,
        'link_size_rem': 1.0,
        'radius_px': 999,
        'border_width_px': 0,
        'bg_color': '',
        'text_color': '',
        'link_color': '',
        'link_hover_bg': '',
        'link_hover_color': '',
        'container_max_px': 1320,
    }


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_universal_navbar_engine'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='navbar_config',
            field=models.JSONField(
                blank=True,
                default=default_navbar_config,
                help_text='Advanced navbar layout/style controls (v1).',
            ),
        ),
    ]

