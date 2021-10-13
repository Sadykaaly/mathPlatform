from django.db.models.signals import pre_save
from django.dispatch import receiver

from courses.models import Quiz
from quiz.models import Sitting


@receiver(pre_save, sender=Quiz)
def pre_save_quiz_max_attempts_is_none(sender, instance, **kwargs):
    if not instance.single_attempt and (instance.max_attempts is None or instance.max_attempts == 0):
        instance.max_attempts = 2
        instance.save()