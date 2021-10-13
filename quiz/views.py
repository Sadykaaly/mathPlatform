import datetime

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.forms import modelform_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.base import TemplateResponseMixin, View, TemplateView

from courses.models import Quiz, Content
from quiz.forms import AnswerFormSet, QuestionForm, EssayForm
from quiz.helpers import get_key
from quiz.mixins import QuizMarkerMixin, SittingFilterTitleMixin
from quiz.models import Question, QuizContent, MCQuestion, Sitting, EssayQuestion, Progress


class QuizManageListView(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'quiz/manage/question_list.html'

    def get(self, request, slug):
        quiz = get_object_or_404(Quiz,
                                 slug=slug,
                                 owner=request.user)

        return self.render_to_response({'quiz': quiz})


class QuizCreateUpdateView(LoginRequiredMixin, TemplateResponseMixin, View):
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
        if model_name in QuizContent.QUESTION_TYPE_LIST:
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

    def dispatch(self, request, slug, model_name, id=None):
        self.quiz = get_object_or_404(Quiz,
                                      slug=slug,
                                      owner=request.user)
        self.model = self.get_model(model_name)

        if id:
            self.obj = get_object_or_404(self.model,
                                         id=id)
        return super(QuizCreateUpdateView,
                     self).dispatch(request, slug, model_name, id)

    def get(self, request, slug, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        print('slug = > ', slug)
        print('model_name = > ', model_name)
        formset = self.get_formset()
        if formset:
            formset = formset(instance=self.obj)

        return self.render_to_response({'form': form,
                                        'object': self.obj,
                                        'formset': formset})

    def post(self, request, slug, model_name, id=None):
        formset = self.get_formset()
        print('slug => ', slug)
        print('model_name => ', model_name)

        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()

            if not id:
                # new content
                QuizContent.objects.create(quiz=self.quiz, item=obj)
                self.quiz.question.add(obj)

            if formset:
                formset = formset(instance=self.obj, data=request.POST)
                if formset.is_valid():
                    formset.instance = obj
                    formset.save()

            return redirect('question_list_manager', self.quiz.slug)

        return self.render_to_response({'form': form,
                                        'object': self.obj})


class QuizContentDeleteView(LoginRequiredMixin, View):
    model = QuizContent

    def post(self, request, pk):
        content = get_object_or_404(self.model, pk=pk)
        quiz = content.quiz
        content.item.delete()
        content.delete()
        return redirect('question_list_manager', quiz.slug)


class QuizUserProgressView(LoginRequiredMixin, TemplateView):
    template_name = 'quiz/manage/progress.html'

    def get_context_data(self, **kwargs):
        context = super(QuizUserProgressView, self).get_context_data(**kwargs)
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        context['cat_scores'] = progress.list_all_cat_scores
        context['exams'] = progress.show_exams()
        return context


class QuizMarkingList(QuizMarkerMixin, SittingFilterTitleMixin, ListView):
    template_name = 'quiz/manage/sitting_list.html'
    model = Sitting

    def get_queryset(self):
        queryset = super(QuizMarkingList, self).get_queryset() \
            .filter(complete=True)

        user_filter = self.request.GET.get('user_filter')
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)

        return queryset


class QuizMarkingDetail(QuizMarkerMixin, DetailView):
    template_name = 'quiz/manage/sitting_detail.html'
    model = Sitting

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()

        q_to_toggle = request.POST.get('qid', None)
        if q_to_toggle:
            q = Question.objects.get_subclass(id=int(q_to_toggle))
            if int(q_to_toggle) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(q)
            else:
                sitting.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context['questions'] = \
            context['sitting'].get_questions(with_answers=True)
        return context


class StudentQuizStartView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'quiz/quiz-start.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.draft:
            if request.user.is_instructor():
                context = self.get_context_data(object=self.object)
                return self.render_to_response(context)
            else:
                raise PermissionDenied
        else:
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sitting = Sitting.objects.filter(user=self.request.user, quiz=self.object, complete=True).exists()
        context['is_sitting_exists'] = sitting
        return context


class QuizTake(LoginRequiredMixin, FormView):
    form_class = QuestionForm
    template_name = 'quiz/question.html'
    result_template_name = 'quiz/result.html'
    single_complete_template_name = 'quiz/complete.html'
    time_up_template_name = 'quiz/time_up.html'
    time_not_yet_template_name = 'quiz/time_not_yet.html'
    not_available_template_name = 'quiz/not_available.html'

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, slug=self.kwargs['slug'])
        self.course = self.get_course(self.quiz)

        if request.user not in self.course.students.all():
            return render(request, self.time_not_yet_template_name)

        if self.quiz.draft and not request.user.has_perm('quiz.change_quiz'):
            raise PermissionDenied

        self.sitting = Sitting.objects.user_sitting(request.user, self.quiz)
        self.sitting_end_in = (self.sitting.created_at + datetime.timedelta(minutes=self.quiz.time_limit)) if self.quiz.time_limit else None

        if self.sitting is False:
            return render(request, self.single_complete_template_name)

        if self.quiz.start_at and self.quiz.start_at > timezone.now():
            return render(request, self.time_not_yet_template_name)

        if (self.quiz.end_at and self.quiz.end_at < timezone.now()) \
                or (self.sitting.start > timezone.now()) \
                or (self.sitting_end_in and timezone.now() > self.sitting_end_in):
            self.sitting.mark_quiz_complete()
            return render(request, self.time_up_template_name)
        return super(QuizTake, self).dispatch(request, *args, **kwargs)

    def get_question(self):
        if self.kwargs.get('question_index', None) == 0:
            return self.sitting.get_first_question()
        else:
            return self.sitting.get_question_by_index(self.kwargs.get('question_index'))

    def get_form(self, *args, **kwargs):
        self.progress = self.sitting.progress()
        self.question = self.get_question()

        if self.question.__class__ is EssayQuestion:
            form_class = EssayForm
        else:
            form_class = self.form_class

        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super(QuizTake, self).get_form_kwargs()
        return dict(kwargs, question=self.question)

    def form_valid(self, form):
        self.form_valid_user(form)
        if self.sitting.get_first_question() is False:
            return self.final_result_user()

        self.request.POST = {}
        return redirect(reverse('quiz_start', kwargs={'slug': self.quiz.slug,
                                                      'question_index': self.kwargs.get('question_index') + 1}))

    def get_context_data(self, **kwargs):
        context = super(QuizTake, self).get_context_data(**kwargs)
        context['questions'] = self.sitting.get_enumerated_questions
        context['question'] = self.question
        context['current_question_index'] = self.kwargs.get('question_index')
        context['question_key'] = get_key(self.sitting.enumerated_questions, str(self.question.id))
        context['quiz'] = self.quiz
        context['sitting_end_in'] = self.sitting_end_in
        if hasattr(self, 'previous'):
            context['previous'] = self.previous
        if hasattr(self, 'progress'):
            context['progress'] = self.progress
        return context

    def form_valid_user(self, form):
        guess = form.cleaned_data['answers']
        is_correct = self.question.check_if_correct(guess)
        if str(self.question.id) in self.sitting.question_list.split(','):
            if is_correct:
                self.sitting.add_to_score(1)
            else:
                self.sitting.add_incorrect_question(self.question)

            self.sitting.add_user_answer(self.question, guess)
            self.sitting.remove_first_question()

        else:
            if is_correct and self.sitting.is_question_incorrect(self.question.id):
                self.sitting.remove_incorrect_question(self.question)

            elif not self.sitting.is_question_incorrect(self.question.id):
                self.sitting.add_incorrect_question(self.question)

        self.sitting.change_question_index(self.kwargs.get('question_index'))

    def final_result_user(self):
        results = {
            'quiz': self.quiz,
            'score': self.sitting.get_current_score,
            'max_score': self.sitting.get_max_score,
            'percent': self.sitting.get_percent_correct,
            'sitting': self.sitting,
        }

        self.sitting.mark_quiz_complete()

        if self.quiz.answers_at_end:
            results['questions'] = \
                self.sitting.get_questions(with_answers=True)
            results['incorrect_questions'] = \
                self.sitting.get_incorrect_questions

        return render(self.request, self.result_template_name, results)

    def get_course(self, related_object):
        related_object_type = ContentType.objects.get_for_model(related_object)
        content = Content.objects.filter(
            content_type__pk=related_object_type.id,
            object_id=related_object.id,
        ).first()
        return content.module.course


class QuizResults(DetailView):
    model = Quiz
    template_name = 'quiz/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sitting = Sitting.objects.filter(user=self.request.user, quiz=self.object, complete=True)[0]

        context['quiz'] = self.object
        context['score'] = sitting.get_current_score
        context['max_score'] = sitting.get_max_score
        context['percent'] = sitting.get_percent_correct
        context['sitting'] = sitting

        if self.object.answers_at_end:
            context['questions'] = \
                sitting.get_questions(with_answers=True)
            context['incorrect_questions'] = \
                sitting.get_incorrect_questions

        return context
