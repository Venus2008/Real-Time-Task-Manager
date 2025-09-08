from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class CanAssignTask(BasePermission):
   
    # Permission to validate who can assign tasks to whom.
    # - Admin cannot assign tasks to another Admin.
    # - Manager can assign tasks only to Employees.
    # - Employees cannot assign tasks at all.
   

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def validate_assignment(self, user, assignee):
        # Admin rules
        if user.role == "ADMIN":
            if assignee.role == "ADMIN":
                raise PermissionDenied("Admin cannot assign tasks to another Admin.")

        # Manager rules
        elif user.role == "MANAGER":
            if assignee.role != "EMPLOYEE":
                raise PermissionDenied("Managers can assign tasks only to Employees.")

        # Employee rules
        else:
            raise PermissionDenied("Employees cannot create or assign tasks.")

        return True
    

class CanViewTask(BasePermission):
    # Permission to check who can see the Task
    # - Admin can see all the tasks
    # - Manager can see the tasks created by them or assign to them
    # - Employee can see only the task that assign to them

    def valid_viewer(self,user,task):
         if user.role == "ADMIN":
            return task

        # Manager can view tasks they created or assigned to them
         if user.role == "MANAGER":
            if task.created_by == user or task.assigned_to == user:
                return task

        # Employee can view only their assigned tasks
         if user.role == "EMPLOYEE":
            if task.assigned_to == user:
                return task

         return None


class CanEditTask(BasePermission):
    
    # - Admin can edit any task
    # - Manager can edit only tasks they created
    # - Employees cannot edit tasks
    

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin can edit any task
        if user.role == "ADMIN":
            return True

        # Manager can edit only their own tasks
        if user.role == "MANAGER":
            return obj.created_by == user

        # Employees cannot edit
        return False