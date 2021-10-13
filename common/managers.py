from django.db import models

from .querysets import SoftDeleteQuerySet


class SoftDeleteManagerMixin:
    queryset_class = SoftDeleteQuerySet

    def __init__(self, *args, **kwargs):
        self.with_deleted = kwargs.pop('with_deleted', False)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = self.queryset_class(self.model).all()

        if self.with_deleted:
            return qs

        return qs.filter(is_deleted=False)


class SoftDeleteManager(SoftDeleteManagerMixin, models.Manager):
    use_in_migrations = True
