# Project Brief

## Visão Geral
Sistema SaaS Multi-tenant para gestão de óticas. Backend API desenvolvido em Python/FastAPI com arquitetura multi-tenancy lógico, utilizando Clerk para autenticação e PostgreSQL como banco de dados.

## Objetivos Principais
- Fornecer API RESTful para gestão completa de óticas
- Implementar isolamento seguro de dados por organização (multi-tenancy)
- Gerenciar equipe (staff) dentro de cada organização
- Autenticação e autorização via Clerk (JWT)

## Escopo do Projeto
**Fase 1 (Atual)**: Módulo de Gestão de Equipe (Staff)
- CRUD de membros da equipe
- Filtros e busca
- Estatísticas agregadas
- Integração com Clerk para autenticação

**Futuro**: Módulos adicionais (pacientes, produtos, vendas, etc.)

## Requisitos Fundamentais
- **Multi-tenancy**: Isolamento de dados por `organization_id` extraído do token JWT
- **Segurança**: Validação de tokens Clerk via JWKS, nunca confiar em `organization_id` do corpo da requisição
- **Stateless**: Nenhuma sessão em memória, tudo via tokens
- **Assíncrono**: Uso de SQLAlchemy async com asyncpg

## Restrições e Considerações
- Python 3.14
- PostgreSQL como banco de dados obrigatório
- Clerk como provedor de autenticação obrigatório
- CORS configurado apenas para origem do frontend
- Variáveis sensíveis apenas em `.env`

## Stakeholders
- Desenvolvedor backend
- Equipes de óticas (usuários finais)

---

**Nota**: Este documento é a base de referência para todo o projeto. Atualize conforme o projeto evolui e os requisitos ficam mais claros.

