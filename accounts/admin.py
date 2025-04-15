from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.core.cache import cache

from academics.models import Grade, SchoolClass, Announcement, Event, Assignment, TeacherSubject

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'role', 'first_name', 'last_name', 'date_of_birth', 'enrollment_number', 'school_class')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()
        user.is_active = False
        if commit:
            user.save()
        return user

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
    ordering = ['email']
    list_display = ('email', 'role', 'first_name', 'last_name', 'school_class_name', 'is_active')
    list_filter = ('role', 'is_active')  # Removed 'school_class' to reduce queries
    readonly_fields = ('last_login', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')  # Removed 'enrollment_number' for speed
    list_per_page = 25
    actions = ['make_active', 'make_inactive']
    list_select_related = ('school_class',)  # Pre-fetch school_class

    def school_class_name(self, obj):
        return obj.school_class.name if obj.school_class else 'None'
    school_class_name.short_description = 'School Class'

    def get_queryset(self, request):
        cache_key = 'user_admin_queryset'
        cached_qs = cache.get(cache_key)
        if cached_qs is not None:
            return cached_qs
        qs = super().get_queryset(request).select_related('school_class')
        cache.set(cache_key, qs, timeout=300)  # Cache for 5 minutes
        return qs

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        cache.delete('user_admin_queryset')  # Invalidate cache on update
    make_active.short_description = "Activate selected users"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        cache.delete('user_admin_queryset')  # Invalidate cache on update
    make_inactive.short_description = "Deactivate selected users"

# Inline for TeacherSubject to reduce separate page loads
class TeacherSubjectInline(admin.TabularInline):
    model = TeacherSubject
    extra = 1
    fields = ('subject',)

class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'supervisor_name', 'student_count', 'teacher_count')
    list_filter = ('grade',)
    search_fields = ('name',)
    list_select_related = ('grade', 'supervisor')
    filter_horizontal = ('teachers', 'students')

    def supervisor_name(self, obj):
        return obj.supervisor.email if obj.supervisor else 'None'
    def student_count(self, obj):
        return obj.students.count()
    def teacher_count(self, obj):
        return obj.teachers.count()

    def get_queryset(self, request):
        cache_key = 'schoolclass_admin_queryset'
        cached_qs = cache.get(cache_key)
        if cached_qs is not None:
            return cached_qs
        qs = super().get_queryset(request).select_related('grade', 'supervisor').prefetch_related('teachers', 'students')
        cache.set(cache_key, qs, timeout=300)
        return qs

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'due', 'status', 'classroom_name', 'created_by_email')
    list_filter = ('subject', 'status', 'due')
    search_fields = ('title',)
    list_select_related = ('classroom', 'created_by')
    date_hierarchy = 'due'

    def classroom_name(self, obj):
        return obj.classroom.name if obj.classroom else 'None'
    def created_by_email(self, obj):
        return obj.created_by.email

    def get_queryset(self, request):
        cache_key = 'assignment_admin_queryset'
        cached_qs = cache.get(cache_key)
        if cached_qs is not None:
            return cached_qs
        qs = super().get_queryset(request).select_related('classroom', 'created_by')
        cache.set(cache_key, qs, timeout=300)
        return qs

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'target_role', 'school_class_name')
    list_filter = ('target_role', 'date')
    search_fields = ('title',)
    list_select_related = ('school_class',)

    def school_class_name(self, obj):
        return obj.school_class.name if obj.school_class else 'None'
    school_class_name.short_description = 'School Class'

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end', 'allDay', 'school_class_name')
    list_filter = ('start', 'allDay')
    search_fields = ('title',)
    list_select_related = ('school_class',)
    date_hierarchy = 'start'

    def school_class_name(self, obj):
        return obj.school_class.name if obj.school_class else 'None'
    school_class_name.short_description = 'School Class'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Grade)
admin.site.register(SchoolClass, SchoolClassAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(TeacherSubject)