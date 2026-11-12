from datetime import timedelta, time
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .forms import SocioForm, perfil_form
from .models import Socio, Entrenador, Membresia, Clase, Reserva, Pago, Asistencia
from .services import reservar

class FlujosFitControl(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hoy = timezone.localdate()
        cls.admin = User.objects.create_user('admin', email='admin@fitcontrol.test', password='PruebaSegura2026!', is_staff=True)
        cls.user = User.objects.create_user('socio', email='socio@fitcontrol.test', password='PruebaSegura2026!')
        cls.otro_user = User.objects.create_user('otro', email='otro@fitcontrol.test', password='PruebaSegura2026!')
        cls.trainer_user = User.objects.create_user('trainer', email='trainer@fitcontrol.test', password='PruebaSegura2026!')
        cls.socio = Socio.objects.create(usuario=cls.user, nombre='Ana Soto', rut='123456785',correo=cls.user.email,telefono='912345678')
        cls.otro = Socio.objects.create(usuario=cls.otro_user, nombre='Luis Paz', rut='111111111',correo=cls.otro_user.email,telefono='912345679')
        cls.trainer = Entrenador.objects.create(usuario=cls.trainer_user,nombre='Diego Ríos',rut='222222222',correo=cls.trainer_user.email,telefono='912345670',especialidad='Fuerza')
        cls.m = Membresia.objects.create(socio=cls.socio,tipo_plan='Mensual',precio=35000,fecha_inicio=cls.hoy-timedelta(days=2),fecha_fin=cls.hoy+timedelta(days=30))
        cls.clase = Clase.objects.create(entrenador=cls.trainer,nombre='Fuerza funcional',fecha=cls.hoy+timedelta(days=1),hora=time(18),cupo_maximo=1)
        Pago.objects.create(membresia=cls.m,monto=35000,fecha_pago=cls.hoy,metodo_pago='Transferencia')

    def test_login_por_correo(self):
        response = self.client.post(reverse('login'),{'username':self.user.email.upper(),'password':'PruebaSegura2026!'})
        self.assertRedirects(response,reverse('inicio'))

    def test_paginas_admin_renderizan(self):
        self.client.force_login(self.admin)
        urls = [reverse('inicio'),reverse('clases'),reverse('clase',args=[self.clase.pk]),reverse('reservas'),reverse('asistencias')]
        for tipo in ['socios','entrenadores','membresias','pagos']:
            urls += [reverse('registros',args=[tipo]),reverse('nuevo',args=[tipo])]
        for tipo in ['socios','membresias','pagos','asistencias']:
            urls += [reverse('reportes')+'?tipo='+tipo]
        for url in urls:
            with self.subTest(url=url): self.assertEqual(self.client.get(url).status_code,200)

    def test_paginas_socio_renderizan(self):
        self.client.force_login(self.user)
        for name in ['inicio','clases','reservas','mi_membresia','perfil']:
            with self.subTest(name=name): self.assertEqual(self.client.get(reverse(name)).status_code,200)

    def test_paginas_entrenador_renderizan(self):
        self.client.force_login(self.trainer_user)
        for name in ['inicio','clases','perfil']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200)

    def test_rutas_admin_bloqueadas_para_socio(self):
        self.client.force_login(self.user)
        for url in [reverse('registros',args=['socios']),reverse('nuevo',args=['clases']),reverse('reportes'),reverse('asistencias')]:
            self.assertEqual(self.client.get(url).status_code,403)

    def test_anonimo_necesita_login(self):
        self.assertEqual(self.client.get(reverse('inicio')).status_code,302)

    def test_membresia_futura_no_es_vigente(self):
        self.m.fecha_inicio = self.hoy+timedelta(days=2)
        self.assertFalse(self.m.verificar_vigencia())

    def test_fechas_invertidas_rechazadas(self):
        self.m.fecha_fin = self.m.fecha_inicio-timedelta(days=1)
        with self.assertRaises(ValidationError): self.m.full_clean()

    def test_reserva_actualiza_disponibilidad(self):
        reservar(self.socio,self.clase.pk)
        self.assertEqual(self.clase.cupos_disponibles,0)

    def test_reserva_sin_membresia_rechazada(self):
        with self.assertRaises(ValidationError): reservar(self.otro,self.clase.pk)

    def test_reserva_duplicada_rechazada(self):
        reservar(self.socio,self.clase.pk)
        with self.assertRaises(ValidationError): reservar(self.socio,self.clase.pk)
        self.assertEqual(Reserva.objects.count(),1)

    def test_sobrecupo_rechazado(self):
        reservar(self.socio,self.clase.pk)
        Membresia.objects.create(socio=self.otro,tipo_plan='Mensual',precio=30000,fecha_inicio=self.hoy,fecha_fin=self.hoy+timedelta(days=30))
        with self.assertRaises(ValidationError): reservar(self.otro,self.clase.pk)

    def test_cancelacion_libera_cupo_y_permite_reservar_otra_vez(self):
        reserva = reservar(self.socio,self.clase.pk)
        self.client.force_login(self.user)
        self.client.post(reverse('cancelar_reserva',args=[reserva.pk]))
        self.assertEqual(self.clase.cupos_disponibles,1)
        reservar(self.socio,self.clase.pk)
        self.assertEqual(Reserva.objects.count(),1)

    def test_socio_no_cancela_reserva_ajena(self):
        reserva = reservar(self.socio,self.clase.pk)
        self.client.force_login(self.otro_user)
        self.assertEqual(self.client.post(reverse('cancelar_reserva',args=[reserva.pk])).status_code,403)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado,'Confirmada')

    def test_admin_cancela_clase_y_reservas(self):
        reserva = reservar(self.socio,self.clase.pk)
        self.client.force_login(self.admin)
        self.client.post(reverse('cancelar_clase',args=[self.clase.pk]))
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado,'Cancelada')

    def test_ingreso_verifica_vigencia_y_evitar_duplicado(self):
        self.client.force_login(self.admin)
        for _ in range(2): self.client.post(reverse('asistencias'),{'identificador':'12.345.678-5'})
        self.assertEqual(Asistencia.objects.filter(socio=self.socio).count(),1)
        self.client.post(reverse('asistencias'),{'identificador':self.otro.rut})
        self.assertFalse(Asistencia.objects.filter(socio=self.otro).exists())

    def test_entrenador_registra_solo_sus_clases(self):
        reservar(self.socio,self.clase.pk)
        self.clase.fecha=self.hoy
        self.clase.save()
        self.client.force_login(self.trainer_user)
        response=self.client.post(reverse('asistencia_clase',args=[self.clase.pk]),{'presentes':[self.socio.pk]})
        self.assertEqual(response.status_code,302)
        self.assertTrue(Asistencia.objects.filter(clase=self.clase,socio=self.socio,estado='Presente').exists())
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('asistencia_clase',args=[self.clase.pk])).status_code,403)

    def test_entrenador_no_ve_clase_ajena(self):
        otra = Entrenador.objects.create(nombre='Otra',rut='333333333',correo='otra@fitcontrol.test',telefono='912345678',especialidad='Yoga')
        self.clase.entrenador=otra
        self.clase.save()
        self.client.force_login(self.trainer_user)
        self.assertEqual(self.client.get(reverse('clase',args=[self.clase.pk])).status_code,403)

    def test_perfil_actualiza_correo_de_login(self):
        self.client.force_login(self.user)
        self.client.post(reverse('perfil'),{'nombre':'Ana Nueva','correo':'nueva@fitcontrol.test','telefono':'912345678'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email,'nueva@fitcontrol.test')

    def test_perfil_rechaza_correo_ajeno(self):
        form = perfil_form(Socio)(data={'nombre':'Ana','correo':self.otro.correo,'telefono':'912345678'},instance=self.socio)
        self.assertFalse(form.is_valid())

    def test_rut_invalido_rechazado(self):
        form=SocioForm(data={'nombre':'Nueva','rut':'12345678-0','correo':'nueva@fitcontrol.test','telefono':'912345678','clave':'ClaveRobusta2026!'})
        self.assertFalse(form.is_valid())
        self.assertIn('rut',form.errors)

    def test_registro_crea_cuenta_con_clave_cifrada(self):
        form=SocioForm(data={'nombre':'Nuevo Socio','rut':'11.111.111-1','correo':'nuevo@fitcontrol.test','telefono':'912345678','clave':'ClaveRobusta2026!'})

        form.data={**form.data,'rut':'9.876.543-3'}
        self.assertTrue(form.is_valid(),form.errors)
        socio=form.save()
        self.assertTrue(socio.usuario.check_password('ClaveRobusta2026!'))
        self.assertEqual(socio.rut,'98765433')

    def test_reporte_filtra_periodo_y_exporta(self):
        self.client.force_login(self.admin)
        response=self.client.get(reverse('reportes'),{'tipo':'pagos','desde':str(self.hoy),'hasta':str(self.hoy),'exportar':'csv'})
        self.assertContains(response,'35000')
        self.assertIn('attachment',response['Content-Disposition'])
        response=self.client.get(reverse('reportes'),{'tipo':'pagos','desde':str(self.hoy+timedelta(days=1)),'exportar':'csv'})
        self.assertNotContains(response,'35000')

    def test_csrf_exigido(self):
        from django.test import Client
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('reservas'),{'clase':self.clase.pk}).status_code,403)
