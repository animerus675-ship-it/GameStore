import json

from django.http import JsonResponse


def json_ok(data=None, status=200):
    return JsonResponse({"ok": True, "data": data, "error": None}, status=status)


def json_error(error, status=400, data=None):
    return JsonResponse({"ok": False, "data": data, "error": error}, status=status)


def parse_json_body(request):
    if not request.body:
        return None, "Request body is empty."
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "Invalid JSON body."

    if not isinstance(payload, dict):
        return None, "JSON body must be an object."

    return payload, None


def ensure_authenticated(request):
    if not request.user.is_authenticated:
        return json_error("Authentication required.", status=401)
    return None
