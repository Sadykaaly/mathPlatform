from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from common.models import TimestampAbstractModel
from common.utils import generate_filename
from courses.fields import OrderField
from accounts.models import User


class Subject(MPTTModel, TimestampAbstractModel):
    class Meta:
        verbose_name_plural = _('Subjects')
        verbose_name = _('Subject')
        ordering = ['title']

    title = models.CharField(max_length=200, verbose_name=_('Title'))
    slug = models.SlugField(max_length=200, unique=True, verbose_name='SLUG')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                            verbose_name=_('Parent'))

    def get_absolute_url(self):
        return reverse('course_list_subject', kwargs={'subject': self.slug})

    def __str__(self):
        return self.title


class Course(TimestampAbstractModel):
    class Meta:
        verbose_name_plural = _('Courses')
        verbose_name = _('Course')

    owner = models.ForeignKey(to='accounts.User', null=True, blank=False, on_delete=models.SET_NULL,
                              related_name='courses_created', verbose_name=_('Owner'))
    subject = models.ForeignKey(to='Subject', null=True, blank=False, on_delete=models.SET_NULL, related_name='course',
                                verbose_name=_('subject'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    slug = models.SlugField(max_length=255, unique=True, verbose_name='SLUG')
    description = models.TextField(verbose_name=_('Description'))
    image = models.FileField(upload_to=generate_filename, verbose_name=_('Image'))
    students = models.ManyToManyField(to='accounts.User',
                                      related_name='courses_joined',
                                      blank=True,
                                      verbose_name=_('Students'))
    enrollment_key = models.CharField(max_length=128, null=True, blank=True, verbose_name=_('Enrollment Key'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('Is Deleted?'))

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class Module(TimestampAbstractModel):
    class Meta:
        verbose_name_plural = _('Module')
        verbose_name = _('Module')
        ordering = ['order']

    course = models.ForeignKey(to='Course', related_name='module', on_delete=models.CASCADE, verbose_name=_('Course'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('description'))
    order = OrderField(blank=True, for_fields=['course'])

    def __str__(self):
        return '{}. {}'.format(self.order, self.title)


class Content(TimestampAbstractModel):
    class Meta:
        verbose_name_plural = _('Content')
        verbose_name = _('Content')
        ordering = ['order']

    TEXT = 'text'
    VIDEO = 'video'
    IMAGE = 'image'
    FILE = 'file'
    QUIZ = 'quiz'

    CONTENT_TYPE_LIST = [TEXT, VIDEO, IMAGE, FILE, QUIZ]

    module = models.ForeignKey(Module,
                               related_name='contents',
                               on_delete=models.CASCADE,
                               verbose_name=_('Module'))
    content_type = models.ForeignKey(ContentType,
                                     limit_choices_to={'model__in': (TEXT,
                                                                     VIDEO,
                                                                     IMAGE,
                                                                     FILE,
                                                                     QUIZ)},
                                     on_delete=models.CASCADE,
                                     verbose_name=_('Content Type'))
    object_id = models.PositiveIntegerField(verbose_name=_('Object id'))
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])


class ItemBase(TimestampAbstractModel):
    owner = models.ForeignKey(User,
                              related_name='%(class)s_related',
                              on_delete=models.CASCADE,
                              verbose_name=_('Owner'))
    title = models.CharField(max_length=250, verbose_name=_('Title'))

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    def render(self):
        return render_to_string('courses/content/{}.html'.format(
            self._meta.model_name), {'item': self})


class Text(ItemBase):
    class Meta:
        verbose_name_plural = _('Text')
        verbose_name = _('Text')

    content = models.TextField(verbose_name=_('Content'))


class File(ItemBase):
    class Meta:
        verbose_name_plural = _('File')
        verbose_name = _('File')

    file = models.FileField(upload_to=generate_filename, verbose_name=_('File'))


class Image(ItemBase):
    class Meta:
        verbose_name_plural = _('Image')
        verbose_name = _('Image')

    image = models.FileField(upload_to=generate_filename, verbose_name=_('Image'))


class Video(ItemBase):
    class Meta:
        verbose_name_plural = _('Video')
        verbose_name = _('Video')

    url = models.URLField(verbose_name=_('Url'))


class Quiz(ItemBase):
    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    course = models.ForeignKey(verbose_name='Course', to='Course', related_name='quizzes', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(
        blank=True, verbose_name=_("Description"),
        help_text=_("a description of the quiz"))
    slug = models.SlugField(
        max_length=60, blank=False,
        verbose_name=_("SLUG"))
    theme = models.ForeignKey(
        to="themes.Theme", null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name=_("Theme"))
    max_questions = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("Max Questions"),
        help_text=_("Number of questions to be answered on each attempt."))
    answers_at_end = models.BooleanField(
        blank=False, default=False,
        help_text=_("Correct answer is NOT shown after question."
                    " Answers displayed at the end."),
        verbose_name=_("Answers at end"))
    single_attempt = models.BooleanField(
        blank=False, default=False,
        help_text=_("If yes, only one attempt by"
                    " a user will be permitted."),
        verbose_name=_("Single Attempt"))
    max_attempts = models.PositiveSmallIntegerField(
        blank=True, null=True, default=2,
        verbose_name=_('Max attempts'),
        help_text=_('Number of attempts available to pass'))
    pass_mark = models.SmallIntegerField(
        blank=True, default=0,
        verbose_name=_("Pass Mark"),
        help_text=_("Percentage required to pass exam."),
        validators=[MaxValueValidator(100)])
    success_text = models.TextField(
        blank=True, help_text=_("Displayed if user passes."),
        verbose_name=_("Success Text"))
    fail_text = models.TextField(
        verbose_name=_("Fail Text"),
        blank=True, help_text=_("Displayed if user fails."))
    draft = models.BooleanField(
        blank=True, default=False,
        verbose_name=_("Draft"),
        help_text=_("If yes, the quiz is not displayed"
                    " in the quiz list and can only be"
                    " taken by users who can edit"
                    " quizzes."))

    time_limit = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Time limit'),
        help_text=_('Time limit from starting of quiz in minutes')
    )
    start_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name=_('Start DateTime'),
        help_text=_('Open access for quiz in show datetime'))
    end_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name=_('End DateTime'),
        help_text=_('Close access for quiz in given datetime'))

    def get_questions(self):
        return self.question.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()

    @property
    def get_attempts_count(self):
        if self.max_attempts == 1:
            return _(f'{self.max_attempts} time')
        return _(f'{self.max_attempts} times')

    def get_absolute_url(self):
        return reverse('quiz_start', kwargs={'slug': self.slug})