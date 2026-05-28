# API de Integração — Módulo Campo

**Europa Serviços · EuropaNew**  
**Versão:** 1.0  
**Base URL:** `https://seu-dominio.com.br`

---

## Visão Geral

A API Campo permite que sistemas externos criem ordens de serviço na fila de execução dos técnicos em campo. Cada serviço criado fica imediatamente disponível no aplicativo mobile do técnico e no painel de monitoramento do gestor.

---

## Autenticação

Todas as requisições exigem um token estático no cabeçalho `Authorization`:

```
Authorization: Token {SEU_TOKEN}
```

O token é fornecido pela Europa Serviços no momento da parceria e configurado no ambiente do servidor.

> **Atenção:** O token deve ser mantido em sigilo. Em caso de comprometimento, entre em contato para rotacionamento.

---

## Endpoints

### `POST /campo/api/roteiro/confirmar/`

Cria um conjunto de serviços de campo a partir de um roteiro externo.

Para cada item em `servicos`, o sistema cria:
- Um registro de serviço (`Servico`) com status **AGENDADO**
- Os técnicos vinculados (`ServTecnico`)
- Os materiais previstos (`ServMaterial`)
- O evento inicial na linha do tempo (`ServTempo`)

---

## Requisição

**Content-Type:** `application/json`

### Estrutura do Payload

```json
{
  "roteiro_id": 101,
  "os_codigo": "OS-2026-0042",
  "tecnicos": [
    {
      "id": 15,
      "nome": "João Silva",
      "papel": "RESPONSAVEL"
    },
    {
      "id": 22,
      "nome": "Carlos Souza",
      "papel": "APOIO"
    }
  ],
  "servicos": [
    {
      "tipo_atividade": "Instalação de equipamento",
      "cliente_id": 308,
      "cliente_nome": "Empresa ABC Ltda",
      "local": "Rua das Flores, 100 — Centro, São Paulo",
      "ativo": "Compressor modelo XR-200",
      "descricao": "Instalar e testar compressor conforme manual técnico.",
      "data_prevista": "2026-06-10",
      "materiais": [
        {
          "item_id": 47,
          "item_codigo": "CMP-XR200",
          "item_descricao": "Compressor XR-200",
          "quantidade": 1
        },
        {
          "item_id": 88,
          "item_codigo": "MNG-12",
          "item_descricao": "Mangueira 1/2\" — 5m",
          "quantidade": 2
        }
      ]
    }
  ]
}
```

---

### Campos do Payload

#### Raiz

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `roteiro_id` | inteiro | Não | ID do roteiro no sistema de origem. Usado para rastreabilidade. |
| `os_codigo` | string | Não | Código da OS no sistema de origem. |
| `tecnicos` | lista | Não | Técnicos que executarão **todos** os serviços do payload. |
| `servicos` | lista | **Sim** | Lista de serviços a criar. Mínimo 1 item. |

#### `tecnicos[i]`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `id` | inteiro | **Sim** | ID do técnico no sistema de origem. |
| `nome` | string | **Sim** | Nome completo do técnico. |
| `papel` | string | Não | `"RESPONSAVEL"` ou `"APOIO"`. Default: `"APOIO"`. |

#### `servicos[i]`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `tipo_atividade` | string | **Sim** | Descrição curta da atividade (máx. 100 caracteres). |
| `cliente_id` | inteiro | Não | ID do cliente no sistema de origem. |
| `cliente_nome` | string | Não | Nome do cliente para exibição. |
| `local` | string | Não | Endereço de execução do serviço. |
| `ativo` | string | Não | Equipamento ou ativo alvo do serviço. |
| `descricao` | string | Não | Descrição detalhada da atividade. |
| `data_prevista` | string | Não | Data prevista de execução no formato `YYYY-MM-DD`. |
| `materiais` | lista | Não | Lista de materiais necessários. |

#### `servicos[i].materiais[j]`

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `item_descricao` | string | **Sim** | Descrição do item/material. |
| `quantidade` | número | **Sim** | Quantidade prevista. Aceita decimal (ex: `1.5`). |
| `item_id` | inteiro | Não | ID do item no catálogo interno. |
| `item_codigo` | string | Não | Código do item no sistema de origem. |

---

## Respostas

### `200 OK` — Sucesso

```json
{
  "status": "ok",
  "servicos_criados": 2,
  "ids": [145, 146]
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | string | `"ok"` |
| `servicos_criados` | inteiro | Quantidade de serviços criados. |
| `ids` | lista de inteiros | IDs dos serviços criados no sistema Europa. |

---

### `400 Bad Request` — Payload inválido

```json
{
  "status": "erro",
  "detalhe": "Campo obrigatório ausente: 'tipo_atividade' em servicos[0]"
}
```

Causas comuns:

| Mensagem | Causa |
|---|---|
| `'servicos' deve ser uma lista não vazia.` | Campo `servicos` ausente ou vazio. |
| `Campo obrigatório ausente: 'tipo_atividade'` | `tipo_atividade` não informado em algum serviço. |
| `Campo obrigatório ausente: 'item_descricao'` | `item_descricao` não informado em algum material. |
| `Campo obrigatório ausente: 'quantidade'` | `quantidade` não informada em algum material. |
| `data_prevista deve ser YYYY-MM-DD` | Formato de data inválido. |
| `JSON inválido.` | Body da requisição não é um JSON válido. |

---

### `401 Unauthorized` — Token inválido

```json
{
  "status": "erro",
  "detalhe": "Token inválido ou ausente."
}
```

---

### `500 Internal Server Error` — Erro interno

```json
{
  "status": "erro",
  "detalhe": "Erro interno: <mensagem>"
}
```

Em caso de erro 500, entre em contato com o suporte informando o payload enviado e o horário da requisição.

---

## Exemplo Completo

### Requisição

```http
POST /campo/api/roteiro/confirmar/ HTTP/1.1
Host: seu-dominio.com.br
Authorization: Token europa-campo-prod
Content-Type: application/json

{
  "roteiro_id": 55,
  "os_codigo": "OS-9901",
  "tecnicos": [
    { "id": 12, "nome": "Ana Ferreira", "papel": "RESPONSAVEL" }
  ],
  "servicos": [
    {
      "tipo_atividade": "Manutenção preventiva",
      "cliente_id": 200,
      "cliente_nome": "Indústria Beta S.A.",
      "local": "Av. Industrial, 500 — Distrito Industrial, Campinas/SP",
      "ativo": "Esteira transportadora #3",
      "descricao": "Lubrificação e verificação de rolamentos conforme plano de manutenção.",
      "data_prevista": "2026-06-15",
      "materiais": [
        {
          "item_id": 33,
          "item_codigo": "LUB-G2",
          "item_descricao": "Graxa G2 — 500g",
          "quantidade": 3
        }
      ]
    }
  ]
}
```

### Resposta

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok",
  "servicos_criados": 1,
  "ids": [178]
}
```

---

## Notas de Integração

- **Atomicidade:** A criação é atômica — se qualquer serviço do payload falhar, nenhum é criado.
- **Idempotência:** A API não verifica duplicidade. Envios repetidos com o mesmo payload criarão múltiplos registros. Controle de idempotência deve ser feito pelo sistema chamador via `roteiro_id`.
- **Técnicos:** Os técnicos listados em `tecnicos` são vinculados a **todos** os serviços do payload. Para técnicos diferentes por serviço, envie um payload por serviço.
- **Materiais:** `item_id` e `item_codigo` são campos de referência opcional para rastreabilidade. Apenas `item_descricao` e `quantidade` são obrigatórios.
- **Status inicial:** Todo serviço criado pela API inicia com status `AGENDADO`.

---

## Suporte

Para obtenção de token, dúvidas técnicas ou reporte de erros:

**Europa Serviços**  
E-mail: `suporte@europaservicos.com.br`
