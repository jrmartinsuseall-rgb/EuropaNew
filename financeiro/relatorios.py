from django.template.loader import render_to_string
from django.http import HttpResponse


def render_pdf(template_name, context, filename='relatorio.pdf', request=None):
    """
    Renderiza um template Django como PDF via WeasyPrint.
    Import lazy — WeasyPrint e GTK só são carregados ao gerar o PDF.
    """
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    html_string = render_to_string(template_name, context, request=request)
    base_url = request.build_absolute_uri('/') if request else None
    font_config = FontConfiguration()
    pdf = HTML(string=html_string, base_url=base_url).write_pdf(
        font_config=font_config,
    )
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
