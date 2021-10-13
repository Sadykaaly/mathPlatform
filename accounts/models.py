from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from accounts.managers import UserManager
from common.models import TimestampAbstractModel
from common.utils import generate_filename


class User(AbstractBaseUser, PermissionsMixin, TimestampAbstractModel):
    class Meta:
        verbose_name_plural = _('Users')
        verbose_name = _('User')
        ordering = ('-created_at',)

    INSTRUCTOR = 'instructor'
    STUDENT = 'student'

    USER_TYPE_LIST = [
        INSTRUCTOR, STUDENT
    ]
    USER_TYPE = (
        (INSTRUCTOR, _('Instructor')),
        (STUDENT, _('Student'))
    )

    MALE = 'male'
    FEMALE = 'female'

    USER_GENDER_LIST = [
        MALE, FEMALE
    ]

    USER_GENDER_TYPE = (
        (MALE, _('Male')),
        (FEMALE, _('Female'))
    )

    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        null=True,
        blank=True,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(max_length=255, unique=True, verbose_name=_('E-mail'))
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Name'))
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Surname'))
    date_of_birth = models.DateField(blank=True, null=True, verbose_name=_('Date of Birth'))
    gender = models.CharField(max_length=20, blank=True, null=True, choices=USER_GENDER_TYPE, verbose_name=_('Gender'))
    avatar = models.FileField(upload_to=generate_filename, verbose_name=_('Avatar'), null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, verbose_name='SLUG')

    is_staff = models.BooleanField(default=False, verbose_name=_('Is Staff?'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active?'))

    is_deleted = models.BooleanField(default=False, verbose_name=_('Is Deleted?'))
    user_type = models.CharField(max_length=20, choices=USER_TYPE, default=STUDENT,
                                 verbose_name=_('Type'))
    objects = UserManager()
    objects_with_deleted = UserManager(with_deleted=True)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name) if self.first_name and self.last_name else None

    @property
    def full_name_or_email(self):
        return self.full_name or self.email

    def is_instructor(self):
        if self.user_type == self.INSTRUCTOR:
            return True
        return False

    def _create_slug(self, new_slug=None):
        slug = self.email
        if new_slug is not None:
            slug = new_slug
        qs = User.objects.filter(slug=slug).order_by("-id")
        exists = qs.exists()
        if exists:
            new_slug = "%s-%s" % (slug, qs.first().id)
            return self._create_slug(new_slug=new_slug)
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._create_slug()
        super(User, self).save(*args, **kwargs)
