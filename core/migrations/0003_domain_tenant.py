# Generated migration to add django-tenants tenant_id field to Domain

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_schema_name'),
    ]

    operations = [
        # Remove the incorrect school field
        migrations.RemoveField(
            model_name='domain',
            name='school',
        ),
        # Add the correct tenant field that django-tenants expects
        migrations.AddField(
            model_name='domain',
            name='tenant',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='domains',
                to='core.school',
                default=1,  # This will be removed after migration
            ),
            preserve_default=False,
        ),
    ]
