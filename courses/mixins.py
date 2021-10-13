from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from courses.models import Course


class OwnerMixin(object):
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin(object):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(OwnerEditMixin, self).form_valid(form)


class InstructorRequiredMixin(object):
    """Verify that the current user is authenticated and is instructor"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and request.user.is_instructor:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class OwnerCourseMixin(OwnerMixin, InstructorRequiredMixin):
    model = Course
    fields = ['subject', 'title', 'slug', 'description']
    success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    fields = ['subject', 'title', 'slug', 'description', 'image', 'enrollment_key']
    success_url = reverse_lazy('manage_course_list')
    template_name = 'courses/manage/course/form.html'

