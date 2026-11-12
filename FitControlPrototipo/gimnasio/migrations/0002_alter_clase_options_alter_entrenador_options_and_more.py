

import django.db.models.deletion
import gimnasio.models
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('gimnasio', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clase',
            options={'ordering': ['fecha', 'hora']},
        ),
        migrations.AlterModelOptions(
            name='entrenador',
            options={'verbose_name_plural': 'Entrenadores'},
        ),
        migrations.AddField(
            model_name='asistencia',
            name='clase',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='gimnasio.clase'),
        ),
        migrations.AddField(
            model_name='socio',
            name='usuario',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='clase',
            name='entrenador',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gimnasio.entrenador'),
        ),
        migrations.AlterField(
            model_name='entrenador',
            name='correo',
            field=models.EmailField(max_length=50),
        ),
        migrations.AlterField(
            model_name='entrenador',
            name='rut',
            field=models.CharField(max_length=12, unique=True, validators=[gimnasio.models.validar_rut]),
        ),
        migrations.AlterField(
            model_name='pago',
            name='metodo_pago',
            field=models.CharField(choices=[('Transferencia', 'Transferencia'), ('Efectivo', 'Efectivo'), ('Tarjeta', 'Tarjeta')], max_length=30),
        ),
        migrations.AlterField(
            model_name='socio',
            name='rut',
            field=models.CharField(max_length=12, unique=True, validators=[gimnasio.models.validar_rut]),
        ),
        migrations.AddConstraint(
            model_name='asistencia',
            constraint=models.UniqueConstraint(fields=('socio', 'clase'), name='asistencia_unica_socio_clase'),
        ),
        migrations.AddConstraint(
            model_name='reserva',
            constraint=models.UniqueConstraint(fields=('socio', 'clase'), name='reserva_unica_socio_clase'),
        ),
    ]
