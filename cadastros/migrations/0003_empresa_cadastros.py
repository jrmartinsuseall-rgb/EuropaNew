from django.db import migrations, models
import django.db.models.deletion


def alocar_empresa(apps, schema_editor):
    Empresa = apps.get_model('core', 'Empresa')
    empresa = Empresa.objects.first()
    if not empresa:
        return

    for model_name in ('Grupo', 'Item', 'Portador', 'Metodo', 'CondicaoPagamento'):
        Model = apps.get_model('cadastros', model_name)
        Model.objects.filter(empresa__isnull=True).update(empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0002_valorreferencia'),
        ('core', '0006_empresa_perfilusuario_projeto'),
    ]

    operations = [
        migrations.AddField(
            model_name='grupo',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.AddField(
            model_name='portador',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.AddField(
            model_name='metodo',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.AddField(
            model_name='condicaopagamento',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.RunPython(alocar_empresa, migrations.RunPython.noop),
    ]
