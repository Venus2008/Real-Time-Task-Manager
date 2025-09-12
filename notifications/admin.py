from django.contrib import admin
from notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id","user","event","status","task","message_preview","is_read","created_at","updated_at",)
    list_filter = ("event", "is_read", "created_at","status")
    search_fields = ("user__email", "task__title", "message","status")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def message_preview(self, obj):
        return obj.message[:50] + ("..." if len(obj.message) > 50 else "")
    message_preview.short_description = "Message"


admin.site.register(Notification,NotificationAdmin)