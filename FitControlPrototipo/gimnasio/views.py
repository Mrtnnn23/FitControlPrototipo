import csv
from datetime import date
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Socio, Entrenador, Membresia, Pago, Clase, Reserva, Asistencia, membresia_vigente
from .forms import SocioForm, EntrenadorForm, MembresiaForm, PagoForm, ClaseForm, perfil_form
from .services import reservar

def rol(user):
    if user.is_staff:
        return 'Administrador'
    if hasattr(user, 'entrenador'):
        return 'Entrenador'
    if hasattr(user, 'socio'):
        return 'Socio'
    return 'Sin perfil'

def contexto(request):
    r = rol(request.user) if request.user.is_authenticated else ''
    nombre = (request.user.first_name or request.user.username).split()[0] if request.user.is_authenticated else ''
    return {'rol': r, 'hoy': timezone.localdate(), 'nombre_corto': nombre}

def solo_admin(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden('No tienes permiso para realizar esta operación.')
        return view(request, *args, **kwargs)
    return wrapped

@login_required
def inicio(request):
    r = rol(request.user)
    today = timezone.localdate()
    ahora = timezone.localtime().time().replace(tzinfo=None)
    proximas = Q(fecha__gt=today) | Q(fecha=today,hora__gt=ahora)
    clases = Clase.objects.filter(proximas, estado='Programada').select_related('entrenador')
    if r == 'Administrador':
        stats = [('Socios registrados', Socio.objects.count(), 'Tu comunidad'),
                 ('Membresías vigentes', Membresia.objects.filter(estado='Activa',fecha_inicio__lte=today,fecha_fin__gte=today).values('socio').distinct().count(), 'Entrenando contigo'),
                 ('Ingresos del mes', '$' + format(Pago.objects.filter(estado='Pagado',fecha_pago__year=today.year,fecha_pago__month=today.month).aggregate(t=Sum('monto'))['t'] or 0, ',').replace(',','.'), 'Pagos confirmados'),
                 ('Clases de hoy', clases.filter(fecha=today).count(), 'Agenda del gimnasio')]
        actividad = Reserva.objects.select_related('socio','clase').order_by('-id')[:5]
        vencimientos = Membresia.objects.filter(estado='Activa',fecha_fin__gte=today).select_related('socio').order_by('fecha_fin')[:4]
    elif r == 'Socio':
        socio = request.user.socio
        stats = [('Mi membresía', 'Vigente' if membresia_vigente(socio) else 'Sin vigencia', 'Revisa tu plan'),
                 ('Próximas reservas', socio.reserva_set.filter(Q(clase__fecha__gt=today)|Q(clase__fecha=today,clase__hora__gt=ahora),estado='Confirmada',clase__estado='Programada').count(), 'Tu próximo desafío'),
                 ('Asistencias', socio.asistencia_set.filter(estado='Presente').count(), 'Sigue sumando movimiento')]
        actividad = socio.reserva_set.select_related('socio','clase').order_by('-id')[:5]
        vencimientos = []
    elif r == 'Entrenador':
        clases = clases.filter(entrenador=request.user.entrenador)
        stats = [('Clases próximas', clases.count(), 'Tu agenda'),('Clases de hoy',clases.filter(fecha=today).count(),'Acompaña a tu equipo'),('Asistencias registradas',Asistencia.objects.filter(entrenador=request.user.entrenador).count(),'Seguimiento de participantes')]
        actividad, vencimientos = [], []
    else:
        return render(request,'gimnasio/sin_perfil.html',status=403)
    return render(request,'gimnasio/inicio.html',{'stats':stats,'clases':clases[:4],'actividad':actividad,'vencimientos':vencimientos})

REGISTROS = {
    'socios': (Socio,SocioForm,'Socios',['Nombre','RUT','Correo','Teléfono']),
    'entrenadores': (Entrenador,EntrenadorForm,'Entrenadores',['Nombre','Especialidad','Correo','Teléfono']),
    'membresias': (Membresia,MembresiaForm,'Membresías',['Socio','Plan','Inicio','Vencimiento','Estado']),
    'pagos': (Pago,PagoForm,'Pagos',['Socio','Monto','Fecha','Método','Estado']),
}

@solo_admin
def registros(request, tipo):
    if tipo not in REGISTROS:
        return HttpResponse(status=404)
    model, form, titulo, columnas = REGISTROS[tipo]
    q = request.GET.get('q','').strip()
    qs = model.objects.all().order_by('-pk')
    if tipo in ['socios','entrenadores']:
        qs = qs.filter(Q(nombre__icontains=q)|Q(rut__icontains=q)|Q(correo__icontains=q))
    elif tipo == 'membresias':
        qs = qs.select_related('socio').filter(socio__nombre__icontains=q)
    else:
        qs = qs.select_related('membresia__socio').filter(membresia__socio__nombre__icontains=q)
    filas = []
    for obj in qs[:200]:
        if tipo == 'socios': c = [obj.nombre,obj.rut,obj.correo,obj.telefono]
        elif tipo == 'entrenadores': c = [obj.nombre,obj.especialidad,obj.correo,obj.telefono]
        elif tipo == 'membresias': c = [obj.socio.nombre,obj.tipo_plan,obj.fecha_inicio,obj.fecha_fin,'Vigente' if obj.verificar_vigencia() else 'No vigente · '+obj.estado]
        else: c = [obj.membresia.socio.nombre,f'${obj.monto:,}'.replace(',','.'),obj.fecha_pago,obj.metodo_pago,obj.estado]
        filas.append((obj.pk,c))
    return render(request,'gimnasio/registros.html',{'titulo':titulo,'tipo':tipo,'columnas':columnas,'filas':filas,'q':q,'total':qs.count()})

@solo_admin
def editar(request, tipo, pk=None):
    if tipo == 'clases':
        model, formclass, titulo = Clase, ClaseForm, 'clase'
    elif tipo in REGISTROS:
        model, formclass, titulo, _ = REGISTROS[tipo]
    else:
        return HttpResponse(status=404)
    obj = get_object_or_404(model,pk=pk) if pk else None
    initial = {}
    if tipo == 'membresias' and obj and request.GET.get('renovar') == '1':
        initial = {'socio':obj.socio_id,'tipo_plan':obj.tipo_plan,'precio':obj.precio,'fecha_inicio':timezone.localdate(),'estado':'Activa'}
        obj = None
    form = formclass(request.POST if request.method == 'POST' else None,instance=obj,initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                if tipo == 'clases' and obj:
                    Clase.objects.select_for_update().get(pk=obj.pk)
                    form.instance.clean()
                saved = form.save()
                if tipo == 'clases' and saved.estado == 'Cancelada':
                    saved.reserva_set.filter(estado='Confirmada').update(estado='Cancelada')
        except ValidationError as exc:
            form.add_error(None, ' '.join(exc.messages))
        else:
            messages.success(request,'Cambios guardados correctamente.')
            return redirect('clases' if tipo == 'clases' else 'registros', **({} if tipo == 'clases' else {'tipo':tipo}))
    return render(request,'gimnasio/form.html',{'form':form,'titulo':('Editar ' if obj else 'Registrar ') + titulo,'subtitulo':'Completa los datos. La información se valida antes de guardarse.'})

@login_required
def clases(request):
    qs = Clase.objects.select_related('entrenador').all()
    if rol(request.user) == 'Entrenador': qs = qs.filter(entrenador=request.user.entrenador)
    elif rol(request.user) not in ['Administrador','Socio']: return HttpResponseForbidden()
    q = request.GET.get('q','')
    qs = qs.filter(nombre__icontains=q)
    if request.GET.get('agenda') != 'todas': qs = qs.filter(fecha__gte=timezone.localdate())
    return render(request,'gimnasio/clases.html',{'clases':qs,'q':q})

@login_required
def clase_detalle(request, pk):
    clase = get_object_or_404(Clase.objects.select_related('entrenador'),pk=pk)
    r = rol(request.user)
    if r == 'Entrenador' and clase.entrenador.usuario_id != request.user.pk: return HttpResponseForbidden()
    if r not in ['Administrador','Entrenador','Socio']: return HttpResponseForbidden()
    reservas = clase.reserva_set.filter(estado='Confirmada').select_related('socio') if r != 'Socio' else []
    presentes = list(clase.asistencia_set.filter(estado='Presente').values_list('socio_id',flat=True)) if r != 'Socio' else []
    return render(request,'gimnasio/clase.html',{'clase':clase,'reservas':reservas,'presentes':presentes})

@login_required
def reservas(request):
    r = rol(request.user)
    qs = Reserva.objects.select_related('clase','socio').order_by('-clase__fecha','-clase__hora')
    if r == 'Socio': qs = qs.filter(socio=request.user.socio)
    elif r != 'Administrador': return HttpResponseForbidden()
    if request.method == 'POST':
        socio = request.user.socio if r == 'Socio' else get_object_or_404(Socio,pk=request.POST.get('socio'))
        clase = get_object_or_404(Clase,pk=request.POST.get('clase'))
        try:
            reservar(socio,clase.pk)
            messages.success(request,'Reserva confirmada. ¡Nos vemos en clase!')
        except ValidationError as exc:
            messages.warning(request,' '.join(exc.messages))
        return redirect('reservas')
    return render(request,'gimnasio/reservas.html',{'reservas':qs,'socios':Socio.objects.all() if r=='Administrador' else [],'clases':Clase.objects.filter(estado='Programada',fecha__gte=timezone.localdate())})

@login_required
@require_POST
def cancelar_reserva(request, pk):
    reserva = get_object_or_404(Reserva.objects.select_related('clase','socio'),pk=pk)
    if not request.user.is_staff and reserva.socio.usuario_id != request.user.pk: return HttpResponseForbidden()
    with transaction.atomic():
        Clase.objects.select_for_update().get(pk=reserva.clase_id)
        if reserva.clase.futura and reserva.estado == 'Confirmada':
            reserva.cancelar()
            messages.success(request,'Reserva cancelada. El cupo quedó disponible.')
        else: messages.warning(request,'Solo se pueden cancelar reservas confirmadas de clases futuras.')
    return redirect('reservas')

@solo_admin
@require_POST
def cancelar_clase(request, pk):
    with transaction.atomic():
        clase = get_object_or_404(Clase.objects.select_for_update(),pk=pk)
        clase.estado = 'Cancelada'
        clase.save(update_fields=['estado'])
        clase.reserva_set.filter(estado='Confirmada').update(estado='Cancelada')
    messages.success(request,'Clase cancelada y reservas actualizadas.')
    return redirect('clases')

@login_required
@require_POST
def asistencia_clase(request, pk):
    clase = get_object_or_404(Clase,pk=pk)
    if not request.user.is_staff and not (rol(request.user)=='Entrenador' and clase.entrenador.usuario_id==request.user.pk): return HttpResponseForbidden()
    if clase.estado != 'Programada' or clase.fecha > timezone.localdate():
        messages.warning(request,'La asistencia se registra el día de la clase o después, en clases no canceladas.')
        return redirect('clase',pk=pk)
    presentes = set(request.POST.getlist('presentes'))
    with transaction.atomic():
        for reserva in clase.reserva_set.filter(estado='Confirmada'):
            Asistencia.objects.update_or_create(socio=reserva.socio,clase=clase,defaults={'entrenador':clase.entrenador,'fecha':clase.fecha,'hora_entrada':clase.hora,'estado':'Presente' if str(reserva.socio_id) in presentes else 'Ausente'})
    messages.success(request,'Asistencia de la clase guardada.')
    return redirect('clase',pk=pk)

@solo_admin
def asistencias(request):
    if request.method == 'POST':
        identificador = request.POST.get('identificador','').replace('.','').replace('-','').upper().strip()
        socio = Socio.objects.filter(rut=identificador).first()
        if not socio and identificador.isdigit(): socio = Socio.objects.filter(pk=identificador).first()
        if not socio: messages.warning(request,'No encontramos un socio con ese RUT o identificador.')
        elif not membresia_vigente(socio): messages.warning(request,'El socio no tiene una membresía vigente.')
        elif Asistencia.objects.filter(socio=socio,clase__isnull=True,fecha=timezone.localdate()).exists(): messages.warning(request,'El ingreso de hoy ya está registrado.')
        else:
            ahora = timezone.localtime()
            Asistencia.objects.create(socio=socio,fecha=ahora.date(),hora_entrada=ahora.time().replace(tzinfo=None))
            messages.success(request,f'Ingreso registrado: {socio.nombre}.')
        return redirect('asistencias')
    return render(request,'gimnasio/asistencias.html',{'asistencias':Asistencia.objects.select_related('socio','clase').order_by('-fecha','-hora_entrada')[:100]})

@login_required
def mi_membresia(request):
    if rol(request.user) != 'Socio': return HttpResponseForbidden()
    qs = request.user.socio.membresia_set.order_by('-fecha_fin')
    return render(request,'gimnasio/membresia.html',{'membresias':qs})

@login_required
def perfil(request):
    r = rol(request.user)
    if r not in ['Socio','Entrenador']: return HttpResponseForbidden()
    persona = request.user.socio if r == 'Socio' else request.user.entrenador
    form = perfil_form(type(persona))(request.POST if request.method=='POST' else None,instance=persona)
    if request.method=='POST' and form.is_valid():
        form.save()
        messages.success(request,'Perfil actualizado. Usa tu correo actualizado para iniciar sesión.')
        return redirect('perfil')
    return render(request,'gimnasio/form.html',{'form':form,'titulo':'Mi perfil','subtitulo':'Mantén tus datos de contacto al día.'})

@solo_admin
def reportes(request):
    tipo = request.GET.get('tipo','pagos')
    if tipo not in ['socios','membresias','pagos','asistencias']: tipo = 'pagos'
    inicio, fin = request.GET.get('desde',''), request.GET.get('hasta','')
    try:
        desde = date.fromisoformat(inicio) if inicio else None
        hasta = date.fromisoformat(fin) if fin else None
        if desde and hasta and desde > hasta: raise ValueError()
    except ValueError:
        messages.warning(request,'Selecciona un período válido: inicio anterior o igual al término.')
        return redirect('reportes')
    if tipo == 'socios':
        qs = Socio.objects.select_related('usuario').all()
        campo, encabezados = 'usuario__date_joined__date', ['Nombre','RUT','Correo','Teléfono']
        convertir = lambda o: [o.nombre,o.rut,o.correo,o.telefono]
    elif tipo == 'membresias':
        qs = Membresia.objects.select_related('socio').all()
        campo, encabezados = 'fecha_inicio', ['Socio','Plan','Inicio','Vencimiento','Estado']
        convertir = lambda o: [o.socio.nombre,o.tipo_plan,o.fecha_inicio,o.fecha_fin,'Vigente' if o.verificar_vigencia() else 'No vigente · '+o.estado]
    elif tipo == 'asistencias':
        qs = Asistencia.objects.select_related('socio','clase').all()
        campo, encabezados = 'fecha', ['Socio','Fecha','Hora','Actividad','Estado']
        convertir = lambda o: [o.socio.nombre,o.fecha,o.hora_entrada,o.clase.nombre if o.clase else 'Ingreso al gimnasio',o.estado]
    else:
        qs = Pago.objects.select_related('membresia__socio').all()
        campo, encabezados = 'fecha_pago', ['Socio','Monto CLP','Fecha','Método','Estado']
        convertir = lambda o: [o.membresia.socio.nombre,o.monto,o.fecha_pago,o.metodo_pago,o.estado]
    if desde: qs = qs.filter(**{campo+'__gte':desde})
    if hasta: qs = qs.filter(**{campo+'__lte':hasta})
    total = qs.count()
    suma = qs.filter(estado='Pagado').aggregate(t=Sum('monto'))['t'] or 0 if tipo=='pagos' else None
    if request.GET.get('exportar') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="fitcontrol-{tipo}.csv"'
        response.write('\ufeff')
        writer = csv.writer(response,delimiter=';')
        writer.writerow(encabezados)
        for obj in qs.iterator():
            writer.writerow([("'"+str(v)) if str(v).startswith(('=','+','-','@')) else v for v in convertir(obj)])
        return response
    return render(request,'gimnasio/reportes.html',{'tipo':tipo,'desde':inicio,'hasta':fin,'columnas':encabezados,'filas':[convertir(o) for o in qs[:200]],'total':total,'suma':suma})
