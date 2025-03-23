from django.urls import path
from .views import calendar_events_view, assignment_view

urlpatterns = [
    path('calendar-events', calendar_events_view, name='calendar_events'),
    path('assignments', assignment_view, name='assignments')
]
