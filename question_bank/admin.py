from django.contrib import admin

# Register your models here.
from question_bank.models import QuestionBank


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    pass