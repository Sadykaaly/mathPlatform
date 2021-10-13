from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext_lazy as _
from quiz.models import Quiz, Question, Answer, MCQuestion, TFQuestion, EssayQuestion, Sitting, Progress
from themes.models import Theme

admin.site.header = 'Панель управления'


class QuizAdminForm(forms.ModelForm):
    """
    below is from
    http://stackoverflow.com/questions/11657682/
    django-admin-interface-using-horizontal-filter-with-
    inline-manytomany-field
    """

    class Meta:
        model = Quiz
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(
            verbose_name=_("Questions"),
            is_stacked=False))

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['questions'].initial = \
                self.instance.question.all().select_subclasses()

    def save(self, commit=True):
        quiz = super(QuizAdminForm, self).save(commit=False)
        quiz.save()
        quiz.question.set(self.cleaned_data['questions'])
        self.save_m2m()
        return quiz


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm

    list_display = ('title', 'theme', )
    list_filter = ('theme',)
    search_fields = ('description', 'theme', )


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


@admin.register(MCQuestion)
class MCQuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'theme', )
    list_filter = ('theme',)
    fields = ('content', 'theme',
              'figure', 'quiz', 'explanation', 'answer_order')

    search_fields = ('content', 'explanation')
    filter_horizontal = ('quiz',)

    inlines = [AnswerInline]


@admin.register(TFQuestion)
class TFQuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'theme', )
    list_filter = ('theme',)
    fields = ('content', 'theme',
              'figure', 'quiz', 'explanation', 'correct',)

    search_fields = ('content', 'explanation')
    filter_horizontal = ('quiz',)


@admin.register(EssayQuestion)
class EssayQuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'theme', )
    list_filter = ('theme',)
    fields = ('content', 'theme', 'quiz', 'explanation', )
    search_fields = ('content', 'explanation')
    filter_horizontal = ('quiz',)


@admin.register(Sitting)
class SittingAdmin(admin.ModelAdmin):
    pass


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    pass

