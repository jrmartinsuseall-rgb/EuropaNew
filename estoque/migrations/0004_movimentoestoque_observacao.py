from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0003_nfentrada_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimentoestoque',
            name='observacao',
            field=models.CharField(blank=True, max_length=200, verbose_name='Observação / Motivo'),
        ),
    ]
