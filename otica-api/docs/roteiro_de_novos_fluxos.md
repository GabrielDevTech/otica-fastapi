🚀 Roteiro de Implementação: Sprint 1 (Alicerces)
Objetivo: Criar a base de dados necessária para suportar o Hub de Vendas. Ordem de Dependência: 1A/1B → 2 → 3 → 4 → 5.

1º Passo (A): Cadastro de Lojas (stores)
A estrutura física da empresa.

Objetivo: Definir onde há estoque físico e movimentação financeira.

Tabela: stores

Campos Essenciais (Backend):

name: String (Ex: "Matriz - Centro")

tax_rate_machine: Decimal (Ex: 2.5) - Vital para o cálculo líquido no módulo Apoio de Caixa.

address_data: JSONB (Endereço completo).

Exemplo de Payload (POST):

JSON

{
  "name": "Óticas Diniz - Filial Shopping",
  "address_data": { "rua": "Av. Central", "numero": "100", "cep": "88000-000" },
  "phone": "(48) 9999-9999",
  "tax_rate_machine": 2.5
}
1º Passo (B): Cadastro de Departamentos (departments)
A estrutura organizacional.

Objetivo: Agrupar colaboradores por função/setor, independente da loja física.

Tabela: departments

Sugestão de Carga Inicial (Seed): Ao criar a conta da Organização, o sistema já deve criar auto: Vendas, Gerência, Financeiro, Laboratório.

Exemplo de Payload (POST):

JSON

{
  "name": "Laboratório e Montagem",
  "description": "Responsável pela conferência e montagem de óculos"
}
2º Passo: Finalizar Equipe (staff_members)
O Vínculo (Quem é quem).

Contexto: O usuário já existe no Clerk (Auth). Agora precisamos dizer onde ele trabalha e o que faz.

Mudança no Banco: A tabela staff_members precisa de duas Foreign Keys (FK) obrigatórias.

store_id (FK): Vincula à Loja (Passo 1A).

department_id (FK): Vincula ao Departamento (Passo 1B).

Fluxo de Tela: O Admin edita o usuário e preenche esses dois selects.

Exemplo de Payload (PUT):

JSON

{
  "role": "SELLER",           // Define permissões (RBAC)
  "store_id": 10,             // Onde ele baixa estoque
  "department_id": 2          // Setor de Vendas
}
3º Passo: Cadastro de Armações (products_frames)
O Produto Unitário.

Tabela: products_frames e inventory_levels.

Campos Críticos:

reference_code: Código de Barras (Vital para o leitor no PDV).

sell_price: Preço de Venda (Automático no PDV).

min_stock_alert: Gatilho para dashboard.

Dica de Backend: O endpoint de POST (criar produto) deve aceitar um campo opcional initial_stock. Se enviado, o backend já cria o registro na tabela inventory_levels para a loja do usuário logado.

4º Passo: Cadastro de Lentes (products_lenses)
O Produto Complexo (Grade vs. Pedido).

Aqui o sistema bifurca. O Backend precisa tratar dois tipos de produto na mesma tela:

Tipo A: Lentes de Estoque (Prontas)

Cadastro: Marca + Modelo + Tratamento.

Estoque: O sistema deve gerar uma matriz (Grade) na tabela lens_stock_grid.

Ex: Esférico -2.00 / Cilíndrico -1.00 = 5 pares.

Tipo B: Lentes de Surfaçagem (Laboratório)

Cadastro: Apenas Modelo e Preço.

Estoque: Não existe grade física.

Flag no Banco: Campo is_lab_order = true. Isso avisa o módulo de Vendas que esse item gera uma Ordem de Serviço para o laboratório, e não uma baixa de estoque imediata.

5º Passo: Cadastro de Clientes (customers)
O Consumidor (CRM).

Objetivo: Permitir que a venda seja nominal e fiscalmente válida.

Campos Diferenciais para Ótica:

cpf: Obrigatório para NFC-e.

birth_date: Obrigatório (Idade define a "Adição" em lentes multifocais).

profession: Ajuda na venda consultiva.

Integração: Criar endpoint POST /customers otimizado para ser chamado via Modal (Popup) de dentro da tela de vendas.