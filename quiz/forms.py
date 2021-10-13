from django.forms import RadioSelect, Textarea
from django.forms.models import inlineformset_factory
from django import forms
from quiz.models import MCQuestion, Answer

AnswerFormSet = inlineformset_factory(MCQuestion,
                                      Answer,
                                      fields=['content', 'correct'],
                                      extra=1,
                                      can_delete=True)


class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_answers_list()]
        self.fields["answers"] = forms.ChoiceField(choices=choice_list,
                                                   widget=RadioSelect)


class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={'style': 'width:100%'}))

