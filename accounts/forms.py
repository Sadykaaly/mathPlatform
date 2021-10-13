from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from courses.models import Course

from .models import User


class CourseEnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(),
                                    widget=forms.HiddenInput)
    enrollment_key = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        course = self.cleaned_data['course']
        enrollment_key = self.data['enrollment_key']

        if course.enrollment_key and course.enrollment_key != enrollment_key:
            raise ValidationError(_('Enrollment key is incorrect!'))

        return self.cleaned_data


class CourseUnEnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(),
                                    widget=forms.HiddenInput)


class UserForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False,
        label=_('Новый пароль'),
        strip=False,
        widget=forms.PasswordInput,
        # help_text=password_validation.password_validators_help_text_html(),  # password cleaner help text
    )

    class Meta:
        model = User
        fields = '__all__'

    def save(self, commit=True):
        new_password = self.cleaned_data.get('new_password', None)
        if new_password:
            self.instance.set_password(new_password)
        return super(UserForm, self).save(commit)


class RegisterForm(SignupForm):
    first_name = forms.CharField()
    last_name = forms.CharField()

    def custom_signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
