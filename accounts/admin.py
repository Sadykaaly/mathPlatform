from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .forms import UserForm
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserForm

    # prepopulated_fields = {'slug': ('email',)}
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    list_display = (
        '__str__',
        'last_name',
        'first_name',
        'user_type',
        'is_active',
        'is_superuser',
    )

    list_filter = (
        'last_name',
        'first_name',
        'user_type',
        'is_superuser',
        'is_active',
    )

    search_fields = (
        'first_name',
        'last_name',
        'user_type',
    )

    fieldsets = (
        (None, {
            'fields': (
                'email',
                'user_type',
                'password',
                'new_password',
            ),
        }),
        (
            _('Personal info'),
            {
                'fields': (
                    'last_name',
                    'first_name',
                    'date_of_birth',
                    'gender',
                    'avatar',
                ),
            },
        ),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_superuser',
                    'is_active',
                    'is_staff',
                    'is_deleted',
                    'groups',
                ),
            },
        ),
        (_('Important dates'),
            {
             'fields': (
                  'last_login',
                  # 'date_joined',
                  'created_at',
                  'updated_at'
               )
            }
         ),
    )

    actions = ('hard_delete',)

    def get_queryset(self, request):
        return User.objects_with_deleted.all()

    def hard_delete(self, _, queryset):
        queryset.hard_delete()

    def save_model(self, request, obj, form, change):
        created = False if obj.id else True
        super().save_model(request, obj, form, change)

