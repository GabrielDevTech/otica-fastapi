
QUERO USA ESSE NOVOS PROCESSOS PARA CRIAR AS TELAS DO FRONT E O BACKAND PRIMEIRO VAMOS ESTRUTURAR COMO VAI SER O BACKAND PARA MANDAR ESSAS INFORMAÇÕES, ROTAS DA API E BODY E RESPONSES DOCUMENTADO PARA QUE O FRONT INTERPRETE E APLIQUE
📘 Fase 2: O Ciclo de Venda (Seller vs. Manager)

Esta documentação detalha a lógica de negócio para a segunda fase do ERP, com foco fundamental na distinção de responsabilidades entre o Operacional (Seller) e o Gerencial (Manager).

Princípio Central: O Vendedor precisa de agilidade e foco na venda. O Gerente precisa de auditoria e visão macro.

1. Módulo: Apoio de Caixa (Cashier Support)

Cenário: O Dashboard financeiro completo (KPIs, faturamento total) é exclusivo da gerência. O vendedor não deve ter acesso a erros de colegas ou totais da loja.

👥 Separação de Visões (Frontend)

A. Visão do Vendedor (Role: SELLER)

Rota: /apoio-de-caixa (Redirecionamento condicional)

Objetivo: Agilidade. Abrir, vender, fechar.

Interface:

Estado Fechado: Card central simples "Seu caixa está fechado". Botão grande [ Abrir Nova Sessão ]. Input para valor do Fundo de Troco.

Estado Aberto: Painel limpo contendo:

Status: "Sessão Aberta às 08:00"

Botão [ Sangria / Retirada ] (Ex: Pagar lanche, motoboy).

Botão [ Suprimento / Entrada ] (Ex: Buscar troco no banco).

Botão [ Fechar Caixa ].

Restrição: Oculto acesso a gráficos, divergências de terceiros ou faturamento total.

B. Visão do Gerente (Role: MANAGER / ADMIN)

Rota: /apoio-de-caixa/dashboard

Objetivo: Auditoria e Monitoramento.

Interface (Baseada no Dashboard Gerencial):

KPIs Globais: Total de "Sessões Ativas", "Divergências Financeiras", "Taxas de Cartão Estimadas".

Lista de Conciliações Pendentes: Atalho para resolver caixas que fecharam com erro (PENDING_AUDIT).

Lista de Fechamentos Pendentes: Atalho para forçar o fechamento de caixas esquecidos abertos.

⚙️ Lógica de Backend (Regras de Negócio)

1. Auditoria de Divergência:
Quando o Seller fecha o caixa e o valor informado difere do calculado pelo sistema, o status da sessão torna-se PENDING_AUDIT. O Manager deve resolver com uma das ações:

Aceitar Quebra: A loja assume o prejuízo (Lança despesa automaticamente).

Cobrar Funcionário: Gera uma conta a receber contra o vendedor.

Corrigir Valor: Ajuste manual (ex: vendedor esqueceu de lançar uma sangria no sistema). Status final: CLOSED.

2. Cálculo de Taxas de Cartão:

Utiliza o campo store.tax_rate_machine (definido na Fase 1).

Toda venda em cartão gera valor_bruto e valor_liquido. A diferença alimenta o KPI "Taxas Cartão (Mês)".

🔗 Endpoints Críticos

GET  /api/v1/cash-sessions/my-session        # (Seller: retorna estado atual)
GET  /api/v1/cash-sessions/dashboard-stats   # (Manager: alimenta os gráficos)
POST /api/v1/cash-sessions/{id}/audit        # (Manager: resolve a divergência)


2. Módulo: Hub de Vendas (Service Order)

Objetivo: Criação da Ordem de Serviço (OS). É o ambiente principal do Vendedor.

👥 Separação de Visões

Seller: Cria OS, edita (enquanto rascunho) e envia para pagamento.

Manager: Permissões estendidas para conceder descontos acima do limite, cancelar OS finalizadas (estorno) ou reabrir OS fechadas.

⚙️ Lógica de Backend (Regras de Negócio)

1. Reserva de Estoque Inteligente:

Ao adicionar uma Armação na OS (Status DRAFT ou PENDING), o sistema incrementa reserved_quantity na tabela inventory_levels.

Motivo: Evita venda duplicada enquanto o cliente escolhe as lentes.

Expiração (Cron Job): Se a OS permanecer inativa por 24h, a reserva é liberada automaticamente.

2. Validação de Lentes:

Lente de Estoque: Backend verifica existência do par na lens_stock_grid.

Sem saldo: Bloqueia venda ou alerta "Saldo Insuficiente".

Lente Surfaçagem: Backend permite venda sem estoque físico.

Ação: Marca flag needs_purchasing = true para o setor de Compras.

🔗 Endpoints Críticos

POST /api/v1/service-orders           # (Cria OS)
GET  /api/v1/products/search          # (Busca unificada Armação/Lente)


3. Módulo: Checkout / Pagamento (PDV)

Objetivo: Etapa final da venda para processamento financeiro.

⚙️ Lógica de Backend (Regras de Negócio)

1. Vínculo Financeiro Automático:

Dinheiro: Sistema captura o ID da cash_session do Seller logado e cria lançamento de entrada (INFLOW).

Trava: Se não houver caixa aberto, bloqueia o checkout e redireciona para Abertura de Caixa.

Cartão/Pix/Crediário: Ignora caixa físico. Cria registros diretos na tabela receivable_accounts (Contas a Receber).

2. Baixa Definitiva de Estoque:

Ao confirmar pagamento, a reserved_quantity converte-se em baixa real (quantity = quantity - 1).

Gera registro de saída no Kardex (histórico do produto).

3. Comissão (Preparação):

Registra seller_id e valor comissionável da venda para processamento na Fase 3.

🔗 Endpoints Críticos

POST /api/v1/sales/{id}/checkout      # (Processa pagamentos e finaliza)


4. Módulo: Fila de Laboratório (Produção)

Objetivo: Controle de montagem e fluxo de produção.

👥 Separação de Visões

Seller: Visualização passiva do status ("Em Produção", "Pronto") na lista de vendas.

Técnico/Laboratorista: Acesso ao quadro Kanban completo com permissão de movimentação.

⚙️ Lógica de Backend (Regras de Negócio)

1. Fluxo de Status:

Aguardando Montagem: OS paga, produtos separados em estoque.

Aguardando Lente: (Condicional) Surfaçagem pendente de chegada do fornecedor.

Em Produção: Técnico iniciou a montagem.

Pronto / Controle Qualidade: Óculos finalizado. Estoque de lentes baixado (se houver quebra na montagem, registra-se aqui).

2. Rastreabilidade:

Log obrigatório a cada mudança: Quem mudou, Quando mudou, Tempo na etapa (para métricas de gargalo).

🔗 Endpoints Críticos

GET   /api/v1/lab/queue                 # (Visualização Kanban)
PATCH /api/v1/service-orders/{id}/status # (Mover card)


🚦 Resumo: Matriz de Permissões (RBAC)

Guia rápido para configuração de rotas e guardas de navegação.

Ação / Tela

Seller (Vendedor)

Manager (Gerente)

Lab (Técnico)

Apoio de Caixa: Dashboard Geral

❌ Acesso Negado

✅ Acesso Total

❌ Acesso Negado

Apoio de Caixa: Minha Sessão

✅ Apenas a sua

✅ Visualiza todas

❌ Acesso Negado

Apoio de Caixa: Resolver Divergência

❌ Acesso Negado

✅ Sim

❌ Acesso Negado

Hub de Vendas: Criar OS

✅ Sim

✅ Sim

❌ Leitura

Hub de Vendas: Desconto > Limite

❌ Bloqueado

✅ Sim (Override)

❌ N/A

Checkout: Receber Dinheiro

✅ Sim (Se caixa aberto)

✅ Sim

❌ N/A

Laboratório: Mover Status

❌ Leitura

✅ Sim

✅ Sim