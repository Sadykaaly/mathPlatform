from django.db.models import QuerySet


class SoftDeleteQuerySet(QuerySet):
    def hard_delete(self):
        return super().delete()

    def delete(self):
        return super().update(is_deleted=True)
