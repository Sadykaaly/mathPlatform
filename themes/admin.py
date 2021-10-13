from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Theme


@admin.register(Theme)
class ThemeAdmin(DraggableMPTTAdmin):
    ist_display = ('tree_actions', 'indented_title',)
    list_display_links = ('indented_title',)
