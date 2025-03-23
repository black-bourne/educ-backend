import jwt
import datetime
import json
import secrets

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit

User = get_user_model()
from accounts.tasks import send_otp_email

@ratelimit(key='ip', rate='5/m', method='POST')  # 10 requests per minute per IP
@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
        # Check rate limit
    if getattr(request, 'limited', False):
        return JsonResponse({'error': 'Too many attempts, please try again later'}, status=429)
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Authenticate the user
    user = authenticate(request, email=email, password=password)
    if user is None:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    otp_code = secrets.token_hex(3).upper()  # Generates a 6-character hexadecimal code (e.g., "A1B2C3")
    cache_key = f'otp_{user.id}'
    cache.set(cache_key, otp_code, timeout=300)  # 300 seconds = 5 minutes exp in redis

    # Send the OTP via email
    try:
        send_otp_email(email, otp_code) # celery
    except Exception as e:
        return JsonResponse({'error': f'Failed to queue OTP email: {str(e)}'}, status=500)

    # Generate JWT token
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'is_2fa_verified': False,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=15),
        'iat': datetime.datetime.now(datetime.UTC),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    return JsonResponse({'token': token})


@csrf_exempt
@ratelimit(key='ip', rate='5/m', method='POST')
def verify_otp(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if getattr(request, 'limited', False):
        return JsonResponse({'error': 'Too many attempts'}, status=429)

    try:
        data = json.loads(request.body)
        token = data.get('token')
        otp = data.get('otp')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    cached_otp = cache.get(f'otp_{user_id}')
    if cached_otp is None or cached_otp != otp:
        return JsonResponse({'error': 'Invalid or expired OTP'}, status=401)

    payload['is_2fa_verified'] = True
    payload['exp'] = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
    new_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    cache.delete(f'otp_{user_id}')
    return JsonResponse({'token': new_token})


@csrf_exempt
@ratelimit(key='ip', rate='5/h', method='POST')  # Limit to 5 requests per hour per IP
def reset_password_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        uidb64 = data.get("uidb64")
        token = data.get("token")
        password = data.get("password")
        validate_password(password)
        if not all([uidb64, token, password]):
            return JsonResponse({"error": "Missing required fields"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
        # regenerates the token using the user’s data (password hash and timestamp) and checks if it matches the provided token and hasn’t expired.
        if default_token_generator.check_token(user, token):
            user.set_password(password)
            user.is_active = True  # Activate user after setting password
            user.save()
            return JsonResponse({"message": "Password set successfully"})
        return JsonResponse({"error": "Invalid or expired token"}, status=401)
    except (User.DoesNotExist, ValueError):
        return JsonResponse({"error": "Invalid user or token"}, status=401)


@csrf_exempt
@ratelimit(key='ip', rate='5/h', method='POST')
def request_reset_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email")
        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"http://localhost:3000/reset/{uid}/{token}"
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Password Reset Request</h2>
                <p>Click below to reset your password:</p>
                <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px;">
                    Reset Password
                </a>
                <p style="font-size: 12px; color: #666;">This link expires in 24 hours.</p>
            </body>
        </html>
        """
        send_mail(
            subject="Reset Your Password",
            message=f"Click here to reset your password: {reset_url}",
            from_email="noreply@localhost.com",
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return JsonResponse({"message": "Reset email sent"})
    except User.DoesNotExist:
        # Return success anyway to prevent email enumeration
        return JsonResponse({"message": "Reset email sent"})
    except Exception as e:
        return JsonResponse({"error": f"Failed to send email: {str(e)}"}, status=500)