from django.db import models
from common.models import TimestampAbstractModel
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.translation import ugettext_lazy as _


class Theme(MPTTModel, TimestampAbstractModel):

    class MPTTMeta:
        verbose_name_plural = _('Themes')
        verbose_name = _('Theme')
        order_insertion_by = ['title']

    title = models.CharField(max_length=255, verbose_name=_('Title'))
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                            verbose_name=_('Parent'))

    def __str__(self):
        return self.title

