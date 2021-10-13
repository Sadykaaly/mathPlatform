import json
import random
import re
from itertools import chain

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import MaxValueValidator, validate_comma_separated_integer_list
from django.db import models
from django.template.loader import render_to_string
from django.utils.timezone import now
from model_utils.managers import InheritanceManager

from common.models import TimestampAbstractModel
from django.utils.translation import ugettext_lazy as _

from courses.fields import OrderField
from courses.models import ItemBase, Quiz
from themes.models import Theme


class ProgressManager(models.Manager):

    def new_progress(self, user):
        new_progress = self.create(user=user,
                                   score="")
        new_progress.save()
        return new_progress


class Progress(TimestampAbstractModel):
    """
    Progress is used to track an individual signed in users score on different
    quiz's and categories

    Data stored in csv using the format:
        theme, score, possible, score, possible, ...
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)

    score = models.CharField(max_length=1024,
                             verbose_name=_("Score"),
                             validators=[validate_comma_separated_integer_list])

    objects = ProgressManager()

    class Meta:
        verbose_name = _("User Progress")
        verbose_name_plural = _("User progress records")

    @property
    def list_all_cat_scores(self):
        """
        Returns a dict in which the key is the theme name and the item is
        a list of three integers.

        The first is the number of questions correct,
        the second is the possible best score,
        the third is the percentage correct.

        The dict will have one key for every theme that you have defined
        """
        score_before = self.score
        output = {}

        for theme in Theme.objects.all():
            to_find = re.escape(theme.title) + r",(\d+),(\d+),"
            #  group 1 is score, group 2 is highest possible

            match = re.search(to_find, self.score, re.IGNORECASE)

            if match:
                score = int(match.group(1))
                possible = int(match.group(2))

                try:
                    percent = int(round((float(score) / float(possible))
                                        * 100))
                except:
                    percent = 0

                output[theme.title] = [score, possible, percent]

            else:  # if theme has not been added yet, add it.
                self.score += theme.title + ",0,0,"
                output[theme.title] = [0, 0]

        if len(self.score) > len(score_before):
            # If a new theme has been added, save changes.
            self.save()

        return output

    def update_score(self, question, score_to_add=0, possible_to_add=0):
        """
        Pass in question object, amount to increase score
        and max possible.

        Does not return anything.
        """
        theme_test = Theme.objects.filter(title=question.theme) \
            .exists()

        if any([item is False for item in [theme_test,
                                           score_to_add,
                                           possible_to_add,
                                           isinstance(score_to_add, int),
                                           isinstance(possible_to_add, int)]]):
            return _("error"), _("theme does not exist or invalid score")

        to_find = re.escape(str(question.theme)) + \
                  r",(?P<score>\d+),(?P<possible>\d+),"

        match = re.search(to_find, self.score, re.IGNORECASE)

        if match:
            updated_score = int(match.group('score')) + abs(score_to_add)
            updated_possible = int(match.group('possible')) + \
                               abs(possible_to_add)

            new_score = ",".join(
                [
                    str(question.theme),
                    str(updated_score),
                    str(updated_possible), ""
                ])

            # swap old score for the new one
            self.score = self.score.replace(match.group(), new_score)
            self.save()

        else:
            #  if not present but existing, add with the points passed in
            self.score += ",".join(
                [
                    str(question.theme),
                    str(score_to_add),
                    str(possible_to_add),
                    ""
                ])
            self.save()

    def show_exams(self):
        """
        Finds the previous quizzes marked as 'exam papers'.
        Returns a queryset of complete exams.
        """
        return Sitting.objects.filter(user=self.user, complete=True)


class SittingManager(models.Manager):
    def new_sitting(self, user, quiz):

        questions = self._get_questions(quiz)
        question_set = self._get_question_set(questions)

        if len(question_set) == 0:
            raise ImproperlyConfigured('Question set of the quiz is empty. '
                                       'Please configure questions properly')

        if quiz.max_questions and quiz.max_questions < len(question_set):
            question_set = question_set[:quiz.max_questions]

        questions = ",".join(map(str, question_set)) + ","

        new_sitting = self.create(user=user,
                                  quiz=quiz,
                                  question_order=questions,
                                  question_list=questions,
                                  incorrect_questions="",
                                  current_score=0,
                                  complete=False,
                                  user_answers='{}')
        return new_sitting

    def user_sitting(self, user, quiz):
        if quiz.single_attempt is True and self.filter(user=user,
                                                       quiz=quiz,
                                                       complete=True) \
                .exists():
            return False
        elif self.filter(user=user, quiz=quiz, complete=True).count() == quiz.max_attempts:
            return False

        try:
            sitting = self.get(user=user, quiz=quiz, complete=False)
        except Sitting.DoesNotExist:
            sitting = self.new_sitting(user, quiz)
        except Sitting.MultipleObjectsReturned:
            sitting = self.filter(user=user, quiz=quiz, complete=False)[0]
        return sitting

    def _get_questions(self, quiz):
        questions = quiz.question.all()

        for question_bank in quiz.question_banks.filter(is_active=True):
            bank_q = question_bank.questions.all()
            questions = set(chain(questions, bank_q))

        questions_list = list(questions)
        random.shuffle(questions_list)

        return questions_list

    def _get_question_set(self, questions):
        return [item.id for item in questions]


class Sitting(TimestampAbstractModel):
    """
    Used to store the progress of logged in users sitting a quiz.
    Replaces the session system used by anon users.

    Question_order is a list of integer pks of all the questions in the
    quiz, in order.

    Question_list is a list of integers which represent id's of
    the unanswered questions in csv format.

    Incorrect_questions is a list in the same format.

    User_answers is a json object in which the question PK is stored
    with the answer the user gave.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)

    quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"), on_delete=models.CASCADE)

    question_order = models.CharField(
        max_length=1024,
        verbose_name=_("Question Order"),
        validators=[validate_comma_separated_integer_list])

    question_list = models.CharField(
        max_length=1024,
        verbose_name=_("Question List"),
        validators=[validate_comma_separated_integer_list])

    incorrect_questions = models.CharField(
        max_length=1024,
        blank=True,
        verbose_name=_("Incorrect questions"),
        validators=[validate_comma_separated_integer_list])

    current_score = models.IntegerField(verbose_name=_("Current Score"))

    complete = models.BooleanField(default=False, blank=False,
                                   verbose_name=_("Complete"))

    user_answers = models.TextField(blank=True, default='{}',
                                    verbose_name=_("User Answers"))

    start = models.DateTimeField(auto_now_add=True,
                                 verbose_name=_("Start"))

    end = models.DateTimeField(null=True, blank=True, verbose_name=_("End"))

    question_index = models.PositiveSmallIntegerField(null=True, blank=True, default=1, verbose_name='Question index')

    objects = SittingManager()

    class Meta:
        permissions = (("view_sittings", _("Can see completed exams.")),)

    @property
    def _question(self):
        return self.get_question_by_index(self.question_index)

    def get_first_question(self):
        # """
        # Returns the next question.
        # If no question is found, returns False
        # Does NOT remove the question from the front of the list.
        # """
        # if not self.question_list:
        #     return False
        #
        # first, _ = self.question_list.split(',', 1)
        # question_id = int(first)
        # return Question.objects.get_subclass(id=question_id)
        if self._question:
            return self._question
        return False

    def get_question_by_index(self, question_index):
        question_id = self.enumerated_questions.get(question_index, None)
        if question_id:
            return Question.objects.get_subclass(id=question_id)
        return False

    def remove_first_question(self):
        if not self.question_list:
            return

        _, others = self.question_list.split(',', 1)
        self.question_list = others
        self.save(update_fields=['question_list'])

    def change_question_index(self, question_index):
        self.question_index = int(question_index) + 1
        self.save(update_fields=['question_index'])
        return self.question_index

    @property
    def enumerated_questions(self):
        return {key: value for key, value in enumerate(self.question_order.split(','), 1) if value}

    @property
    def get_enumerated_questions(self):
        return [key for key, value in enumerate(self.question_order.split(','), 1) if value]

    def add_to_score(self, points):
        self.current_score += int(points)
        self.save(update_fields=['current_score'])

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):
        return [int(n) for n in self.question_order.split(',') if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0  # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = now()
        self.save(update_fields=['complete', 'end'])

    def add_incorrect_question(self, question):
        """
        Adds uid of incorrect question to the list.
        The question object must be passed in.
        """
        self.incorrect_questions += str(question.id) + ","
        if self.complete:
            self.add_to_score(-1)
        self.save()

    def is_question_incorrect(self, question):
        if str(question) in self.incorrect_questions.split(','):
            return True
        return False

    @property
    def get_incorrect_questions(self):
        """
        Returns a list of non empty integers, representing the pk of
        questions
        """
        return [int(q) for q in self.incorrect_questions.split(',') if q]

    def remove_incorrect_question(self, question):
        current = self.get_incorrect_questions
        current.remove(question.id)
        self.incorrect_questions = ','.join(map(str, current))
        self.add_to_score(1)
        self.save()

    @property
    def check_if_passed(self):
        return self.get_percent_correct >= self.quiz.pass_mark

    @property
    def result_message(self):
        if self.check_if_passed:
            return self.quiz.success_text
        else:
            return self.quiz.fail_text

    def add_user_answer(self, question, guess):
        current = json.loads(self.user_answers)
        current[question.id] = guess
        self.user_answers = json.dumps(current)
        self.save()

    def get_question_set(self):
        questions = self.quiz.question.all()

        for question_bank in self.quiz.question_banks.filter(is_active=True):
            bank_q = question_bank.questions.all()
            # questions.union(bank_1)
            # questions = (questions | bank_q).distinct()
            questions = (questions | bank_q)
            # questions = chain(questions, bank_q)

        # question_set = questions.order_by('?')

        return questions.select_subclasses()

    def get_questions(self, with_answers=False):
        question_ids = self._question_ids()

        # questions = sorted(
        #     self.quiz.question.filter(id__in=question_ids)
        #         .select_subclasses(),
        #     key=lambda q: question_ids.index(q.id))

        questions = sorted(
            self.get_question_set().filter(id__in=question_ids),
            key=lambda q: question_ids.index(q.id)
        )

        if with_answers:
            user_answers = json.loads(self.user_answers)
            print("user_answers => ", user_answers)
            for question in questions:
                question.user_answer = user_answers[str(question.id)]

        return questions

    @property
    def questions_with_user_answers(self):
        return {
            q: q.user_answer for q in self.get_questions(with_answers=True)
        }

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        """
        Returns the number of questions answered so far and the total number of
        questions.
        """
        answered = len(json.loads(self.user_answers))
        total = self.get_max_score
        return answered, total




class QuizContent(TimestampAbstractModel):
    # obj._meta.model_name
    MCQ = 'mcquestion'
    ESSAY = 'essayquestion'
    TF = 'tfquestion'

    QUESTION_TYPE_LIST = [MCQ, ESSAY, TF]

    quiz = models.ForeignKey(Quiz,
                             related_name='content',
                             on_delete=models.CASCADE,
                             verbose_name=_('Quiz Content'))
    content_type = models.ForeignKey(ContentType,
                                     limit_choices_to={'model__in': set(QUESTION_TYPE_LIST)},
                                     on_delete=models.CASCADE,
                                     verbose_name=_('Content Type'))
    object_id = models.PositiveIntegerField(verbose_name=_('Object id'))
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['quiz'])


class Question(TimestampAbstractModel):
    """
    Base class for all question types.
    Shared properties placed here.
    """
    MCQ = 'mcq'
    ESSAY = 'essay'
    TF = 'tf'

    QUESTION_TYPE = (
        (MCQ, 'Multiple choice'),
        (ESSAY, 'Essay'),
        (TF, 'True/False'),
    )

    QUESTION_TYPE_LIST = [MCQ, ESSAY, TF]

    quiz = models.ManyToManyField(Quiz,
                                  verbose_name=_("Quiz"),
                                  related_name='question',
                                  blank=True)

    theme = models.ForeignKey(to="themes.Theme",
                              verbose_name=_("Theme"),
                              blank=True,
                              null=True,
                              on_delete=models.CASCADE)

    figure = models.ImageField(upload_to='uploads/%Y/%m/%d',
                               blank=True,
                               null=True,
                               verbose_name=_("Figure"))

    content = models.TextField(blank=False,
                               help_text=_("Enter the question text that "
                                           "you want displayed"),
                               verbose_name=_('Question'))

    explanation = models.TextField(max_length=2000,
                                   blank=True,
                                   help_text=_("Explanation to be shown "
                                               "after the question has "
                                               "been answered."),
                                   verbose_name=_('Explanation'))

    objects = InheritanceManager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['theme']

    def __str__(self):
        return self.content

    def render(self):
        return render_to_string('quiz/content/{}.html'.format(
            self._meta.model_name), {'item': self})


class MCQuestion(Question):
    class Meta:
        verbose_name = _("Multiple Choice Question")
        verbose_name_plural = _("Multiple Choice Questions")

    CONTENT = 'content'
    RANDOM = 'random'
    NONE = 'none'

    ANSWER_ORDER_OPTIONS = (
        (CONTENT, _('Content')),
        (RANDOM, _('Random')),
        (NONE, _('None'))
    )

    answer_order = models.CharField(
        max_length=30, null=True, blank=True,
        choices=ANSWER_ORDER_OPTIONS,
        help_text=_("The order in which multichoice "
                    "answer options are displayed "
                    "to the user"),
        verbose_name=_("Answer Order"))

    def check_if_correct(self, guess):
        answer = Answer.objects.get(id=guess)

        if answer.correct is True:
            return True
        else:
            return False

    def order_answers(self, queryset):
        if self.answer_order == 'content':
            return queryset.order_by('content')
        if self.answer_order == 'random':
            return queryset.order_by('?')
        if self.answer_order == 'none':
            return queryset.order_by()
        return queryset

    def get_answers(self):
        return self.order_answers(Answer.objects.filter(question=self))

    def get_answers_list(self):
        return [(answer.id, answer.content) for answer in
                self.order_answers(Answer.objects.filter(question=self))]

    def answer_choice_to_string(self, guess):
        return Answer.objects.get(id=guess).content


class Answer(models.Model):
    question = models.ForeignKey(MCQuestion, verbose_name=_("Question"), on_delete=models.CASCADE)

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Enter the answer text that "
                                           "you want displayed"),
                               verbose_name=_("Content"))

    correct = models.BooleanField(blank=False,
                                  default=False,
                                  help_text=_("Is this a correct answer?"),
                                  verbose_name=_("Correct"))

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")


class EssayQuestion(Question):
    class Meta:
        verbose_name = _("Essay style question")
        verbose_name_plural = _("Essay style questions")

    def check_if_correct(self, guess):
        return False

    def get_answers(self):
        return False

    def get_answers_list(self):
        return False

    def answer_choice_to_string(self, guess):
        return str(guess)

    def __str__(self):
        return self.content


class TFQuestion(Question):
    class Meta:
        verbose_name = _("True/False Question")
        verbose_name_plural = _("True/False Questions")
        ordering = ['theme']

    correct = models.BooleanField(
        blank=False, default=False, verbose_name=_("Correct"),
        help_text=_("Tick this if the question is true. Leave it blank for false.")
    )

    def check_if_correct(self, guess):
        if guess == "True":
            guess_bool = True
        elif guess == "False":
            guess_bool = False
        else:
            return False

        if guess_bool == self.correct:
            return True
        else:
            return False

    def get_answers(self):
        return [{'correct': self.check_if_correct("True"),
                 'content': 'True'},
                {'correct': self.check_if_correct("False"),
                 'content': 'False'}]

    def get_answers_list(self):
        return [(True, True), (False, False)]

    def answer_choice_to_string(self, guess):
        return str(guess)
