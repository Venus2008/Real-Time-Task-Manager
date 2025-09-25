from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from urllib.parse import urlencode
from django.db.models import Q



from notifications.services import NotificationService
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.enums import NotificationType
from task.models import Task
from account.models import User


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        params = request.query_params
        query_string = urlencode(params, doseq=True)

        cache_key = f"notifications_{request.user.email}_{query_string}"

        # Try cache first
        data = cache.get(cache_key)
        if data:
            return Response(data)
        
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")

        # --- Filters ---
        title = params.get("title")
        if title:
            qs = qs.filter(task__title__icontains=title)

        event = params.get("event")
        if event:
            qs = qs.filter(event__iexact=event)  # change field name if needed


        # Optional search across multiple fields
        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(task__title__icontains=search) |
                Q(event_type__icontains=search)
            )


        serializer = NotificationSerializer(qs, many=True)
        data = serializer.data

        cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes

        return Response(serializer.data)




class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        task_id = request.data.get("task_id")
        event = request.data.get("event")

        qs = Notification.objects.filter(user=request.user, is_read=False)

        if task_id:
            qs = qs.filter(task_id=task_id)
        if event:
            qs = qs.filter(event=event)

        updated = qs.update(is_read=True)

        return Response({"detail": f"{updated} notifications marked as read"}, status=200)



class MessageView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        task_id = request.data.get("task_id")
        message = request.data.get("message")

        if not task_id or not message:
            return Response({"detail": "Task ID and message are required."}, status=400)

        task = get_object_or_404(Task, id=task_id)

        # Only assigner or assignee can chat
        if request.user not in [task.created_by, task.assigned_to]:
            return Response({"detail": "Not allowed"}, status=403)

        # Choose recipient
        recipient = task.assigned_to if request.user == task.created_by else task.created_by


        NotificationService.send(
            user=recipient,
            event="general",
            message=message,
            task=task,
            created_by=request.user
        )

        return Response({"detail": "Message sent successfully."}, status=201)