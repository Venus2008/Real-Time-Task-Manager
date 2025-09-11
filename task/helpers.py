from django.db.models import Q
from task.models import Task

class TaskVisibilityHelper:
    @staticmethod
    def get_visible_tasks(user):
        if user.role == "ADMIN":
            return Task.objects.all().order_by("-created_at")

        elif user.role == "MANAGER":
            return Task.objects.filter(
                Q(created_by=user) | Q(assigned_to=user),
                is_archived=False
            ).order_by("-created_at")

        elif user.role == "EMPLOYEE":
            return Task.objects.filter(
                assigned_to=user,
                is_archived=False
            ).order_by("-created_at")

        return Task.objects.none()