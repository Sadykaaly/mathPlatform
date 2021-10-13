from django.forms.models import inlineformset_factory

from question_bank.models import QuestionBank
from .models import Course, Module, Quiz
from django import forms


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        exclude = ['owner',
                   'order',
                   'created_at',
                   'updated_at']

    question_banks = forms.ModelMultipleChoiceField(queryset=QuestionBank.objects.filter(is_active=True),
                                                    required=False)

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            initial = kwargs.setdefault('initial', {})
            initial['question_banks'] = [t.pk for t in kwargs['instance'].question_banks.filter(is_active=True)]

        forms.ModelForm.__init__(self, *args,    **kwargs)
        self.fields['start_at'].widget = forms.DateTimeInput(attrs={
            'placeholder': 'yyyy-mm-dd hh:mm:ss'
        })
        self.fields['end_at'].widget = forms.DateTimeInput(attrs={
            'placeholder': 'yyyy-mm-dd hh:mm:ss'
        })

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, False)

        old_save_m2m = self.save_m2m

        def save_m2m():
            old_save_m2m()
            instance.question_banks.clear()
            instance.question_banks.add(*self.cleaned_data['question_banks'])

        self.save_m2m = save_m2m

        if commit:
            instance.save()
            self.save_m2m()

        return instance


ModuleFormSet = inlineformset_factory(Course,
                                      Module,
                                      fields=['title', 'description'],
                                      extra=1,
                                      can_delete=True)
