# Manual migration to add django-tenants fields for production
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Add schema_name field from TenantMixin
        migrations.AddField(
            model_name='school',
            name='schema_name',
            field=models.CharField(max_length=63, unique=True, db_index=True, default='public'),
            preserve_default=False,
        ),
        # Rename Domain.school to Domain.tenant (DomainMixin convention)
        migrations.RenameField(
            model_name='domain',
            old_name='school',
            new_name='tenant',
        ),
        # Update School Meta to match TenantMixin
        migrations.AlterModelOptions(
            name='school',
            options={'verbose_name': 'School (Tenant)', 'verbose_name_plural': 'Schools (Tenants)', 'ordering': ['name']},
        ),
    ]
