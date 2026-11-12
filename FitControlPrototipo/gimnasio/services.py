from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Clase, Reserva, membresia_vigente

@transaction.atomic
def reservar(socio, clase_id):

    clase = Clase.objects.select_for_update().get(pk=clase_id)
    if not clase.consultar_disponibilidad():
        raise ValidationError('La clase no está disponible o ya no tiene cupos.')
    if not membresia_vigente(socio) or not membresia_vigente(socio, clase.fecha):
        raise ValidationError('El socio necesita una membresía vigente hoy y en la fecha de la clase.')
    reserva = Reserva.objects.filter(socio=socio, clase=clase).first()
    if reserva and reserva.estado == 'Confirmada':
        raise ValidationError('El socio ya tiene una reserva en esta clase.')
    if reserva:
        reserva.estado = 'Confirmada'
        reserva.save(update_fields=['estado'])
    else:
        reserva = Reserva.objects.create(socio=socio, clase=clase)
    return reserva
