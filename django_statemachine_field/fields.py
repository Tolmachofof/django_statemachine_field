from django.db import models
from django.core import checks


__all__ = ('StateFieldMixin', 'StateCharField', 'StateIntegerField')


class StateDescriptor(object):
    """
    A wrapper for field. Supports defered-loading field logic: when the value
    is read from this object the first time, the query is executed.
    When the value is assigned on the field, it checks if value
    can be
    """

    def __init__(self, field_name, workflow, model):
        self.field_name = field_name
        self.workflow = workflow

    def __get__(self, instance, cls=None):
        """
        Returns the wrapped value from db on the first lookup.
        Returns the wrapped field value otherwise.
        """
        if instance is None:
            return self
        val = instance.__dict__.get(self.field_name)
        return val

    def __set__(self, instance, state):
        """
        Sets the new value on the field if it is available in the workflow
        for the current state. Raises exception otherwise.
        """
        current_state = self.__get__(instance, instance.__class__)
        if current_state is None and state in self.workflow:
            instance.__dict__[self.field_name] = state
        elif state in self.workflow[current_state]:
            instance.__dict__[self.field_name] = state
        else:
            # TODO: create exception
            raise ValueError()


class StateFieldMixin(models.Field):

    def __init__(self, *args, **kwargs):
        try:
            self.workflow = kwargs.pop('workflow')
        except KeyError:
            # TODO: create exception
            pass
        super(StateFieldMixin, self).__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super(StateFieldMixin, self).check(**kwargs)
        errors.extend(self._check_workflow_attribute(**kwargs))
        return errors

    def _check_workflow_attribute(self, **kwargs):
        if self.workflow is None:
            return [
                checks.Error(
                    "StateField must define a 'workflow' attribute.",
                    obj=self,
                    code='StateField.required_workflow'
                )
            ]
        # TODO: check if mapping
        else:
            return []

    def deconstruct(self):
        name, path, args, kwargs = super(StateFieldMixin, self).deconstruct()
        kwargs.setdefault('workflow', self.workflow)
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, private_only=False,
                            virtual_only=models.NOT_PROVIDED):
        super(StateFieldMixin, self).contribute_to_class(
            cls, name, private_only, virtual_only
        )
        setattr(cls, self.name, StateDescriptor(self.name, self.workflow, cls))


class StateCharField(StateFieldMixin, models.CharField):
    """
    State field for char values
    """


class StateIntegerField(StateFieldMixin, models.IntegerField):
    """
    State field for int values
    """
