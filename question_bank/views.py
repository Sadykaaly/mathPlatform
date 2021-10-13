from django.apps import apps
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, DetailView, FormView
from django.views.generic.base import TemplateResponseMixin, View
from django.utils.translation import ugettext_lazy as _

from courses.mixins import InstructorRequiredMixin
from courses.models import Quiz
from generator.simple.generator import SimpleMath
from question_bank.forms import QuestionGeneratorForm
from question_bank.mixinx import OwnerQuestionBankMixin, QuestionBankMixin, \
    OwnerQuestionBankEditMixin
from question_bank.models import QuestionBank, QuestionBankContent
from quiz.forms import AnswerFormSet
from quiz.models import MCQuestion


class QuestionBankCreateView(PermissionRequiredMixin,
                             OwnerQuestionBankEditMixin,
                             CreateView):
    permission_required = 'questionbanks.add_questionbank'


class QuestionBankDeleteView(PermissionRequiredMixin,
                             OwnerQuestionBankMixin,
                             DeleteView):
    template_name = 'question-bank/manage/question-bank/delete.html'
    success_url = reverse_lazy('question_bank_mine')
    permission_required = 'questionbanks.delete_questionbank'


class QuestionBankUpdateView(PermissionRequiredMixin,
                             OwnerQuestionBankEditMixin,
                             UpdateView):
    permission_required = 'questionbanks.change_questionbank'


class ManageQuestionBankListView(OwnerQuestionBankMixin, ListView):
    template_name = 'question-bank/manage/question-bank/list.html'

    # template_name = 'courses/manage/course/list.html'

    def get_queryset(self):
        queryset = QuestionBank.objects.filter(owner=self.request.user)
        return queryset


class QuestionBankManagerView(InstructorRequiredMixin, QuestionBankMixin, DetailView):
    template_name = 'question-bank/manage/question-bank/detail.html'


class QuestionBankContentCreateUpdateView(LoginRequiredMixin,
                                          TemplateResponseMixin,
                                          View):
    model = None
    obj = None
    formset = None
    template_name = 'quiz/manage/content/form.html'
    template_mcq_name = 'quiz/manage/content/mcq_form.html'

    def get_formset(self):
        if self.model == MCQuestion:
            return AnswerFormSet
        return None

    def get_model(self, model_name):
        if model_name in QuestionBankContent.QUESTION_TYPE_LIST:
            return apps.get_model(app_label='quiz',
                                  model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['quiz',
                                                 'order',
                                                 'created_at',
                                                 'updated_at'])
        return Form(*args, **kwargs)

    def get_template_names(self):
        if self.model.__name__ == MCQuestion.__name__:
            return self.template_mcq_name
        else:
            return self.template_name

    def dispatch(self, request, pk, model_name, content_id=None):
        self.question_bank = get_object_or_404(QuestionBank,
                                               id=pk,
                                               owner=request.user)
        self.model = self.get_model(model_name)

        if content_id:
            self.obj = get_object_or_404(self.model,
                                         id=content_id)
        return super(QuestionBankContentCreateUpdateView,
                     self).dispatch(request, pk, model_name, content_id)

    def get(self, request, question_bank_id, model_name, content_id=None):
        form = self.get_form(self.model, instance=self.obj)

        formset = self.get_formset()
        if formset:
            formset = formset(instance=self.obj)

        return self.render_to_response({'form': form,
                                        'object': self.obj,
                                        'formset': formset})

    def post(self, request, pk, model_name, content_id=None):
        formset = self.get_formset()

        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()

            if not content_id:
                # new content
                QuestionBankContent.objects.create(question_bank=self.question_bank, item=obj)
                self.question_bank.questions.add(obj)

            if formset:
                formset = formset(instance=self.obj, data=request.POST)
                if formset.is_valid():
                    formset.instance = obj
                    formset.save()

            return redirect('question_bank_manager', self.question_bank.pk)

        return self.render_to_response({'form': form,
                                        'object': self.obj})


class QuestionBankContentDeleteView(LoginRequiredMixin, View):
    model = QuestionBankContent

    def post(self, request, pk, content_id):
        content = get_object_or_404(self.model, pk=content_id)
        question_bank = content.question_bank
        content.item.delete()
        content.delete()
        return redirect('question_bank_manager', question_bank.pk)


class QuestionBankListView(InstructorRequiredMixin, QuestionBankMixin, ListView):
    template_name = 'question-bank/list.html'
    context_object_name = 'question_banks'
    queryset = QuestionBank.objects.filter(is_active=True)


class QuestionBankDetailView(InstructorRequiredMixin, QuestionBankMixin, DetailView):
    template_name = 'question-bank/detail.html'


class QuestionBankGeneratorFormView(InstructorRequiredMixin, FormView):
    template_name = 'question-bank/manage/generator/form.html'
    form_class = QuestionGeneratorForm
    model = QuestionBank

    def get_context_data(self, **kwargs):
        context = super(QuestionBankGeneratorFormView, self).get_context_data()
        context['object'] = get_object_or_404(self.model, id=self.kwargs['pk'])
        return context


def generate_question(request, pk):
    if request.method == 'POST':
        form = QuestionGeneratorForm(request.POST, question_bank=pk)
        if form.is_valid():
            form.save()
            data = dict(
                success=True,
                message=_('Questions successfully generated')
            )
            return JsonResponse(data, content_type='application/json', status=200)

        data = dict(
            error=True,
            form=form
        )
        return JsonResponse(data, content_type='application/json', status=200)
    return HttpResponse(status=405)
