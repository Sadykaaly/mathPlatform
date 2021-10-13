from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView

from courses.models import Course, Quiz


class StudentMainPageView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/course/main.html'

    def get_context_data(self, **kwargs):
        context = super(StudentMainPageView, self).get_context_data()

        user_courses = Course.objects.filter(students__in=[self.request.user])
        context['courses'] = user_courses
        context['quiz_list'] = Quiz.objects.filter(course__in=user_courses, draft=False)
        return context


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'accounts/course/list.html'

    def get_queryset(self):
        qs = super(StudentCourseListView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'accounts/course/detail.html'

    def get_queryset(self):
        qs = super(StudentCourseDetailView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        context = super(StudentCourseDetailView,
                        self).get_context_data(**kwargs)
        # get course object
        course = self.get_object()
        if 'module_id' in self.kwargs:
            # get current module
            context['module'] = course.module.get(
                                    id=self.kwargs['module_id'])
        else:
            # get first module
            context['module'] = course.module.all()[0]
        return context
