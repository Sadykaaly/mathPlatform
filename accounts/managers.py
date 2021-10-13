from django.contrib.auth.base_user import BaseUserManager

from common.managers import SoftDeleteManagerMixin
from common.querysets import SoftDeleteQuerySet


class UserSoftDeleteQuerySet(SoftDeleteQuerySet):
    def delete(self):
        return super().update(is_deleted=True, is_active=False)


class UserSoftDeleteManagerMixin(SoftDeleteManagerMixin):
    queryset_class = UserSoftDeleteQuerySet


class UserManager(UserSoftDeleteManagerMixin, BaseUserManager):
    """Custom user manager for User model with an email as a username"""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self._create_user(email, password, **extra_fields)

