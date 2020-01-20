import easy
from admin_actions.admin import ActionsModelAdmin
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from .models import Destination, UploadedMedia, DESTINATION_MODULES


class FixedAMA(ActionsModelAdmin):
    def get_urls(self):
        urls = super(ActionsModelAdmin, self).get_urls()

        action_row_urls = []
        for method_name in self.actions_row:
            method = getattr(self, method_name)
            action_row_urls.append(
                path(getattr(method, 'url_path', method_name) + '/<pk>/', self.admin_site.admin_view(method), name=method_name))

        action_detail_urls = []
        for method_name in self.actions_detail:
            method = getattr(self, method_name)
            action_detail_urls.append(
                path(getattr(method, 'url_path', method_name) + '/<pk>/', self.admin_site.admin_view(method), name=method_name))

        action_list_urls = []
        for method_name in self.actions_list:
            method = getattr(self, method_name)

            action_list_urls.append(
                path(getattr(method, 'url_path', method_name), self.admin_site.admin_view(method), name=method_name)
            )

        return action_list_urls + action_row_urls + action_detail_urls + urls


for module in DESTINATION_MODULES:
    @admin.register(module)
    class _(FixedAMA):
        actions_row = actions_detail = 'destination',

        def destination(self, request, pk):
            obj = module.objects.get(pk=pk)
            return redirect(f'admin:app_destination_change', object_id=obj.destination.pk)


@admin.register(Destination)
class DestinationAdmin(FixedAMA):
    list_display = 'id', 'title', 'owner', 'module',
    list_filter = 'owner',
    actions_row = actions_detail = 'config',

    module = easy.SimpleAdminField('config.MODULE_NAME')

    def config(self, request, pk):
        obj = Destination.objects.get(pk=pk)
        return redirect(f'admin:app_{obj.config_type.model}_change', object_id=obj.config_id)


@admin.register(UploadedMedia)
class UploadedMediaAdmin(FixedAMA):
    list_display = 'filename', 'is_video', 'destination_', 'owner_', 'datetime', 'status',
    list_filter = 'destination', 'destination__owner', 'is_video', 'status',
    date_hierarchy = 'datetime'
    actions_row = actions_detail = 'file_link',

    filename = easy.SimpleAdminField('file.name')
    destination_ = easy.ForeignKeyAdminField('destination')
    owner_ = easy.ForeignKeyAdminField('destination.owner')

    def file_link(self, request, pk):
        obj = UploadedMedia.objects.get(pk=pk)
        return redirect(obj.file.url)
