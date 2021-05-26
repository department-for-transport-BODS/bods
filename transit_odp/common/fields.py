from django.core.files.storage import Storage, default_storage
from django.db import models


class CallableStorageFileField(models.FileField):
    """Backport of __init__ for Django 3.1 FileField adds the option to
    specify a callable storage.
    """

    def __init__(
        self, verbose_name=None, name=None, upload_to="", storage=None, **kwargs
    ):
        super().__init__(verbose_name, name, **kwargs)
        self.storage = storage or default_storage
        if callable(self.storage):
            # Hold a reference to the callable for deconstruct().
            self._storage_callable = self.storage
            self.storage = self.storage()
            if not isinstance(self.storage, Storage):
                raise TypeError(
                    "%s.storage must be a subclass/instance of %s.%s"
                    % (
                        self.__class__.__qualname__,
                        Storage.__module__,
                        Storage.__qualname__,
                    )
                )

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.storage is not default_storage:
            kwargs["storage"] = getattr(self, "_storage_callable", self.storage)
        return name, path, args, kwargs


class NullFileField(models.FileField):
    """
    A custom FileField which defaults unique=True and saves unset files to the
    DB as NULL rather than an empty string
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("unique", True)
        kwargs["null"] = True
        kwargs["blank"] = True
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.null is not False:
            kwargs["null"] = True
        if self.blank is not True:
            kwargs["blank"] = False
        if self.unique is not True:
            kwargs["unique"] = False
        return name, path, args, kwargs

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value == "":
            value = None
        return value
