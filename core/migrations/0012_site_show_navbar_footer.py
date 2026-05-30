from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_site_navbar_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='show_footer',
            field=models.BooleanField(default=True, help_text='Render the footer on public pages.'),
        ),
        migrations.AddField(
            model_name='site',
            name='show_navbar',
            field=models.BooleanField(default=True, help_text='Render the navbar on public pages.'),
        ),
    ]

