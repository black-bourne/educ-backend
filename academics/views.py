import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.http.response import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.dateparse import parse_datetime
from .models import Event, Assignment, SchoolClass, TeacherSubject, Submission


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

from django.http import JsonResponse
from .models import Announcement

def announcements_view(request):
    announcements = Announcement.objects.all()
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
    return JsonResponse(announcements_data, safe=False)


@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def assignment_view(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Authentication required")

    if request.method == "GET":
        if 'submission' in request.path:
            # Fetch submissions for a specific assignment
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

        if request.user.role == "teacher":
            assignments = Assignment.objects.filter(created_by=request.user).order_by('-created_at')
        elif request.user.role == "student":
            student_class = SchoolClass.objects.filter(students=request.user).first()
            if not student_class:
                return JsonResponse({"error": "No class assigned to this student"}, status=404)
            assignments = Assignment.objects.filter(classroom=student_class).order_by('-created_at')
            # submission status for students
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
        return JsonResponse({'assignments': data})


    elif request.method == "POST":
        if request.path.endswith('/submit'):
            if request.user.role != "student":
                return HttpResponseForbidden("Only students can submit assignments")
            try:
                assignment_id = request.POST.get('assignment_id')
                file = request.FILES.get('file')
                if not all([assignment_id, file]):
                    return HttpResponseBadRequest("Missing assignment_id or file")
                # File validation
                if not file.name.endswith('.pdf'):
                    return HttpResponseBadRequest("Only PDF files are allowed")
                if file.size > 5 * 1024 * 1024:  # 5MB limit
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

        if request.user.role != "teacher":
            return HttpResponseForbidden("Only teachers can create assignments")
        try:
            body = json.loads(request.body)
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
        except SchoolClass.DoesNotExist:
            return HttpResponseBadRequest("Invalid classroom ID")
        except Exception as e:
            return HttpResponseBadRequest(str(e))

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
