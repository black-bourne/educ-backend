import jwt
from django.http import JsonResponse

from educ_backend import settings


def role_required(allowed_roles):
  def decorator(view_func):
    def wrapper(request, *args, **kwargs):
      if hasattr(request, "user_id"):
        payload = jwt.decode(request.headers["Authorization"].split()[1], settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") not in allowed_roles:
          return JsonResponse({"error": "Permission denied"}, status=403)
      return view_func(request, *args, **kwargs)
    return wrapper
  return decorator