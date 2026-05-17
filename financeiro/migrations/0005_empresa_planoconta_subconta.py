from django.db import migrations, models
import django.db.models.deletion


def alocar_empresa(apps, schema_editor):
    Empresa = apps.get_model('core', 'Empresa')
    empresa = Empresa.objects.first()
    if not empresa:
        return

    PlanoConta = apps.get_model('financeiro', 'PlanoConta')
    PlanoConta.objects.filter(empresa__isnull=True).update(empresa=empresa)

    SubConta = apps.get_model('financeiro', 'SubConta')
    SubConta.objects.filter(empresa__isnull=True).update(empresa=empresa)


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0004_movcaixa_projeto'),
        ('core', '0006_empresa_perfilusuario_projeto'),
    ]

    operations = [
        migrations.AddField(
            model_name='planoconta',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.AddField(
            model_name='subconta',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa', verbose_name='Empresa',
            ),
        ),
        migrations.RunPython(alocar_empresa, migrations.RunPython.noop),
    ]
