from django.db import migrations, models


def mpestoque_para_controla(apps, schema_editor):
    Item = apps.get_model('cadastros', 'Item')
    Item.objects.filter(mpestoque='S').update(controla_estoque=True)


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0003_empresa_cadastros'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='controla_estoque',
            field=models.BooleanField(default=False, verbose_name='Controla Estoque'),
        ),
        migrations.RunPython(mpestoque_para_controla, migrations.RunPython.noop),
    ]
