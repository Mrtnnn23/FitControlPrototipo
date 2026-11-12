from datetime import timedelta, time
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from gimnasio.models import Socio, Entrenador, Membresia, Pago, Clase, Reserva

class Command(BaseCommand):
    help = 'Crea datos ficticios y cuentas de demostración. No usar en producción.'
    def add_arguments(self, parser):
        parser.add_argument('--password', required=True, help='Contraseña para las nuevas cuentas de demostración')

    @transaction.atomic
    def handle(self, *args, **options):
        from django.contrib.auth.password_validation import validate_password
        validate_password(options['password'])
        hoy=timezone.localdate()
        def cuenta(alias,nombre,staff=False):
            email=alias+'@fitcontrol.demo'
            user,created=User.objects.get_or_create(username='demo_'+alias,defaults={'email':email,'first_name':nombre,'is_staff':staff})
            if created:
                user.set_password(options['password'])
                user.save()
            elif user.email != email:
                raise CommandError('Existe una cuenta incompatible. No se cambió ningún dato.')
            return user
        cuenta('admin','Martín',True)
        trainer,_=Entrenador.objects.get_or_create(rut='222222222',defaults={'usuario':cuenta('entrenador','Diego Ríos'),'nombre':'Diego Ríos','correo':'entrenador@fitcontrol.demo','telefono':'+56987654321','especialidad':'Fuerza y acondicionamiento'})
        socios=[]
        nombres=['Sofía Torres','Matías Fuentes','Valentina Pérez','Benjamín Soto','Catalina Rojas','Tomás Díaz','Antonia Silva','Vicente Muñoz']
        for i,nombre in enumerate(nombres):
            numero=str(14000000+i)
            suma=sum(int(n)*(2+j%6) for j,n in enumerate(reversed(numero)))
            d=11-suma%11
            rut=numero+('0' if d==11 else 'K' if d==10 else str(d))
            user=cuenta('socio' if i==0 else f'socio{i+1}',nombre)
            socio,_=Socio.objects.get_or_create(rut=rut,defaults={'usuario':user,'nombre':nombre,'correo':user.email,'telefono':f'9123456{i:02}'})
            socios.append(socio)
            m,_=Membresia.objects.get_or_create(socio=socio,tipo_plan='Mensual',defaults={'precio':35000,'fecha_inicio':hoy-timedelta(days=12),'fecha_fin':hoy+timedelta(days=18+i)})
            Pago.objects.get_or_create(membresia=m,fecha_pago=hoy-timedelta(days=i),defaults={'monto':35000,'metodo_pago':'Transferencia'})
        sesiones=[('Fuerza funcional','Construye fuerza para tu día a día.',8,0),('Movilidad & core','Recupera tu equilibrio y muévete mejor.',10,0),('Entrenamiento HIIT','Energía en equipo. Supera tu siguiente desafío.',18,1),('Full body','Una sesión completa para seguir avanzando.',19,1),('Fuerza funcional','Técnica, progresión y trabajo en comunidad.',9,2),('Movilidad & core','Un momento para conectar con tu cuerpo.',11,3)]
        for i,(nombre,descripcion,hora,delta) in enumerate(sesiones):
            clase,_=Clase.objects.get_or_create(nombre=nombre,fecha=hoy+timedelta(days=delta),hora=time(hora),defaults={'entrenador':trainer,'descripcion':descripcion,'cupo_maximo':12})
            for socio in socios[:3+i%4]:
                Reserva.objects.get_or_create(socio=socio,clase=clase)
        self.stdout.write(self.style.SUCCESS('Demo lista. Cuentas: admin@fitcontrol.demo / socio@fitcontrol.demo / entrenador@fitcontrol.demo. Usa la contraseña que indicaste. Las cuentas existentes conservan su contraseña.'))
