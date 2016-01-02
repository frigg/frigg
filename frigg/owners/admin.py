from django.contrib import admin
from django.template.defaultfilters import pluralize

from frigg.owners.models import Owner


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'account_type',
        'queue_name',
        'image',
        'number_of_members',
    )
    list_filter = ['queue_name']
    actions = ['sync_members']

    def sync_members(self, request, queryset):
        for owner in queryset:
            owner.update_members()

        self.message_user(
            request,
            '{} owner{} was synced'.format(len(queryset), pluralize(len(queryset)))
        )

    sync_members.short_description = 'Sync members of selected owners'
