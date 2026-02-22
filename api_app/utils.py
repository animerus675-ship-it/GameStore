import json

from django.http import JsonResponse


def json_ok(data=None, status=200):
    return JsonResponse(
        {
            "ok": True,
            "data": data if data is not None else {},
            "error": None,
        },
        status=status,
    )


def json_error(error, status=400, data=None):
    return JsonResponse(
        {
            "ok": False,
            "data": data,
            "error": error,
        },
        status=status,
    )


def parse_json_body(request):
    raw_body = request.body.decode("utf-8").strip()
    if not raw_body:
        return None, "Request body is empty."

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return None, "Request body must be valid JSON."

    if not isinstance(payload, dict):
        return None, "JSON body must be an object."

    return payload, None


def ensure_authenticated(request):
    if request.user.is_authenticated:
        return None
    return json_error("Authentication required.", status=401)


def ensure_manager(request):
    user = request.user
    if not user.is_authenticated:
        return json_error("Authentication required.", status=401)
    if user.is_superuser or user.groups.filter(name="manager").exists():
        return None
    return json_error("Permission denied.", status=403)
