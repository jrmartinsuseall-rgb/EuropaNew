# Europa Python — Diário de Migração

**Projeto:** Migração EuropaNew VDF → Django + PostgreSQL + WeasyPrint
**Origem:** `C:\Jrmartins\D\EuropaNew` (Visual DataFlex)
**Destino:** `C:\Jrmartins\D\NewEuropaPython` (Python + Django)
**Última atualização:** 2026-05-11 (sessão 8)

---

## Stack Definida

| Componente      | Versão  | Função                      |
|-----------------|---------|-----------------------------|
| Python          | 3.12.10 | Runtime                     |
| Django          | 6.0.4   | Framework web               |
| PostgreSQL      | 18      | Banco de dados              |
| psycopg2        | 2.9.11  | Driver PostgreSQL            |
| WeasyPrint      | 68.1    | Geração de PDF / Espelhos   |
| python-decouple | 3.8     | Variáveis de ambiente       |
| Pillow          | 12.2.0  | Processamento de imagens    |
| Alpine.js       | 3.14.1  | Reatividade frontend        |
| HTMX            | 1.9.12  | Requisições parciais HTML   |
| Bootstrap       | 5.3.3   | Layout e componentes        |
| IMask           | 7.6.1   | Máscaras de campo           |

---

## Fase 1 — Estrutura Base ✅
- [x] Projeto Django criado, venv, dependências, settings, .env, .gitignore

## Fase 2 — Banco de Dados ✅
- [x] PostgreSQL 18, banco `europa_db`, migrations iniciais, superusuário

## Fase 3 — Apps Django (Models) ✅
- [x] 6 apps: `core`, `cadastros`, `estoque`, `financeiro`, `vendas`, `servicos`
- [x] 49 tabelas mapeadas + novos campos de evolução OS
- [x] `python manage.py check` — **0 erros**

## Fase 4 — Interface Web ✅
- [x] `base.html` — sidebar colapsável (Alpine.js + localStorage), topbar, breadcrumb
- [x] `static/css/europa.css` + `static/js/europa.js` — máscaras IMask, UX VDF
- [x] Stack frontend: HTMX 1.9.12 + Alpine.js 3.14.1 + Bootstrap 5.3.3 + IMask 7.6.1

## Fase 5 — Controle de Acesso ✅
- [x] `@modulo_required` decorator, PerfilUsuario, login/logout, troca de senha
- [x] Sidebar condicional por permissão, sessão multi-empresa

---

## Fase 6 — Módulos Implementados

### Módulo Cadastros ✅

| Funcionalidade | Status |
|---|---|
| Clientes / Fornecedores — CRUD completo | ✅ |
| Formulário 6 abas Alpine.js (PF/PJ adaptativo) | ✅ |
| Busca HTMX em tempo real, inativar/reativar | ✅ |
| Lookup de cidade inline (Alpine v3 compatível) | ✅ |
| Itens — CRUD + busca HTMX + campo `tipo_item` (S/P/M) | ✅ |
| Grupos — CRUD hierárquico | ✅ |
| Condições de Pagamento — CRUD | ✅ |
| Portadores — CRUD | ✅ |
| Métodos de Pagamento — CRUD | ✅ |
| Tabelas de Preço — CRUD | ✅ |

**Correção sessão 6:** `selecionarCidade()` usava API interna Alpine v2 (`_x_dataStack`).
Corrigido para Alpine v3: `comp.dispatchEvent(new Event('input'))`.
`autocomplete="nope"` usado para desabilitar sugestão do Chrome em campos com lookup.

### Módulo Configurações (core) ✅

| Funcionalidade | Status |
|---|---|
| Empresa — edição singleton | ✅ |
| Usuários — CRUD + permissões por módulo | ✅ |
| Bancos — CRUD | ✅ |
| Cidades — CRUD | ✅ |
| CFOP — CRUD | ✅ |
| Plano de Contas — CRUD | ✅ |
| Sub-Contas — CRUD | ✅ |
| Config. Caixa — singleton | ✅ |

### Módulo Financeiro ✅

| Funcionalidade | Status |
|---|---|
| Contas a Receber — CRUD + filtros + totalizador | ✅ |
| Contas a Pagar — CRUD | ✅ |
| Geração de Boletos — numerobanco, race-condition safe | ✅ |
| Caixa — abertura, entrada/saída, sangria, fechamento | ✅ |
| Caixa — recebimento CR + pagamento CP com método | ✅ |
| Caixa — cancelamento com contra-partida + reabertura | ✅ |

### Módulo CRM ✅

| Funcionalidade | Status |
|---|---|
| Lookup de clientes — busca adaptativa por campo | ✅ |
| Ordenação server-side HTMX | ✅ |
| Ícones de status inline (inadimplente, OS, pedido) | ✅ |
| Ficha do cliente — hub unificado | ✅ |
| Contatos / log de atendimento | ✅ |
| Histórico de compras e OS | ✅ |
| Posição financeira | ✅ |

### Módulo Estoque ✅

| Funcionalidade | Status |
|---|---|
| NF de Entrada — CRUD (cabeçalho + itens + parcelas) | ✅ |
| NF de Entrada — lançamento (gera movimento + contas a pagar) | ✅ |
| NF de Entrada — cancelamento | ✅ |
| Requisições — CRUD + atendimento parcial/total | ✅ |
| Requisições — indicadores de disponibilidade de estoque por item | ✅ |
| Ajustes de Estoque — lançamento avulso com motivo | ✅ |
| Ajustes — listagem com últimos 200 registros | ✅ |
| Inventário — *(a implementar)* | ⏳ |

### Módulo Vendas ✅

| Funcionalidade | Status |
|---|---|
| Pedidos — CRUD + listagem | ✅ |
| Pedido — fluxo: Aberto → Instalado → Faturado / Cancelado | ✅ |
| Pedido — modal Instalação (data + técnico + obs) | ✅ |
| Pedido — modal Cancelamento com motivo | ✅ |
| Pedido — faturamento (gera contas a receber) | ✅ |
| Pedido — parcelas automáticas por condição de pagamento | ✅ |

### Módulo Serviços (OS) ✅

| Funcionalidade | Status |
|---|---|
| Ordem de Serviço — CRUD completo | ✅ |
| OS — fluxo: Agendada → Pendente → Realizada → Faturada / Cancelada | ✅ |
| OS — Reagendamento com modal Alpine.js | ✅ |
| OS — Geração de Requisição de Estoque ao criar roteiro | ✅ |
| OS — Roteiros de Assistência Técnica (agrupamento de OS) | ✅ |
| OS — CRM Ficha integrada (link direto OS → Ficha cliente) | ✅ |
| **OS — Classificação de itens: Serviço / Produto / Matéria-Prima** | ✅ |
| **OS — Hierarquia 2 níveis: Serviço como agrupador de P/M** | ✅ |
| **OS — Vínculo de P/M a serviço pai no lançamento (Alpine.js)** | ✅ |
| **OS — Detalhe com exibição hierárquica (grupos + filhos indentados)** | ✅ |

---

## Fase 7 — Espelhos PDF ✅

Espelho = documento gerado a partir de **um único registro** para impressão/arquivo.
Base: `render_pdf()` em `financeiro/relatorios.py` + `templates/relatorios/base_pdf.html`.

| Espelho | Template | View |
|---|---|---|
| Ordem de Serviço | `espelhos/os.html` | `servicos:os_espelho` |
| Pedido de Venda | `espelhos/pedido.html` | `vendas:pedido_espelho` |
| NF de Entrada | `espelhos/nf.html` | `estoque:nf_espelho` |
| Requisição de Estoque | `espelhos/req.html` | `estoque:req_espelho` |
| Ajuste de Estoque | `espelhos/ajuste.html` | `estoque:ajuste_espelho` |

**Espelho OS** renderiza hierarquia (serviço em `row-servico` azul-claro, filhos com `└ `).

---

## Fase 8 — Evolução OS: Classificação e Hierarquia ✅

### Objetivo
Permitir que uma OS contenha itens classificados como Serviço, Produto ou Matéria-Prima,
com Serviços funcionando como agrupadores de P/M.

### Modelo de dados adicionado

| Campo | Tabela | Tipo | Descrição |
|---|---|---|---|
| `tipo_item` | `itens` | CharField(1) S/P/M | Classificação nasce no item |
| `tipo_item` | `itemtel` | CharField(1) | Persiste na OS para integridade histórica |
| `servico_pai` | `itemtel` | IntegerField | PK do ItemTeleVenda pai (0 = raiz) |
| `idpedido_material` | `telvenda` | IntegerField | Preparado para bifurcação de faturamento |
| `tipo_faturamento` | `pedido` | CharField(1) U/S/M | Identificação do tipo de pedido gerado |
| `tipo_item` | `itemped` | CharField(1) | Rastreabilidade do tipo no pedido |

### Fluxo de lançamento (OS Create)
- Lookup de itens retorna `tipo_item` no JSON
- Badge de tipo (info/warning/secondary) exibido nos resultados e na tabela
- Dropdown "Vincular ao serviço" aparece **somente** quando: item sendo adicionado é P/M **e** já existe ao menos um Serviço na lista
- Serviços na tabela: estilo `table-light fw-semibold`
- Filhos na tabela: prefixo `└` (indent visual)
- Submit via `itens_json` com campos `_tid`, `tipo_item`, `servico_pai_tid`
- View cria items em **dois passes** — 1º cria todos e mapeia `_tid → pk`; 2º resolve `servico_pai` via FK real

### Compatibilidade retroativa
Itens antigos com `tipo_item = ''` são tratados como "standalone" (sem grupo) e exibidos normalmente em ambos os modos (detalhe e espelho).

---

## Migrations Aplicadas

| App | Migration | Descrição |
|---|---|---|
| core | 0001_initial | Estrutura base |
| core | 0002_cfgcaixa | Config caixa |
| core | 0003_cfgcaixa_revisao | Revisão campos caixa |
| cadastros | 0001_initial | Estrutura base |
| cadastros | 0002 … 0004 | Evoluções intermediárias |
| cadastros | 0005_item_tipo_item | Novo campo `tipo_item` + `controla_estoque` |
| financeiro | 0001_initial | Estrutura base |
| financeiro | 0002_contarec_status_renegociado | Status renegociado em CR |
| financeiro | 0003_aberturacaixa_empresa | Empresa em AberturaCaixa |
| estoque | 0001_initial | Estrutura base |
| vendas | 0001_initial | Estrutura base |
| vendas | 0002_itempedido_tipo_item | `tipo_item` + `tipo_faturamento` |
| servicos | 0001_initial | Estrutura base |
| servicos | 0002_contatocliente | CRM contatos |
| servicos | 0003_televenda_campos | Campos de reagendamento/período |
| servicos | 0004_itemtelevenda_hierarquia | `tipo_item`, `servico_pai`, `idpedido_material` |

---

## Arquitetura de Templates

```
templates/
├── base.html                    — layout master (sidebar colapsável, topbar)
├── login.html
├── relatorios/
│   └── base_pdf.html            — base WeasyPrint (cabeçalho empresa, @page A4)
├── espelhos/
│   ├── os.html                  — Espelho OS (hierárquico)
│   ├── pedido.html              — Espelho Pedido
│   ├── nf.html                  — Espelho NF de Entrada
│   ├── req.html                 — Espelho Requisição
│   └── ajuste.html              — Espelho Ajuste
├── core/
│   └── (empresa, usuários, bancos, cidades, cfop, planoconta, subconta)
├── cadastros/
│   ├── cliente_list/form.html
│   ├── item_list/form.html      — badge tipo_item por item
│   ├── item_form.html           — select tipo_item na aba Dados
│   ├── grupo/condpag/portador/metodo/tabela — CRUD
│   └── partials/                — tabelas HTMX, lookup cidade, lookup item
├── financeiro/
│   └── (contarec, contapag, boletos, caixa, recebimento, pagamento, partials)
├── estoque/
│   ├── nf_list/form/detalhe.html
│   ├── req_list/detalhe.html
│   └── ajuste_list/create.html
├── vendas/
│   ├── pedido_list.html
│   └── pedido_detalhe.html      — modais Bootstrap: Instalar / Cancelar
└── servicos/
    ├── os_list.html
    ├── os_create.html           — Alpine.js hierárquico (tipo_item + vincular serviço)
    ├── os_detalhe.html          — grupos hierárquicos (serviço → filhos)
    ├── crm_lookup/ficha.html
    ├── roteiro_list/create/detalhe.html
    └── partials/
```

---

## Padrões de Desenvolvimento Estabelecidos

| Padrão | Implementação |
|---|---|
| Busca em tempo real | `hx-get` + `hx-trigger="keyup changed delay:300ms"` |
| Ordenação de tabela | `hx-get` com `?order=campo&dir=asc/desc`, server-side |
| Modais simples | Alpine.js `x-show` + `x-data` local, sem Bootstrap Modal |
| Modais Bootstrap | `data-bs-toggle="modal"` para fluxos com formulário pesado |
| Inativar/reativar | `hx-post` + `hx-swap="outerHTML"` na linha da tabela |
| Totalizadores | `qs.aggregate(Sum(...))` no view, `<tfoot>` no partial |
| Saldo acumulado | Cada `MovimentoCaixa` grava `saldo` corrente |
| Ações atômicas | `transaction.atomic()` + `select_for_update()` onde necessário |
| Campos de data | `DateInput(format='%Y-%m-%d')` — obrigatório com `LANGUAGE_CODE=pt-br` |
| Sidebar colapsável | `x-data="{open: JSON.parse(localStorage.getItem('nav_KEY') ?? 'true')}"` |
| Alpine v3 x-model update | `comp.dispatchEvent(new Event('input'))` — não usar `_x_dataStack` (v2) |
| Autocomplete Chrome | `autocomplete="nope"` para campos com lookup próprio |
| PDF / Espelho | `render_pdf()` em `financeiro/relatorios.py` → WeasyPrint |
| Hierarquia Alpine | temp ID (`_tid`) no array → dois passes no view para resolver FK pai |
| Grupos hierárquicos | View computa `grupos = [{servico, filhos}]`, template itera |

---

## Pendente / Em Homologação

| Item | Status |
|---|---|
| **OS Evolution — Homologação** | ⏳ Em homologação pelo usuário |
| Inventário de Estoque | ⏳ Pendente |
| Fase de importação de dados VDF | ⏳ Pendente |
| Licença de uso por empresa + expiração de senha | ⏳ Pendente (antes do deploy) |
| Módulo Projetos / Financeiro avançado | ⏳ Pendente |

---

## Referências Rápidas

```
Login:  http://127.0.0.1:8000/login/
Admin:  http://127.0.0.1:8000/admin/
User:   admin
Senha:  #Salmos128
```

```bash
source .venv/Scripts/activate
python manage.py check
python manage.py makemigrations && python manage.py migrate
python manage.py runserver
```
