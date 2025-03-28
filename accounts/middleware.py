from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import jwt
from django.conf import settings



class JWTMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip auth routes
        if request.path.startswith('/api/auth/'):
            return None

        auth_header = request.headers.get('Authorization', '').split()
        if len(auth_header) != 2 or auth_header[0] != 'Bearer':
            return JsonResponse({"error": "Invalid or missing Authorization header"}, status=401)
        token = auth_header[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload['user_id']  # Attach user_id to request
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)


# class RestrictEndpointsMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#         self.allowed_paths = ["/api/auth/", "/api/assignments/"]  # Define allowed paths
#
#     def __call__(self, request):
#         if request.path.startswith("/api/") and not any(request.path.startswith(path) for path in self.allowed_paths):
#             return HttpResponseNotFound()
#         return self.get_response(request)