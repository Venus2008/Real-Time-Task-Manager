from task.serializers import TaskSerializer
from task.permissions import CanAssignTask,CanViewTask,CanEditTask
from task.models import Task
from notifications.services import NotificationService


from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import PermissionDenied
from notifications.tasks import send_task_assigned_email,send_task_updated_email
from django.db.models import Q



# Admin/Manager : Create and vier tasks
class TaskListCreateView(APIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  

        if user.role == "ADMIN":
            tasks = Task.objects.all().order_by("-created_at")

        elif user.role == "MANAGER":
            tasks = Task.objects.filter(
                Q(created_by=user) | Q(assigned_to=user),
                is_archived=False
            ).order_by("-created_at")

        elif user.role == "EMPLOYEE":
            tasks = Task.objects.filter(
                assigned_to=user,
                is_archived=False
            ).order_by("-created_at")

        else:
            tasks = Task.objects.none()

         # --- Query params filtering ---
        params = request.query_params

        # Filter by status
        status_param = params.get("status")
        if status_param:
            tasks = tasks.filter(status=status_param)
    
        # Filter by priority
        priority_param = params.get("priority")
        if priority_param:
            tasks = tasks.filter(priority=priority_param)

        # Filter by assignee (only useful for Admin/Manager)
        assignee = params.get("assignee")
        if assignee:
            tasks = tasks.filter(assigned_to_id=assignee)

        # Due before / after
        due_before = params.get("due_before")
        if due_before:
            tasks = tasks.filter(due_date__lte=due_before)

        due_after = params.get("due_after")
        if due_after:
            tasks = tasks.filter(due_date__gte=due_after)

        # Search in title/description
        search = params.get("search")
        if search:
            tasks = tasks.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        serializer = TaskSerializer(data=request.data)

        if serializer.is_valid():
            assignee = serializer.validated_data.get("assigned_to")
            CanAssignTask().validate_assignment(request.user, assignee)

            task = serializer.save(created_by=user)
            if assignee and assignee.email:
                send_task_assigned_email.delay(task.id, assignee.email)

            NotificationService.send(
                user=assignee,
                event="task_assigned",
                message=f"Task '{task.title}' assigned to you",
                task=task,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin/Manager : Modify and Delete the task role based permissions
class TaskModifyView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        # Return task if user has permission to view it,
        # otherwise return 403.
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return None
        
        if not CanViewTask().valid_viewer(user, task):
            raise PermissionDenied("You do not have access to this task.")
        return task

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        
        if not CanEditTask().has_object_permission(request, self, task):
            return Response(
                {"detail": "You do not have permission to edit this task."},status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            old_assignee = task.assigned_to
            updated_task = serializer.save()

            if updated_task.assigned_to:
                send_task_updated_email.delay(updated_task.id, updated_task.assigned_to.email)

    # Case 2: Assignee changed
            if "assigned_to" in serializer.validated_data and updated_task.assigned_to != old_assignee:
                send_task_assigned_email.delay(updated_task.id, updated_task.assigned_to.email)

            # If assignee changed → notify only the new assignee
            if updated_task.assigned_to != old_assignee:
                NotificationService.send(
                    user=updated_task.assigned_to,
                    event="task_reassigned",
                    message=f"You have been assigned to task '{updated_task.title}'",
                    task=updated_task,
                    created_by=request.user
                )
            else:
                # Otherwise → general update notification
                NotificationService.send(
                    user=updated_task.assigned_to,
                    event="task_updated",
                    message=f"Task '{updated_task.title}' has been updated.",
                    task=updated_task,
                    created_by=request.user
                )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        if not task:
            return Response({"detail": "Not authorized to delete this task or Task does not exists."}, status=status.HTTP_403_FORBIDDEN)

        user = request.user

        # Admin can hard delete any task
        if user.role == "ADMIN":
            task.delete()
            return Response({"detail": "Task deleted successfully."}, status=status.HTTP_200_OK)

        # Manager can archive (not delete) their own tasks
        elif user.role == "MANAGER":
            if task.created_by != user:
                return Response({"detail": "Managers can only archive their own tasks."},status=status.HTTP_403_FORBIDDEN)
            task.is_archived = True
            task.save()
            return Response({"detail": "Task archived successfully."}, status=status.HTTP_200_OK)
        # Employees cannot delete/archive
        return Response({"detail": "Employees cannot delete or archive tasks."},status=status.HTTP_403_FORBIDDEN)

