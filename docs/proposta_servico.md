# Proposta de Prestação de Serviço
## Sistema Europa — Gestão Empresarial em Nuvem

**Versão:** 1.0  
**Data:** Abril / 2026  
**Validade:** 60 dias

---

## 1. Apresentação

O **Sistema Europa** é uma plataforma de gestão empresarial (ERP) desenvolvida em tecnologia moderna, multi-empresa e baseada em nuvem. Projetada para pequenas e médias empresas, oferece controle integrado de cadastros, finanças, serviços, estoque e vendas em um único ambiente web — acessível de qualquer dispositivo, sem necessidade de instalação local.

**Stack tecnológico:**
- Back-end: Python 3.12 / Django 6
- Banco de dados: PostgreSQL
- Geração de PDF: WeasyPrint
- Hospedagem: Hetzner Cloud (Alemanha / Helsinque)
- Segurança: HTTPS, autenticação por usuário, isolamento total de dados por empresa

---

## 2. Módulos e Funcionalidades

### 2.1 Administrativo (Core)
> Configuração e governança do sistema.

| Funcionalidade | Descrição |
|---|---|
| Gestão de Usuários | Cadastro, permissões por módulo, vínculo com empresa |
| Cadastro de Empresa | Dados institucionais, parâmetros operacionais, identidade visual por módulo |
| Plano de Contas | Estrutura contábil (Débito / Crédito) com agrupamentos |
| Sub-Contas | Detalhamento analítico do plano de contas |
| Projetos e Orçamentos | Criação de projetos com orçamento estimado × realizado por conta |
| Configuração de Caixa | Parâmetros de abertura, portadores padrão e descrições de lançamento |
| Cidades / Bancos / CFOPs | Tabelas de referência compartilhadas entre empresas |

---

### 2.2 Cadastros
> Base de dados mestre da empresa.

| Funcionalidade | Descrição |
|---|---|
| Clientes e Fornecedores | Cadastro unificado (C/F/Vendedor/Técnico), pessoa física e jurídica |
| Itens / Produtos / Serviços | Catálogo com grupo, unidade, preço base, comissão e saldo de estoque |
| Grupos de Itens | Classificação hierárquica com cores para listagem |
| Tabelas de Preço | Múltiplas tabelas com parcelamento em até 12x por item |
| Condições de Pagamento | Configuração de parcelas e prazos |
| Portadores | Meios de recebimento (dinheiro, PIX, cartão, cheque etc.) |
| Métodos de Pagamento | Formas operacionais com controle de movimentação de caixa |
| Histórico do Cliente | Registro de vendas realizadas por cliente |

---

### 2.3 Financeiro
> Controle completo de receitas, despesas e fluxo de caixa.

| Funcionalidade | Descrição |
|---|---|
| Contas a Receber | Lançamento, baixa manual, renegociação, cancelamento e impressão |
| Contas a Pagar | Lançamento, baixa e controle de vencimentos |
| Caixa | Abertura/fechamento de sessão, entradas, saídas, sangria, suprimento |
| Recebimento via Caixa | Baixa de CR com registro automático de movimento de caixa |
| Pagamento via Caixa | Baixa de CP com registro automático de movimento de caixa |
| Orçamento × Realizado | Alerta ao ultrapassar orçamento estimado por projeto/conta |
| Assistente de Recebimento Recorrente | Geração em lote de CR para clientes com valor de referência |
| Operadoras de Cartão | Cadastro de taxas e controle de recebimentos parcelados |
| Boletos | Geração de remessa de boletos bancários |
| Relatórios (PDF) | Listagem de CR/CP, extrato de caixa, orçamento por projeto |

---

### 2.4 CRM / Serviços
> Relacionamento com clientes e execução de ordens de serviço.

| Funcionalidade | Descrição |
|---|---|
| Contatos com Clientes | Histórico de interações com status e agendamento de retorno |
| Ordens de Serviço | Emissão, alocação de itens, vendedor e técnico responsável |
| Agenda de OS | Visualização por data e período (matutino / vespertino) |
| Roteiros de Assistência | Agrupamento de OS em roteiros com alocação de técnicos e capacidade |
| Cobranças em Roteiro | Registro de boletos e cobranças vinculados ao roteiro |
| Parcelas e Condições | Parcelamento automático por condição de pagamento na OS |

---

### 2.5 Estoque
> Rastreabilidade de entradas e saídas de produtos.

| Funcionalidade | Descrição |
|---|---|
| Notas Fiscais de Entrada | Cadastro de NF de compra com itens, CFOP, IPI e ICMS |
| Movimentos de Estoque | Registro de entradas e saídas com origem (NF, Pedido, OS, Ajuste) |
| Requisições | Solicitação interna de materiais com controle de atendimento parcial |
| Saldo por Item | Atualização automática do saldo ao registrar NF ou movimento |

---

### 2.6 Vendas
> Ciclo completo de pedidos e comissionamento.

| Funcionalidade | Descrição |
|---|---|
| Pedidos de Venda | Emissão com tabela de preço, condição de pagamento e parcelamento automático |
| Itens do Pedido | Produtos/serviços com preço unitário, instalação e controle de estoque |
| Faturamento e Instalação | Controle de status do pedido (Aberto → Faturado → Instalado) |
| Comissões | Cálculo e acerto de comissões por vendedor / representante |
| Configuração de Comissão | Faixas de comissão para televendas, meio e representante (4 faixas) |

---

## 3. Plano de Treinamento

O treinamento é realizado de forma remota (Google Meet / Teams), com gravação disponibilizada ao contratante. Sugerimos a seguinte distribuição:

| Módulo | Carga Horária | Perfil Indicado | Formato |
|---|:---:|---|---|
| Administrativo — Configuração inicial | 3h | Gestor / TI | Remoto — individual |
| Cadastros | 4h | Equipe operacional | Remoto — grupo |
| Financeiro — Contas a Receber/Pagar | 4h | Financeiro | Remoto — grupo |
| Financeiro — Caixa e Fechamento | 3h | Operador de caixa | Remoto — individual |
| CRM / Ordens de Serviço | 4h | Atendimento / Campo | Remoto — grupo |
| Estoque | 3h | Almoxarifado / Compras | Remoto — individual |
| Vendas e Comissões | 4h | Vendedores / Gestão | Remoto — grupo |
| **Total** | **25h** | | |

> **Suporte pós-treinamento:** 30 dias de suporte por e-mail e WhatsApp inclusos no contrato de implantação.

---

## 4. Infraestrutura de Hospedagem — Hetzner Cloud

A hospedagem é provisionada na **Hetzner Cloud** (data centers em Falkenstein/DE ou Helsinque/FI), com os seguintes recursos:

### 4.1 Configurações disponíveis

| Tier | Servidor | vCPU | RAM | Armazenamento | Hetzner (€/mês) | Aprox. R$/mês |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Micro** | CX22 | 2 | 4 GB | 40 GB SSD | €3,85 | ~R$ 24 |
| **Pequeno** | CX32 | 4 | 8 GB | 80 GB SSD | €7,29 | ~R$ 46 |
| **Médio** | CX42 | 8 | 16 GB | 160 GB SSD | €15,90 | ~R$ 100 |
| **Grande** | CX52 | 16 | 32 GB | 320 GB SSD | €34,49 | ~R$ 217 |

> Conversão aproximada: 1 EUR = R$ 6,30. Valores sujeitos à variação cambial.

### 4.2 Dimensionamento recomendado por número de usuários simultâneos

| Usuários ativos simultâneos | Tier recomendado | Custo hospedagem (R$/mês) |
|:---:|---|:---:|
| Até 10 | Micro (CX22) | R$ 24 |
| 11 a 25 | Pequeno (CX32) | R$ 46 |
| 26 a 60 | Médio (CX42) | R$ 100 |
| 61 a 150 | Grande (CX52) | R$ 217 |
| Acima de 150 | Múltiplos servidores | sob consulta |

### 4.3 Serviços adicionais de infraestrutura

| Item | Custo estimado (R$/mês) |
|---|:---:|
| Backup automático diário (20% do servidor) | R$ 5 a R$ 44 |
| Volume de armazenamento adicional (100 GB) | ~R$ 32 |
| IP dedicado (Floating IP) | ~R$ 2 |
| Certificado SSL (Let's Encrypt) | Gratuito |
| Domínio (registro anual) | ~R$ 50/ano |

---

## 5. Modelo de Precificação — Locação por Usuário

### 5.1 Estrutura de planos

A precificação é baseada em **usuários ativos cadastrados** por empresa, cobrada mensalmente. O acesso ao sistema é modular — cada usuário é configurado com os módulos que necessita.

| Módulo | Valor por usuário/mês |
|---|:---:|
| Administrativo + Cadastros (base obrigatória) | R$ 30,00 |
| Financeiro | R$ 45,00 |
| CRM / Serviços | R$ 35,00 |
| Estoque | R$ 30,00 |
| Vendas | R$ 35,00 |

### 5.2 Planos pré-configurados (desconto por bundle)

| Plano | Módulos incluídos | Por usuário/mês |
|---|---|:---:|
| **Essencial** | Administrativo + Cadastros + Financeiro | R$ 65,00 |
| **Operacional** | Essencial + CRM/Serviços + Estoque | R$ 110,00 |
| **Completo** | Todos os módulos | R$ 140,00 |

> Mínimo de **2 usuários** por empresa contratante.

### 5.3 Tabela de custo total estimado por empresa

| Usuários | Plano Essencial | Plano Operacional | Plano Completo | + Hospedagem* |
|:---:|:---:|:---:|:---:|:---:|
| 2 | R$ 130 | R$ 220 | R$ 280 | + R$ 24 |
| 5 | R$ 325 | R$ 550 | R$ 700 | + R$ 24 |
| 10 | R$ 650 | R$ 1.100 | R$ 1.400 | + R$ 46 |
| 20 | R$ 1.300 | R$ 2.200 | R$ 2.800 | + R$ 46 |
| 50 | R$ 3.250 | R$ 5.500 | R$ 7.000 | + R$ 100 |

*Hospedagem cobrada por empresa contratante, dimensionada conforme uso.

### 5.4 Implantação (taxa única)

| Item | Valor |
|---|:---:|
| Configuração do ambiente e banco de dados | R$ 500,00 |
| Migração de dados (planilhas / sistema legado) | sob consulta |
| Treinamento (25h conforme seção 3) | R$ 2.500,00 |
| **Total implantação (sem migração)** | **R$ 3.000,00** |

---

## 6. Resumo do Investimento

### Exemplo: empresa com 5 usuários — Plano Completo

| Item | Mensal | Anual |
|---|:---:|:---:|
| Licença de uso (5 usuários × R$ 140) | R$ 700,00 | R$ 8.400,00 |
| Hospedagem Hetzner (Micro) | R$ 24,00 | R$ 288,00 |
| **Total recorrente** | **R$ 724,00** | **R$ 8.688,00** |
| Implantação + Treinamento (taxa única) | — | R$ 3.000,00 |
| **Investimento total no 1º ano** | | **R$ 11.688,00** |

### Exemplo: empresa com 15 usuários — Plano Operacional

| Item | Mensal | Anual |
|---|:---:|:---:|
| Licença de uso (15 usuários × R$ 110) | R$ 1.650,00 | R$ 19.800,00 |
| Hospedagem Hetzner (Pequeno) | R$ 46,00 | R$ 552,00 |
| **Total recorrente** | **R$ 1.696,00** | **R$ 20.352,00** |
| Implantação + Treinamento (taxa única) | — | R$ 3.000,00 |
| **Investimento total no 1º ano** | | **R$ 23.352,00** |

---

## 7. Condições Gerais

- **Contrato mínimo:** 12 meses
- **Reajuste anual:** IPCA do período
- **SLA de disponibilidade:** 99,5% mensal
- **Suporte contínuo:** por e-mail e WhatsApp em dias úteis, horário comercial
- **Backups:** diários, retenção de 7 dias
- **Atualizações:** inclusas no contrato de locação
- **Rescisão antecipada:** multa de 2 mensalidades vigentes

---

*Proposta elaborada com base no estado atual do sistema Europa — versão em desenvolvimento ativo.*  
*Valores e especificações sujeitos a ajuste antes da assinatura do contrato.*
