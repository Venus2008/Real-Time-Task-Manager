from django.http import JsonResponse
from django.conf import settings

class CustomHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.excluded_paths = ["/admin/", "/static/", "/favicon.ico"] # exclude admin & static paths

    def __call__(self, request):
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return self.get_response(request)
        api_key = request.headers.get("X-API-KEY")

        if api_key != getattr(settings, "CUSTOM_API_KEY", None):
            return JsonResponse({"detail": "Invalid or missing API key"}, status=403)

        return self.get_response(request)
