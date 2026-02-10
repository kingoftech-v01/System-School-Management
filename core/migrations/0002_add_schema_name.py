# Generated migration to add django-tenants schema_name field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Add schema_name field to School model (required by django-tenants TenantMixin)
        migrations.AddField(
            model_name='school',
            name='schema_name',
            field=models.CharField(db_index=True, max_length=63, unique=True, default='public'),
            preserve_default=False,
        ),
    ]
