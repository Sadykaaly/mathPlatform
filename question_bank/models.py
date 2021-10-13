from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from common.models import TimestampAbstractModel
from django.utils.translation import ugettext_lazy as _

from courses.fields import OrderField
from courses.models import Quiz
from quiz.models import Question
from themes.models import Theme

User = get_user_model()


class QuestionBank(TimestampAbstractModel):
    class Meta:
        verbose_name = 'Question Bank'
        verbose_name_plural = 'question Banks'

    owner = models.ForeignKey(User,
                              related_name='bank',
                              on_delete=models.CASCADE,
                              verbose_name=_('Owner'))
    theme = models.ForeignKey(Theme,
                              related_name='bank',
                              on_delete=models.SET_NULL,
                              verbose_name=_('Theme'),
                              null=True, blank=True)
    title = models.CharField(max_length=250, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    is_active = models.BooleanField(default=False, verbose_name=_('Is active?'))
    quizzes = models.ManyToManyField(Quiz, related_name='question_banks', blank=True)
    questions = models.ManyToManyField(Question, related_name='question_banks', blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('question_bank_detail', kwargs={'pk': self.pk})


class QuestionBankContent(TimestampAbstractModel):
    MCQ = 'mcquestion'
    ESSAY = 'essayquestion'
    TF = 'tfquestion'

    QUESTION_TYPE = (
        (MCQ, 'Multiple choice'),
        (ESSAY, 'Essay'),
        (TF, 'True/False'),
    )

    QUESTION_TYPE_LIST = [MCQ, ESSAY, TF]

    question_bank = models.ForeignKey(QuestionBank,
                                      related_name='content',
                                      on_delete=models.CASCADE,
                                      verbose_name=_('Quiz Content'))
    content_type = models.ForeignKey(ContentType,
                                     limit_choices_to={'model__in': set(QUESTION_TYPE_LIST)},
                                     on_delete=models.CASCADE,
                                     verbose_name=_('Content Type'))
    object_id = models.PositiveIntegerField(verbose_name=_('Object id'))
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['question_bank'])
