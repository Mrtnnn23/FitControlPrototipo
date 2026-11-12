

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Membresia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_plan', models.CharField(choices=[('Mensual', 'Mensual'), ('Semestral', 'Semestral'), ('Anual', 'Anual')], max_length=20)),
                ('precio', models.PositiveIntegerField()),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('estado', models.CharField(choices=[('Activa', 'Activa'), ('Vencida', 'Vencida'), ('Cancelada', 'Cancelada')], default='Activa', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Socio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('rut', models.CharField(max_length=12, unique=True)),
                ('correo', models.EmailField(max_length=50)),
                ('telefono', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Entrenador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('rut', models.CharField(max_length=12, unique=True)),
                ('correo', models.CharField(max_length=50)),
                ('telefono', models.CharField(max_length=15)),
                ('especialidad', models.CharField(max_length=50)),
                ('usuario', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Clase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('descripcion', models.CharField(blank=True, max_length=200)),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
                ('cupo_maximo', models.PositiveIntegerField()),
                ('estado', models.CharField(choices=[('Programada', 'Programada'), ('Cancelada', 'Cancelada')], default='Programada', max_length=20)),
                ('entrenador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gimnasio.entrenador')),
            ],
        ),
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monto', models.PositiveIntegerField()),
                ('fecha_pago', models.DateField()),
                ('metodo_pago', models.CharField(max_length=30)),
                ('estado', models.CharField(choices=[('Pendiente', 'Pendiente'), ('Pagado', 'Pagado')], default='Pagado', max_length=20)),
                ('membresia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gimnasio.membresia')),
            ],
        ),
        migrations.CreateModel(
            name='Reserva',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_reserva', models.DateField(auto_now_add=True)),
                ('estado', models.CharField(choices=[('Confirmada', 'Confirmada'), ('Cancelada', 'Cancelada')], default='Confirmada', max_length=20)),
                ('clase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gimnasio.clase')),
                ('socio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gimnasio.socio')),
            ],
        ),
        migrations.AddField(
            model_name='membresia',
            name='socio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gimnasio.socio'),
        ),
        migrations.CreateModel(
            name='Asistencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('hora_entrada', models.TimeField()),
                ('estado', models.CharField(choices=[('Presente', 'Presente'), ('Ausente', 'Ausente')], default='Presente', max_length=20)),
                ('entrenador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gimnasio.entrenador')),
                ('socio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gimnasio.socio')),
            ],
        ),
    ]
