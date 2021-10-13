from django.urls import reverse_lazy

from courses.mixins import OwnerMixin, InstructorRequiredMixin, OwnerEditMixin
from question_bank.models import QuestionBank


class QuestionBankMixin:
    model = QuestionBank


class OwnerQuestionBankMixin(OwnerMixin, InstructorRequiredMixin, QuestionBankMixin):
    fields = ['theme', 'title', 'description', 'is_active']
    success_url = reverse_lazy('question_bank_mine')


class OwnerQuestionBankEditMixin(OwnerQuestionBankMixin, OwnerEditMixin):
    fields = ['theme', 'title', 'description', 'is_active']
    success_url = reverse_lazy('question_bank_mine')
    # template_name = 'courses/manage/course/form.html'
    template_name = 'question-bank/manage/question-bank/form.html'

