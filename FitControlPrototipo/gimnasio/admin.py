from django.contrib import admin

from django.contrib import admin
from gimnasio.models import Socio, Entrenador, Membresia, Pago, Clase, Reserva, Asistencia

class SocioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'correo', 'telefono']

class EntrenadorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'especialidad', 'correo']

class MembresiaAdmin(admin.ModelAdmin):
    list_display = ['socio', 'tipo_plan', 'precio', 'fecha_inicio', 'fecha_fin', 'estado']

class PagoAdmin(admin.ModelAdmin):
    list_display = ['membresia', 'monto', 'fecha_pago', 'metodo_pago', 'estado']

class ClaseAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'entrenador', 'fecha', 'hora', 'cupo_maximo', 'estado']

class ReservaAdmin(admin.ModelAdmin):
    list_display = ['socio', 'clase', 'fecha_reserva', 'estado']

class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ['socio', 'fecha', 'hora_entrada', 'estado']

admin.site.register(Socio, SocioAdmin)
admin.site.register(Entrenador, EntrenadorAdmin)
admin.site.register(Membresia, MembresiaAdmin)
admin.site.register(Pago, PagoAdmin)
admin.site.register(Clase, ClaseAdmin)
admin.site.register(Reserva, ReservaAdmin)
admin.site.register(Asistencia, AsistenciaAdmin)