from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from academics.models import Grade, SchoolClass, Announcement, Event, Assignment, TeacherSubject

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'role', 'first_name','last_name', 'date_of_birth', 'enrollment_number', 'school_class')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Mark the password as unusable so the user must reset it via the email link
        user.set_unusable_password()
        user.is_active = False  # Mark as inactive until password is set
        if commit:
            user.save()
        return user

# Custom form for changing user details (excluding direct password modification)
class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'role', 'date_of_birth', 'first_name', 'last_name', 'enrollment_number', 'school_class', 'is_active')


class CustomUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    model = User

    fieldsets = (
        (None, {'fields': ('email', 'role')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth')}),
        ('Academic info', {'fields': ('school_class', 'enrollment_number')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        ('Information', {
            'classes': ('wide',),
            'fields': ('email', 'role', 'first_name', 'last_name', 'date_of_birth', 'school_class', 'enrollment_number'),
        }),
    )
    ordering = ['email', 'enrollment_number']
    list_display = ('email', 'role', 'full_name', 'date_of_birth', 'school_class', 'enrollment_number', 'is_active')
    list_filter = ('role', 'school_class', 'is_active')
    readonly_fields = ('last_login', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'enrollment_number')
    list_per_page = 25
    actions = ['make_active', 'make_inactive']
    list_select_related = ('school_class',)

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    full_name.short_description = "Full Name"

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser  # Restrict to superusers

    def make_active(self, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Activate selected users"

    def make_inactive(self, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Deactivate selected users"

    # def changelist_view(self, request, extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['title'] = "User Administration"
    #     return super().changelist_view(request, extra_context=extra_context)



admin.site.register(User, CustomUserAdmin)
admin.site.register(Grade)
admin.site.register(SchoolClass)
admin.site.register(Announcement)
admin.site.register(Event)
admin.site.register(Assignment)
admin.site.register(TeacherSubject)

