from functools import wraps

from django.http import JsonResponse

from accounts.models import ApiToken


def get_api_token_from_request(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()

    return request.headers.get("X-Api-Key", "").strip()


def authenticate_api_request(request):
    return ApiToken.authenticate(get_api_token_from_request(request))


def api_token_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = authenticate_api_request(request)
        if user is None:
            return JsonResponse({"error": "Authentication required"}, status=401)

        request.api_user = user
        return view_func(request, *args, **kwargs)

    return wrapper
