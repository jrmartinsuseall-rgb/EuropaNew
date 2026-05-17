from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0004_item_controla_estoque'),
        ('estoque', '0002_inventario'),
    ]

    operations = [
        # usuariolanc no cabeçalho
        migrations.AddField(
            model_name='notafiscalentrada',
            name='usuariolanc',
            field=models.CharField(blank=True, max_length=50, verbose_name='Usuário Lanç.'),
        ),
        # item FK no item da NF
        migrations.AddField(
            model_name='itemnfentrada',
            name='item',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='cadastros.item',
                verbose_name='Item',
            ),
        ),
        # descricao_item no item da NF
        migrations.AddField(
            model_name='itemnfentrada',
            name='descricao_item',
            field=models.CharField(blank=True, max_length=200, verbose_name='Descrição'),
        ),
        # nova tabela de parcelas
        migrations.CreateModel(
            name='ParcelaNFEntrada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parcela', models.IntegerField(verbose_name='Parcela')),
                ('vencimento', models.DateField(verbose_name='Vencimento')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Valor')),
                ('idcontapag', models.IntegerField(default=0, verbose_name='ID Conta Pagar')),
                ('nfentrada', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='parcelas',
                    to='estoque.notafiscalentrada',
                    verbose_name='NF Entrada',
                )),
            ],
            options={
                'verbose_name': 'Parcela da NF de Entrada',
                'verbose_name_plural': 'Parcelas da NF de Entrada',
                'db_table': 'parcnfentrada',
                'ordering': ['nfentrada', 'parcela'],
            },
        ),
    ]
