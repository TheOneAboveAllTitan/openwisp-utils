from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class TimeReadonlyAdminMixin(object):
    """
    mixin that automatically flags
    `created` and `modified` as readonly
    """
    def __init__(self, *args, **kwargs):
        self.readonly_fields += ('created', 'modified',)
        super().__init__(*args, **kwargs)


class ReadOnlyAdmin(ModelAdmin):
    """
    Disables all editing capabilities
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_fields = [f.name for f in self.model._meta.fields]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:  # pragma: no cover
            del actions['delete_selected']
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):  # pragma: nocover
        pass

    def delete_model(self, request, obj):  # pragma: nocover
        pass

    def save_related(self, request, form, formsets, change):  # pragma: nocover
        pass

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super().change_view(request, object_id, extra_context=extra_context)


class AlwaysHasChangedMixin(object):
    def has_changed(self):
        """
        This django-admin trick ensures the settings
        are saved even if default values are unchanged
        (without this trick new setting objects won't be
        created unless users change the default values)
        """
        if self.instance._state.adding:
            return True
        return super().has_changed()


class UUIDAdmin(ModelAdmin):
    """
    Defines a field name uuid whose value is that
    of the id of the object
    """

    def uuid(self, obj):
        return obj.pk

    def _process_fields(self, fields, request, obj):
        fields = list(fields)
        if obj:
            if 'uuid' in fields:
                fields.remove('uuid')
                fields.insert(0, 'uuid')
        else:
            # remove read_only fields
            for field in self.readonly_fields:
                if field in fields:
                    fields.remove(field)
        return tuple(fields)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return self._process_fields(fields, request, obj)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return self._process_fields(fields, request, obj)

    class Media:
        js = ('admin/js/jquery.init.js', 'openwisp-utils/js/uuid.js')

    uuid.short_description = _('UUID')


class ReceiveUrlAdmin(ModelAdmin):
    """
    Return a receive_url field whose value is that of
    a view_name concatenated with the obj id and/or
    with the key of the obj
    """
    receive_url_querystring_arg = 'key'
    receive_url_object_arg = 'pk'
    receive_url_name = None

    def receive_url(self, obj):
        """
        :param obj: Object for which the url is generated
        """
        if self.receive_url_name is None:
            raise ValueError('receive_url_name is not set up')
        reverse_kwargs = {}
        if self.receive_url_object_arg:
            reverse_kwargs = {
                self.receive_url_object_arg: getattr(obj, self.receive_url_object_arg)
            }
        url = reverse(self.receive_url_name, kwargs=reverse_kwargs)
        if self.receive_url_querystring_arg:
            return '{0}?{1}={2}'.format(
                url,
                self.receive_url_querystring_arg,
                getattr(obj, self.receive_url_querystring_arg)
            )
        else:
            return url

    class Media:
        js = ('admin/js/jquery.init.js', 'openwisp-utils/js/receive_url.js')

    receive_url.short_description = _('URL')
