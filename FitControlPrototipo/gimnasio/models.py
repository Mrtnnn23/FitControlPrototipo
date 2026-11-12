from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone

def validar_rut(value):
    rut = value.replace('.', '').replace('-', '').upper().strip()
    if len(rut) < 2 or not rut[:-1].isdigit():
        raise ValidationError('Ingresa un RUT válido, por ejemplo 12.345.678-5.')
    total = sum(int(n) * (2 + i % 6) for i, n in enumerate(reversed(rut[:-1])))
    digito = 11 - total % 11
    if rut[-1] != ('0' if digito == 11 else 'K' if digito == 10 else str(digito)):
        raise ValidationError('El dígito verificador del RUT no es correcto.')

class Persona(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=50)
    rut = models.CharField(max_length=12, unique=True, validators=[validar_rut])
    correo = models.EmailField(max_length=50)
    telefono = models.CharField(max_length=15)
    class Meta:
        abstract = True
    def clean(self):
        self.correo = self.correo.strip().lower()
        self.rut = self.rut.replace('.', '').replace('-', '').upper().strip()
        if not self.telefono.replace('+', '').replace(' ', '').isdigit():
            raise ValidationError({'telefono': 'Ingresa un teléfono válido.'})
        otros = User.objects.filter(email__iexact=self.correo)
        if self.usuario_id:
            otros = otros.exclude(pk=self.usuario_id)
        if otros.exists():
            raise ValidationError({'correo': 'Este correo ya tiene una cuenta.'})
    def __str__(self):
        return self.nombre

class Socio(Persona):
    pass

class Entrenador(Persona):
    especialidad = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = 'Entrenadores'

class Membresia(models.Model):
    PLANES = [('Mensual','Mensual'), ('Semestral','Semestral'), ('Anual','Anual')]
    ESTADOS = [('Activa','Activa'), ('Vencida','Vencida'), ('Cancelada','Cancelada')]
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    tipo_plan = models.CharField(max_length=20, choices=PLANES)
    precio = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Activa')
    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({'fecha_fin': 'El vencimiento debe ser posterior o igual al inicio.'})
        if self.precio is not None and self.precio <= 0:
            raise ValidationError({'precio': 'El precio debe ser mayor a cero.'})
    def activar(self):
        self.estado = 'Activa'
        self.save()
    def cancelar(self):
        self.estado = 'Cancelada'
        self.save()
    def verificar_vigencia(self, fecha=None):
        fecha = fecha or timezone.localdate()
        return self.estado == 'Activa' and self.fecha_inicio <= fecha <= self.fecha_fin
    def __str__(self):
        return f'{self.socio.nombre} · {self.tipo_plan}'

def membresia_vigente(socio, fecha=None):
    fecha = fecha or timezone.localdate()
    return socio.membresia_set.filter(estado='Activa', fecha_inicio__lte=fecha, fecha_fin__gte=fecha).exists()

class Pago(models.Model):
    ESTADOS = [('Pendiente','Pendiente'), ('Pagado','Pagado')]
    membresia = models.ForeignKey(Membresia, on_delete=models.CASCADE)
    monto = models.PositiveIntegerField()
    fecha_pago = models.DateField()
    metodo_pago = models.CharField(max_length=30, choices=[('Transferencia','Transferencia'),('Efectivo','Efectivo'),('Tarjeta','Tarjeta')])
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pagado')
    def clean(self):
        if self.monto is not None and self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})
    def __str__(self):
        return f'Pago #{self.pk} · {self.membresia.socio}'

class Clase(models.Model):
    ESTADOS = [('Programada','Programada'), ('Cancelada','Cancelada')]
    entrenador = models.ForeignKey(Entrenador, on_delete=models.PROTECT)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)
    fecha = models.DateField()
    hora = models.TimeField()
    cupo_maximo = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Programada')
    class Meta:
        ordering = ['fecha', 'hora']
    @property
    def cupos_disponibles(self):
        return max(0, self.cupo_maximo - self.reserva_set.filter(estado='Confirmada').count())
    @property
    def futura(self):
        ahora = timezone.localtime()
        return self.fecha > ahora.date() or (self.fecha == ahora.date() and self.hora > ahora.time().replace(tzinfo=None))
    def consultar_disponibilidad(self):
        return self.estado == 'Programada' and self.futura and self.cupos_disponibles > 0
    def clean(self):
        if self.cupo_maximo is not None and self.cupo_maximo < 1:
            raise ValidationError({'cupo_maximo': 'La clase debe tener al menos un cupo.'})
        if self.pk and self.cupo_maximo < self.reserva_set.filter(estado='Confirmada').count():
            raise ValidationError({'cupo_maximo': 'No puedes reducir el cupo por debajo de las reservas confirmadas.'})
    def __str__(self):
        return f'{self.nombre} · {self.fecha:%d/%m/%Y} {self.hora:%H:%M}'

class Reserva(models.Model):
    ESTADOS = [('Confirmada','Confirmada'), ('Cancelada','Cancelada')]
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    fecha_reserva = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Confirmada')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['socio','clase'], name='reserva_unica_socio_clase')]
    def cancelar(self):
        self.estado = 'Cancelada'
        self.save()
    def __str__(self):
        return f'{self.socio} · {self.clase}'

class Asistencia(models.Model):
    ESTADOS = [('Presente','Presente'), ('Ausente','Ausente')]
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    entrenador = models.ForeignKey(Entrenador, on_delete=models.SET_NULL, null=True, blank=True)
    clase = models.ForeignKey(Clase, on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Presente')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['socio','clase'], name='asistencia_unica_socio_clase')]
    def __str__(self):
        return f'{self.socio} · {self.fecha}'
