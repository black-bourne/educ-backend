import json

from django.core.cache import cache
from django.http import JsonResponse, HttpResponseBadRequest
from django.http.response import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime

from .models import Event, Assignment, SchoolClass, TeacherSubject, Submission, Announcement
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def calendar_events_view(request):
    cache_key = 'calendar_events'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)

    events = Event.objects.select_related('school_class').all()
    events_data = [
        {
            'title': event.title,
            'description': event.description,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
            'school_class': event.school_class.name if event.school_class else None,
            'allDay': event.allDay
        }
        for event in events
    ]
    cache.set(cache_key, events_data, timeout=600)  # Cache for 10 minutes
    return JsonResponse(events_data, safe=False)

def announcements_view(request):
    cache_key = 'announcements'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)

    announcements = Announcement.objects.select_related('school_class').all()
    announcements_data = [
        {
            'title': announcement.title,
            'description': announcement.description,
            'date': announcement.date.isoformat(),
            'target_role': announcement.target_role,
            'school_class': announcement.school_class.id if announcement.school_class else None,
        }
        for announcement in announcements
    ]
    cache.set(cache_key, announcements_data, timeout=600)
    return JsonResponse(announcements_data, safe=False)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def assignment_view(request):
    logger.info(f"User role: {request.user.role}")
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    if request.method == "GET":
        if 'submission' in request.path:
            if request.user.role != "teacher":
                return HttpResponseForbidden("Only teachers can view submissions")
            assignment_id = request.GET.get('assignment_id')
            if not assignment_id:
                return HttpResponseBadRequest("Missing assignment_id")
            try:
                assignment = Assignment.objects.get(id=assignment_id, created_by=request.user)
                submissions = assignment.submissions.all()
                data = [
                    {
                        'id': sub.id,
                        'student': sub.student.first_name + " " + sub.student.last_name,
                        'file': sub.file.url,
                        'submitted_at': sub.submitted_at.isoformat(),
                        'status': sub.status,
                        'score': sub.score,
                    }
                    for sub in submissions
                ]
                return JsonResponse({'submissions': data})
            except Assignment.DoesNotExist:
                return HttpResponseBadRequest("Invalid assignment ID or not your assignment")

        cache_key = f'assignments_{request.user.id}_{request.user.role}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return JsonResponse(cached_data)

        if request.user.role == "teacher":
            assignments = Assignment.objects.filter(created_by=request.user).select_related('classroom').order_by('-created_at')
        elif request.user.role == "student":
            student_class = SchoolClass.objects.filter(students=request.user).first()
            if not student_class:
                return JsonResponse({"error": "No class assigned to this student"}, status=404)
            assignments = Assignment.objects.filter(classroom=student_class).select_related('classroom').order_by('-created_at')
            data = []
            for assignment in assignments:
                submission = assignment.submissions.filter(student=request.user).first()
                data.append({
                    'id': assignment.id,
                    'subject': assignment.subject,
                    'title': assignment.title,
                    'description': assignment.description,
                    'due': assignment.due.isoformat(),
                    'status': assignment.status,
                    'classroom': assignment.classroom.id if assignment.classroom else None,
                    'created_at': assignment.created_at.isoformat(),
                    'submission_status': submission.status if submission else None,
                    'submission_score': submission.score if submission else None,
                })
            cache.set(cache_key, {'assignments': data}, timeout=300)
            return JsonResponse({'assignments': data})
        else:
            return HttpResponseForbidden("Invalid role")

        data = [
            {
                'id': assignment.id,
                'subject': assignment.subject,
                'title': assignment.title,
                'description': assignment.description,
                'due': assignment.due.isoformat(),
                'status': assignment.status,
                'classroom': assignment.classroom.id if assignment.classroom else None,
                'created_at': assignment.created_at.isoformat(),
            }
            for assignment in assignments
        ]
        cache.set(cache_key, {'assignments': data}, timeout=300)
        return JsonResponse({'assignments': data})

    elif request.method == "POST":
        # Handle teacher creating assignment (for /api/assignments)
        if not request.path.endswith('/submit'):
            if request.user.role != "teacher":
                return HttpResponseForbidden("Only teachers can create assignments")
            try:
                body = json.loads(request.body.decode('utf-8'))
                title = body.get('title')
                description = body.get('description', '')
                subject = body.get('subject')
                classroom_id = body.get('classroom')
                due = parse_datetime(body.get('due'))

                if not all([title, due, classroom_id, subject]):
                    return HttpResponseBadRequest("Missing required fields: title, due, classroom, or subject")

                classroom = SchoolClass.objects.get(id=classroom_id)
                if request.user not in classroom.teachers.all():
                    return HttpResponseForbidden("You are not assigned to this class")
                if not TeacherSubject.objects.filter(teacher=request.user, subject=subject).exists():
                    return HttpResponseForbidden("You are not assigned to teach this subject")

                assignment = Assignment.objects.create(
                    title=title,
                    description=description,
                    subject=subject,
                    classroom=classroom,
                    due=due,
                    created_by=request.user,
                )
                data = {
                    'id': assignment.id,
                    'subject': assignment.subject,
                    'title': assignment.title,
                    'description': assignment.description,
                    'due': assignment.due.isoformat(),
                    'status': assignment.status,
                    'classroom': assignment.classroom.id,
                    'created_at': assignment.created_at.isoformat(),
                }
                return JsonResponse(data, status=201)
            except json.JSONDecodeError:
                return HttpResponseBadRequest("Invalid JSON format")
            except SchoolClass.DoesNotExist:
                return HttpResponseBadRequest("Invalid classroom ID")
            except Exception as e:
                return HttpResponseBadRequest(str(e))

        # Handle student submitting assignment (for /api/assignments/submit)
        if request.path.endswith('/submit'):
            if request.user.role != "student":
                return HttpResponseForbidden("Only students can submit assignments")
            try:
                assignment_id = request.POST.get('assignment_id')
                file = request.FILES.get('file')
                if not all([assignment_id, file]):
                    return HttpResponseBadRequest("Missing assignment_id or file")
                if not file.name.endswith('.pdf'):
                    return HttpResponseBadRequest("Only PDF files are allowed")
                if file.size > 5 * 1024 * 1024:
                    return HttpResponseBadRequest("File size must not exceed 5MB")
                assignment = Assignment.objects.get(id=assignment_id)
                if request.user not in assignment.classroom.students.all():
                    return HttpResponseForbidden("You are not enrolled in this class")

                submission, created = Submission.objects.update_or_create(
                    assignment=assignment,
                    student=request.user,
                    defaults={'file': file}
                )

                return JsonResponse({
                    'id': submission.id,
                    'assignment_id': assignment.id,
                    'file': submission.file.url,
                    'submitted_at': submission.submitted_at.isoformat(),
                }, status=201 if created else 200)

            except Assignment.DoesNotExist:
                return HttpResponseBadRequest("Invalid assignment ID")
            except Exception as e:
                return HttpResponseBadRequest(str(e))

@csrf_exempt
@require_http_methods(["GET"])
def classes_view(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Authentication required")
    if request.user.role != "teacher":
        return HttpResponseForbidden("Only teachers can view classes")

    classes = SchoolClass.objects.filter(teachers=request.user)
    data = [
        {
            'id': cls.id,
            'name': cls.name,
        }
        for cls in classes
    ]
    return JsonResponse({'classes': data})
