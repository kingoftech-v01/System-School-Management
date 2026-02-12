import uuid


class AuditedModelMixin:
    """
    Mixin that automatically tracks field-level changes on save().

    Usage:
        class MyModel(AuditedModelMixin, models.Model):
            AUDITED_FIELDS = ['name', 'status', 'phone']
            ...

    The mixin compares old vs new values for fields listed in AUDITED_FIELDS
    and creates FieldChangeRecord entries for any differences.

    Pass _audit_user, _audit_reason, or _skip_audit as kwargs to save().
    """

    # Override in subclass: list of field names to track
    AUDITED_FIELDS = []

    # Override in subclass: fields to exclude even if in AUDITED_FIELDS
    AUDIT_EXCLUDE_FIELDS = ['updated_at', 'password']

    def save(self, *args, **kwargs):
        audit_user = kwargs.pop('_audit_user', None)
        audit_reason = kwargs.pop('_audit_reason', None)
        skip_audit = kwargs.pop('_skip_audit', False)

        if skip_audit or not self.AUDITED_FIELDS:
            return super().save(*args, **kwargs)

        is_new = self.pk is None
        old_values = {}

        if not is_new:
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                for field in self.AUDITED_FIELDS:
                    if field not in self.AUDIT_EXCLUDE_FIELDS:
                        old_values[field] = str(
                            getattr(old_instance, field, '') or ''
                        )
            except self.__class__.DoesNotExist:
                is_new = True

        result = super().save(*args, **kwargs)

        # Import here to avoid circular imports
        from audit.middleware import get_current_user
        from audit.models import FieldChangeRecord
        from django.contrib.contenttypes.models import ContentType

        if audit_user is None:
            audit_user = get_current_user()

        ct = ContentType.objects.get_for_model(self)
        batch = uuid.uuid4()

        records = []
        for field_name in self.AUDITED_FIELDS:
            if field_name in self.AUDIT_EXCLUDE_FIELDS:
                continue

            new_val = str(getattr(self, field_name, '') or '')

            if is_new:
                records.append(FieldChangeRecord(
                    content_type=ct,
                    object_id=self.pk,
                    field_name=field_name,
                    field_verbose_name=self._get_field_verbose_name(field_name),
                    old_value=None,
                    new_value=new_val,
                    changed_by=audit_user,
                    change_reason=audit_reason or '',
                    batch_id=batch,
                    action='create',
                ))
            else:
                old_val = old_values.get(field_name, '')
                if old_val != new_val:
                    records.append(FieldChangeRecord(
                        content_type=ct,
                        object_id=self.pk,
                        field_name=field_name,
                        field_verbose_name=self._get_field_verbose_name(
                            field_name
                        ),
                        old_value=old_val,
                        new_value=new_val,
                        changed_by=audit_user,
                        change_reason=audit_reason or '',
                        batch_id=batch,
                        action='update',
                    ))

        if records:
            FieldChangeRecord.objects.bulk_create(records)

        return result

    def _get_field_verbose_name(self, field_name):
        try:
            return str(self._meta.get_field(field_name).verbose_name)
        except Exception:
            return field_name
