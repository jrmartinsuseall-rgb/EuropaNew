from datetime import date


class SerializerError(Exception):
    pass


def _exige(d, campo, onde):
    if not d.get(campo):
        raise SerializerError(f"Campo obrigatório ausente: '{campo}' em {onde}")


def validar_payload(data):
    """
    Valida o payload recebido pela API de confirmação de roteiro.
    Lança SerializerError com mensagem descritiva se algo estiver errado.
    Retorna o payload limpo (sem modificações).
    """
    if not isinstance(data, dict):
        raise SerializerError("Payload deve ser um objeto JSON.")

    servicos = data.get('servicos', [])
    if not isinstance(servicos, list) or len(servicos) == 0:
        raise SerializerError("'servicos' deve ser uma lista não vazia.")

    tecnicos = data.get('tecnicos', [])
    if not isinstance(tecnicos, list):
        raise SerializerError("'tecnicos' deve ser uma lista.")

    for i, tec in enumerate(tecnicos):
        _exige(tec, 'id',   f"tecnicos[{i}]")
        _exige(tec, 'nome', f"tecnicos[{i}]")

    for i, srv in enumerate(servicos):
        _exige(srv, 'tipo_atividade', f"servicos[{i}]")

        data_prev = srv.get('data_prevista')
        if data_prev:
            try:
                date.fromisoformat(str(data_prev))
            except ValueError:
                raise SerializerError(
                    f"servicos[{i}].data_prevista deve ser YYYY-MM-DD, recebido: '{data_prev}'"
                )

        materiais = srv.get('materiais', [])
        if not isinstance(materiais, list):
            raise SerializerError(f"servicos[{i}].materiais deve ser uma lista.")

        for j, mat in enumerate(materiais):
            _exige(mat, 'item_descricao', f"servicos[{i}].materiais[{j}]")
            if mat.get('quantidade') is None:
                raise SerializerError(
                    f"Campo obrigatório ausente: 'quantidade' em servicos[{i}].materiais[{j}]"
                )

    return data
