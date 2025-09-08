from task.serializers import TaskSerializer,TaskUpdateSerializer
from task.permissions import IsAdminFullAccess,IsManagerTaskOwner
from task.models import Task,TaskUpdate

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.db.models import Q  


# Admin: List of all active tasks + create tasks
class TaskListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminFullAccess]

    def get(self, request):
        tasks = Task.objects.filter(is_archived=False).order_by("-created_at")
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# Admin: Retrieve, Modify, Delete any task
class TaskDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminFullAccess]

    def get_object(self, pk):
        return get_object_or_404(Task, pk=pk)

    def get(self, request, pk):
        task = self.get_object(pk)

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        task = self.get_object(pk)

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Admin can update everything
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        task = self.get_object(pk)

        task.delete()  # Hard delete (Admin only)
        return Response({"detail": "Task deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# Manager : List of all created tasks by itself + create tasks
class ManagerTaskListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsManagerTaskOwner]  

    def get(self, request):
        """List all tasks created by OR assigned to this Manager."""
        tasks = Task.objects.filter(
            Q(created_by=request.user) | Q(assigned_to=request.user)
        ).distinct()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Manager creates a task (only for Employees)."""
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            assignee = serializer.validated_data.get("assigned_to")  # 🔹 FIXED
            if assignee.role != "EMPLOYEE":
                return Response(
                    {"detail": "Managers can assign tasks only to Employees."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Manager : Retrieve, Modify, Delete task createde by him/her
class ManagerTaskDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,IsManagerTaskOwner]

    def get_object(self, pk, user):
        return get_object_or_404(Task, pk=pk, created_by=user)

    def get(self, request, pk):
        task = self.get_object(pk, request.user)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    def put(self, request, pk):
        task = self.get_object(pk, request.user)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Manager can update their own tasks
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = self.get_object(pk, request.user)   #Instead of hard delete, archive the task
        task.status = "ARCHIVED"
        task.save()
        return Response({"detail": "Task archived successfully"}, status=status.HTTP_200_OK)


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
            serializer.save(updated_by=request.user, task=task)
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

