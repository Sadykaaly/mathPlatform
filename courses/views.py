from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import Count
from django.forms import modelform_factory
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.template import loader
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views.generic.base import TemplateResponseMixin, View

from accounts.forms import CourseEnrollForm, CourseUnEnrollForm
from courses.forms import ModuleFormSet, QuizForm
from courses.mixins import OwnerCourseMixin, OwnerCourseEditMixin
from courses.models import Course, Subject, Module, Content


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'


class CourseCreateView(PermissionRequiredMixin,
                       OwnerCourseEditMixin,
                       CreateView):
    permission_required = 'courses.add_course'


class CourseDeleteView(PermissionRequiredMixin,
                       OwnerCourseMixin,
                       DeleteView):
    template_name = 'courses/manage/course/delete.html'
    success_url = reverse_lazy('manage_course_list')
    permission_required = 'courses.delete_course'


class CourseUpdateView(PermissionRequiredMixin,
                       OwnerCourseEditMixin,
                       UpdateView):
    permission_required = 'courses.change_course'


class CourseModuleUpdateView(LoginRequiredMixin, CreateView):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def dispatch(self, request, pk):
        self.course = get_object_or_404(
            Course,
            id=pk,
            owner=request.user
        )
        return super(CourseModuleUpdateView, self).dispatch(request, pk)

    def get(self, request, *args, **kwargs):
        formset = ModuleFormSet(instance=self.course)
        return self.render_to_response({'course': self.course,
                                        'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = ModuleFormSet(instance=self.course, data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({'course': self.course,
                                        'formset': formset})


class ContentCreateUpdateView(LoginRequiredMixin, TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    # template_name_quiz = 'courses/manage/content/form.html'

    # def get_template_names(self):
    #     model_name = self.kwargs.get('model_name')
    #     if model_name == Content.QUIZ:
    #         return self.template_name_quiz
    #     return [self.template_name]

    def get_model(self, model_name):
        if model_name in Content.CONTENT_TYPE_LIST:
            return apps.get_model(app_label='courses',
                                  model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        if model.__name__ == 'Quiz':
            Form = QuizForm
        else:
            Form = modelform_factory(model, exclude=['owner',
                                                     'order',
                                                     'created_at',
                                                     'updated_at'])
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(Module,
                                        id=module_id,
                                        course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model,
                                         id=id,
                                         owner=request.user)
        return super(ContentCreateUpdateView,
                     self).dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form,
                                        'object': self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.course = self.module.course
            obj.save()
            form.save_m2m()

            if not id:
                # new content
                Content.objects.create(module=self.module,
                                       item=obj)
            return redirect('module_content_list', self.module.id)

        return self.render_to_response({'form': form,
                                        'object': self.obj})


class ContentDeleteView(LoginRequiredMixin, View):

    def post(self, request, id):
        content = get_object_or_404(Content,
                                    id=id,
                                    module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)


class ModuleContentListView(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        module = get_object_or_404(Module,
                                   id=module_id,
                                   course__owner=request.user)

        return self.render_to_response({'module': module})


class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'courses/subject/list.html'


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/course/list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CourseListView, self).get_context_data()
        subject = Subject.objects.get(slug=self.kwargs.get('subject'))

        subject_course = Course.objects.filter(subject=subject)

        subject_children = subject.get_descendants()
        courses = Course.objects.filter(subject__in=subject_children)
        context['courses'] = subject_course.union(courses)

        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course/detail.html'

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView,
                        self).get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(
            initial={'course': self.object})
        context['un_enroll_form'] = CourseUnEnrollForm(initial={'course': self.object})
        return context


class ModuleOrderView(CsrfExemptMixin,
                      JsonRequestResponseMixin,
                      View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(
                id=id,
                course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentOrderView(CsrfExemptMixin,
                       JsonRequestResponseMixin,
                       View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id,
                                   module__course__owner=request.user) \
                .update(order=order)
        return self.render_json_response({'saved': 'OK'})


@login_required()
def enroll_to_course(request):
    messages = {
        'invalid-enrollment-key': 'Invalid enrollment key',
    }

    if request.method == 'POST':
        form = CourseEnrollForm(request.POST)
        form_html = loader.render_to_string(
            'courses/manage/form/enrollment.html',
            {'form': form}
        )
        if form.is_valid():
            course = form.cleaned_data['course']
            enrollment_key = form.cleaned_data['enrollment_key']

            success = False
            message = messages['invalid-enrollment-key']
            if course.enrollment_key and course.enrollment_key == enrollment_key:
                success = True
                course.students.add(request.user)
                message = None
            elif course.enrollment_key is None:
                success = True
                course.students.add(request.user)
                message = None

            data = {
                'message': message,
                'success': success,
                'form': form_html
            }
            return JsonResponse(data)

        data = {
            'message': None,
            'success': False,
            'form': form_html
        }

        return JsonResponse(data)
    return HttpResponse(status=405)


@login_required()
def un_enroll_from_course(request):
    if request.method == 'POST':
        un_enroll_form = CourseUnEnrollForm(request.POST)
        enroll_form = CourseEnrollForm()
        form_html = loader.render_to_string(
            'courses/manage/form/enrollment.html',
            {'form': enroll_form}
        )

        if un_enroll_form.is_valid():
            course = un_enroll_form.cleaned_data['course']
            course.students.remove(request.user)
            data = {
                'success': True,
                'form': form_html
            }
            return JsonResponse(data)

        data = {
            'success': False,
        }

        return JsonResponse(data)
    return HttpResponse(status=405)
