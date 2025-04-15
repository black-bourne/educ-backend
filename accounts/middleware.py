# accounts/middleware.py
import jwt
import logging
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)
User = get_user_model()

class SimpleJWTMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        skip_paths = ["/api/auth/login", "/api/auth/reset-email", "/api/auth/reset" "/api/auth/verify-otp", "/admin/"]
        if any(request.path.startswith(path) for path in skip_paths):
            logger.debug("Skipping authentication for auth or admin path")
            return None

        if not auth_header:
            request.user = AnonymousUser()
            return None

        if not auth_header.startswith("Bearer "):
            request.user = AnonymousUser()
            return None

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            is_2fa_verified = payload.get("is_2fa_verified", False)
            if not user_id:
                return JsonResponse({"error": "Invalid token payload"}, status=403)
            if not is_2fa_verified:
                return JsonResponse({"error": "2FA verification required"}, status=403)

            user = User.objects.get(pk=user_id)
            request.user = user
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError as e:
            return JsonResponse({"error": "Invalid token"}, status=401)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        return None