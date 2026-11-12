from uuid import uuid4
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Socio, Entrenador, Membresia, Pago, Clase

class EstiloForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type':'date'})
            elif isinstance(field, forms.TimeField):
                field.widget = forms.TimeInput(format='%H:%M', attrs={'type':'time'})

class PersonaForm(EstiloForm):
    clave = forms.CharField(label='Contraseña de acceso', required=False, widget=forms.PasswordInput,
        help_text='Obligatoria al crear la cuenta. Al editar, déjala vacía para conservarla.')
    def clean_clave(self):
        clave = self.cleaned_data.get('clave')
        if not clave and not self.instance.usuario_id:
            raise ValidationError('Ingresa una contraseña para la cuenta.')
        if clave:
            validate_password(clave, self.instance.usuario if self.instance.usuario_id else None)
        return clave
    @transaction.atomic
    def save(self, commit=True):
        persona = super().save(commit=False)
        user = persona.usuario if persona.usuario_id else User(username='fc_' + uuid4().hex[:20])
        user.email = persona.correo
        user.first_name = persona.nombre
        if self.cleaned_data.get('clave'):
            user.set_password(self.cleaned_data['clave'])
        user.save()
        persona.usuario = user
        if commit:
            persona.save()
        return persona

class SocioForm(PersonaForm):
    class Meta:
        model = Socio
        fields = ['nombre','rut','correo','telefono']

class EntrenadorForm(PersonaForm):
    class Meta:
        model = Entrenador
        fields = ['nombre','rut','correo','telefono','especialidad']

class MembresiaForm(EstiloForm):
    class Meta:
        model = Membresia
        fields = ['socio','tipo_plan','precio','fecha_inicio','fecha_fin','estado']

class PagoForm(EstiloForm):
    class Meta:
        model = Pago
        fields = ['membresia','monto','fecha_pago','metodo_pago','estado']

class ClaseForm(EstiloForm):
    class Meta:
        model = Clase
        fields = ['nombre','descripcion','entrenador','fecha','hora','cupo_maximo','estado']

def perfil_form(model):
    class PerfilForm(EstiloForm):
        class Meta:
            fields = ['nombre','correo','telefono']
        @transaction.atomic
        def save(self, commit=True):
            persona = super().save(commit=commit)
            user = persona.usuario
            user.email, user.first_name = persona.correo, persona.nombre
            user.save(update_fields=['email','first_name'])
            return persona
    PerfilForm._meta.model = model
    PerfilForm.base_fields = forms.models.fields_for_model(model, fields=['nombre','correo','telefono'])
    return PerfilForm
