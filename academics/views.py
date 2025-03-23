import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.http.response import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
# from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from .models import Event, Assignment, SchoolClass, TeacherSubject


def calendar_events_view(request):
    events = Event.objects.all()
    events_data = [
        {
            'title': event.title,
            'description': event.description,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
            'school_class': event.school_class,
            'allDay': event.allDay
        }
        for event in events
    ]
    # safe=False allows returning a list
    return JsonResponse(events_data, safe=False)



@ensure_csrf_cookie
# @login_required
@require_http_methods(["GET", "POST"])
def assignment_view(request):
    if request.method == "GET":
        assignments = Assignment.objects.filter(created_by=request.user).order_by('-created_at')
        data = [{
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'due': a.due_date.isoformat(),
            'status': a.status,
        } for a in assignments]
        return JsonResponse({'assignments': data})

    elif request.method == "POST":
        try:
            body = json.loads(request.body)
            title = body.get('title')
            description = body.get('description', '')
            subject = body.get('subject')
            classroom_id = body.get('classroom_id')
            due = parse_datetime(body.get('due')) # Handles date in ISO format to work with it here

            # Basic validations
            if not title or not due or classroom_id:
                return HttpResponseBadRequest("Missing required fields: title or due date or  classroom.")
            # Get the class
            try:
                classroom = SchoolClass.objects.get(id=classroom_id)
            except SchoolClass.DoesNotExist:
                return HttpResponseBadRequest("Invalid classroom ID")

            # Check if assigned teacher is in that class
            if request.user not in classroom.teachers.all():
                return HttpResponseForbidden("You are not assigned to this class")

            # Find if the subject is being by that teacher
            if not TeacherSubject.objects.filter(teacher=request.user, subject=subject).exists():
                return HttpResponseForbidden("You are not assigned to teach this class")

            # assignment instance
            assignment = Assignment.objects.create(
                title=title,
                description=description,
                subject = subject,
                classroom = classroom,
                due=due,
                created_by=request.user
            )
            data = {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'subject': assignment.subject,
                'classroom': assignment.classroom.name,
                'due': assignment.due.isoformat(), #YY-MM-DD (ISO) format
                'status': assignment.status,
            }
            return JsonResponse(data, status=201)
        except Exception as e:
            return HttpResponseBadRequest(str(e))

