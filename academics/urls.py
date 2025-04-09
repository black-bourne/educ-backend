from django.urls import path
from .views import calendar_events_view, assignment_view, announcements_view, classes_view

urlpatterns = [
    path('calendar-events', calendar_events_view, name='calendar_events'),
    path('announcements', announcements_view, name='announcements'),
    path('assignments', assignment_view, name='assignment_view'),
    path('assignments/submit', assignment_view, name='assignment_submit'),
    path('assignments/submissions',assignment_view, name='assignment_submissions'),
    path('assignments/grade', assignment_view, name='assignment_grade'),
    path('classes', classes_view, name='classes_view'),
]
