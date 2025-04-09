import re
import jwt
import logging
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)
User = get_user_model()

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Compile skip patterns (defaults to /api/auth/)
        skip_paths = getattr(settings, "JWT_SKIP_PATHS", [r"^/api/auth/"])
        self.skip_regex = [re.compile(p) for p in skip_paths]

    def __call__(self, request):
        # Skip any path matching skip patterns
        for regex in self.skip_regex:
            if regex.match(request.path):
                return self.get_response(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            request.user = AnonymousUser()
            return self.get_response(request)

        token = auth_header.split(" ", 1)[1]

        try:
            # Decode and validate token
            options = {"require": ["exp", "iat"]}
            decode_kwargs = {
                "key": settings.SECRET_KEY,
                "algorithms": [getattr(settings, "JWT_ALGORITHM", "HS256")],
                "options": options,
            }
            # Optional audience/issuer checks
            if hasattr(settings, "JWT_AUDIENCE"):
                decode_kwargs["audience"] = settings.JWT_AUDIENCE
            if hasattr(settings, "JWT_ISSUER"):
                decode_kwargs["issuer"] = settings.JWT_ISSUER

            payload = jwt.decode(token, **decode_kwargs)
        except jwt.ExpiredSignatureError:
            logger.warning("JWT expired")
            return JsonResponse({"error": "token_expired"}, status=401)
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT: {e}")
            return JsonResponse({"error": "invalid_token"}, status=401)

        # Verify required claims
        user_id = payload.get("user_id")
        is_2fa = payload.get("is_2fa_verified", False)
        if not user_id or not is_2fa:
            return JsonResponse({"error": "invalid_token_payload"}, status=403)

        # Fetch the user
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "user_not_found"}, status=401)

        if not user.is_active:
            return JsonResponse({"error": "user_inactive"}, status=403)

        # All good: attach to request
        request.user = user
        request.jwt_payload = payload

        return self.get_response(request)
