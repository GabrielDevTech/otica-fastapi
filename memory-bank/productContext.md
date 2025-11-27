# Product Context

## Por que este projeto existe?
Sistema SaaS para gestão de múltiplas óticas, permitindo que cada organização gerencie sua equipe, pacientes, produtos e operações de forma isolada e segura.

## Problemas que resolve
- Gestão centralizada de múltiplas óticas (multi-tenancy)
- Isolamento seguro de dados entre organizações
- Autenticação e autorização robusta via Clerk
- API RESTful para integração com frontend

## Como deve funcionar
1. **Autenticação**: Frontend gerencia login e seleção de organização via Clerk
2. **Autorização**: Backend valida token JWT e extrai `organization_id` automaticamente
3. **Isolamento**: Todas as queries filtram automaticamente por `organization_id` do token
4. **Gestão de Equipe**: CRUD de membros da equipe com diferentes roles (ADMIN, MANAGER, STAFF, ASSISTANT)

## Experiência do Usuário
- Usuário faz login no frontend (Clerk)
- Seleciona organização ativa
- Frontend envia token JWT em todas as requisições
- Backend valida e isola dados automaticamente
- Usuário gerencia equipe dentro de sua organização

## Casos de Uso Principais
1. **Listar equipe**: Ver todos os membros da organização atual com filtros
2. **Criar membro**: Adicionar novo membro à equipe (role, departamento, etc.)
3. **Estatísticas**: Ver contagens agregadas (total, ativos, por role)
4. **Busca**: Filtrar membros por nome/email

---

**Nota**: Este documento descreve o "porquê" e o "como" do produto do ponto de vista do usuário final.

