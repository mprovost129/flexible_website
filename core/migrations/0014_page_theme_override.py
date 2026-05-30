from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_merge_20260529_0652'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='inherit_site_theme',
            field=models.BooleanField(default=True, help_text='When enabled, this page uses the site theme.'),
        ),
        migrations.AddField(
            model_name='page',
            name='theme',
            field=models.ForeignKey(blank=True, help_text='Optional page-specific theme when inheritance is disabled.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='page_overrides', to='core.theme'),
        ),
    ]
