from django.urls import path
from . import views
urlpatterns = [
    path('',views.inicio,name='inicio'),
    path('gestion/<str:tipo>/',views.registros,name='registros'),
    path('gestion/<str:tipo>/nuevo/',views.editar,name='nuevo'),
    path('gestion/<str:tipo>/<int:pk>/',views.editar,name='editar'),
    path('clases/',views.clases,name='clases'),
    path('clases/<int:pk>/',views.clase_detalle,name='clase'),
    path('clases/<int:pk>/cancelar/',views.cancelar_clase,name='cancelar_clase'),
    path('clases/<int:pk>/asistencia/',views.asistencia_clase,name='asistencia_clase'),
    path('reservas/',views.reservas,name='reservas'),
    path('reservas/<int:pk>/cancelar/',views.cancelar_reserva,name='cancelar_reserva'),
    path('asistencias/',views.asistencias,name='asistencias'),
    path('mi-membresia/',views.mi_membresia,name='mi_membresia'),
    path('perfil/',views.perfil,name='perfil'),
    path('reportes/',views.reportes,name='reportes'),
]
