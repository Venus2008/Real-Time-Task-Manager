from notifications.enums import NotificationType
from task.serializers import TaskSerializer,TaskUpdateSerializer
from task.permissions import CanAssignTask,CanViewTask,CanEditTask
from task.models import Task
from notifications.models import Notification
from notifications.enums import NotificationType



from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import PermissionDenied
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q
from django.db import transaction





# Manager/Emplyee : Share Updates on the tasks assigned  
class TaskUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        # only allow updates for tasks assigned to this manager
        try:
            task = Task.objects.get(id=task_id, assigned_to=request.user)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found or not assigned to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TaskUpdateSerializer(data=request.data)
        if serializer.is_valid():
            task_update=serializer.save(updated_by=request.user, task=task)

            if task_update.status:
                task.status = task_update.status
                task.save(update_fields=["status"])

            # Notify the task creator about the update
            recipients = [task.created_by, task.assigned_to]
            recipients = [u for u in recipients if u and u != request.user]  # avoid self-notify

            notifications = []
            for user in recipients:
                notif = Notification.objects.create(
                    user=user,
                    event=NotificationType.TASK_UPDATED,
                    task=task,
                    message=f"Task '{task.title}' was updated by {request.user.name}",
                    created_by=request.user
                )
                notifications.append((user, notif))

            # WebSocket push after commit
            channel_layer = get_channel_layer()

            def _send():
                for user, notif in notifications:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{user.id}",
                        {
                            "type": "send_notification",
                            "notification_id": notif.id,
                            "event": notif.event,
                            "task_id": task.id,
                            "title": task.title,
                            "message": notif.message,
                            "updated_by": request.user.email,
                            "created_at": notif.created_at.isoformat(),
                        }
                    )

            transaction.on_commit(_send)
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, task_id):
        # fetch all updates for a task assigned to this manager
        try:
            task = Task.objects.get(id=task_id, assignee=request.user)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found or not assigned to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        updates = task.updates.all().order_by("-created_at")
        serializer = TaskUpdateSerializer(updates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        serializer = TaskSerializer(data=request.data)

        if serializer.is_valid():
            assignee = serializer.validated_data.get("assigned_to")
            CanAssignTask().validate_assignment(request.user, assignee)

            task = serializer.save(created_by=user)

            notification = Notification.objects.create(
                user=assignee,
                event=NotificationType.TASK_ASSIGNED,
                task=task,
                message=f"Task '{task.title}' has been assigned to you",
                created_by=request.user
            )

            # Send WebSocket notification
            channel_layer = get_channel_layer()
                # Ensure the notification is sent after the transaction commits
            def _send():
                async_to_sync(channel_layer.group_send)(
                    f"notifications_{assignee.id}",  # matches your consumer's group
                    {
                        "type": "send_notification",  # must match consumer method
                        "notification_id": notification.id,
                        "event": notification.event,
                        "task_id": task.id,
                        "title": task.title,
                        "assigned_to": assignee.email,
                        "message": notification.message,
                        "created_at": notification.created_at.isoformat(),
                    }
                )

            transaction.on_commit(_send)
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
        task = self.get_object(pk, request.user)
        if not task:
            return Response({"detail": "Not authorized to view this task."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        task = self.get_object(pk, request.user)
        if not task:
            return Response({"detail": "Not authorized to edit this task."}, status=status.HTTP_403_FORBIDDEN)
        
        if not CanEditTask().has_object_permission(request, self, task):
            return Response(
                {"detail": "You do not have permission to edit this task."},status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
        # Save old values before updating
            old_values = {field: getattr(task, field, None) for field in serializer.validated_data.keys()}

            # Save updated task
            updated_task = serializer.save()

            updated_fields = []
            for field, new_value in serializer.validated_data.items():
                old_value = old_values.get(field)
                if old_value != new_value:
                    updated_fields.append((field, old_value, new_value))

            # Send notifications
            channel_layer = get_channel_layer()

            for field, old_value, new_value in updated_fields:
                if field == "assigned_to":
                    # Notify the NEW assignee only
                    if new_value:
                        async_to_sync(channel_layer.group_send)(
                            f"notifications_{new_value.id}",
                            {
                                "type": "send_notification",
                                "event": "task_assigned",
                                "task_id": updated_task.id,
                                "title": updated_task.title,
                                "message": f"You have been assigned task '{updated_task.title}'",
                            }
                        )
                else:
                    # Notify the current assignee for other field updates
                    assignee = updated_task.assigned_to
                    if assignee:
                        async_to_sync(channel_layer.group_send)(
                            f"notifications_{assignee.id}",
                            {
                                "type": "send_notification",
                                "event": "task_updated",
                                "task_id": updated_task.id,
                                "title": updated_task.title,
                                "field": field,
                                "old_value": str(old_value),
                                "new_value": str(new_value),
                                "message": f"Task '{updated_task.title}' → {field} changed from '{old_value}' to '{new_value}'",
                            }
                        )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = self.get_object(pk, request.user)
        if not task:
            return Response({"detail": "Not authorized to delete this task or Task does not exists."}, status=status.HTTP_403_FORBIDDEN)

        user = request.user

        # Admin can hard delete any task
        if user.role == "ADMIN":
            task.delete()
            return Response({"detail": "Task deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        # Manager can archive (not delete) their own tasks
        elif user.role == "MANAGER":
            if task.created_by != user:
                return Response({"detail": "Managers can only archive their own tasks."},status=status.HTTP_403_FORBIDDEN)
            task.is_archived = True
            task.save()
            return Response({"detail": "Task archived successfully."}, status=status.HTTP_200_OK)
        # Employees cannot delete/archive
        return Response({"detail": "Employees cannot delete or archive tasks."},status=status.HTTP_403_FORBIDDEN)

