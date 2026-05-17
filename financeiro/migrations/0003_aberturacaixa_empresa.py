from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_cfgcaixa_revisao'),
        ('financeiro', '0002_contarec_status_renegociado'),
    ]

    operations = [
        migrations.AddField(
            model_name='aberturacaixa',
            name='empresa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.empresa',
                verbose_name='Empresa',
            ),
        ),
    ]
