from django.db import migrations, models
import django.db.models.deletion


def alocar_empresa(apps, schema_editor):
    Empresa = apps.get_model('core', 'Empresa')
    empresa = Empresa.objects.first()
    if not empresa:
        return

    PerfilUsuario = apps.get_model('core', 'PerfilUsuario')
    PerfilUsuario.objects.filter(empresa__isnull=True).update(empresa=empresa)

    Projeto = apps.get_model('core', 'Projeto')
    Projeto.objects.filter(empresa__isnull=True).update(empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_projeto_orcamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.AddField(
            model_name='projeto',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.RunPython(alocar_empresa, migrations.RunPython.noop),
    ]
