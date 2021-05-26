from django.forms import Select


class SelectDisabledChoices(Select):
    """
    Useage:

    class SearchFilterForm(forms.Form):
        data_type = forms.MultipleChoiceField(
            choices=(
                ('timetables', 'Timetables'),
                ('realtime', 'Real-time'),
                ('fares', 'Fares'),
            ),
            widget=SelectDisabledChoices
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['data_type'].widget.disabled_choices = ['realtime', 'fares']
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._disabled_choices = []

    @property
    def disabled_choices(self):
        return self._disabled_choices

    @disabled_choices.setter
    def disabled_choices(self, other):
        self._disabled_choices = other

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if value in self.disabled_choices:
            option_dict["attrs"]["disabled"] = "disabled"
        return option_dict
