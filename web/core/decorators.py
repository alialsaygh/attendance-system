from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect
from functools import wraps


# this decorator checks if the user has the right role to access a page

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # if logged in first
            if not request.user.is_authenticated:
                # if its an ajax request return json error
                if 'live-data' in request.path or request.headers.get('Accept') == 'application/json':
                    return JsonResponse({"error": "not logged in", "present": [], "late": [], "total": 0}, status=401)
                return redirect('login')

            # if user has the correct role
            if request.user.role not in roles:
                # for ajax/fetch requests dont redirect just return error json
                if 'live-data' in request.path:
                    return JsonResponse({"error": "wrong role", "present": [], "late": [], "total": 0}, status=403)
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator