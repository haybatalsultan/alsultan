from django import forms
from django.utils.translation import get_language

from .models import AmbassadorProgramSetting


class AmbassadorSettingsForm(forms.ModelForm):
    class Meta:
        model = AmbassadorProgramSetting
        fields = ("enabled",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["enabled"].label = (
            "تفعيل برنامج سفير هيبة السلطان"
            if get_language() != "en"
            else "Enable Haybat Alsultan Ambassador Program"
        )
