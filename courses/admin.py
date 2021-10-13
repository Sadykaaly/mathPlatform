from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin

from .models import Subject, Course, Module, Content, File, Image, Video, Text


@admin.register(Subject)
class SubjectAdmin(DraggableMPTTAdmin):
    ist_display = ('tree_actions', 'indented_title',)
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('title',)}


class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    pass


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    pass


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    pass


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    pass


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    pass



