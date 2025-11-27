-- Script SQL para criar usuário de teste como ADMIN
-- IMPORTANTE: Substitua 'org_xxx' pelo organization_id do seu token Clerk

-- Exemplo de INSERT para criar usuário ADMIN
INSERT INTO staff_members (
    clerk_id,
    organization_id,
    full_name,
    email,
    role,
    is_active,
    department
) VALUES (
    'user_362f7Ug2v5SRN',  -- ← User ID do Clerk (ajuste se necessário)
    'org_xxx',              -- ← SUBSTITUA pelo organization_id do seu token!
    '123 123',              -- ← Nome completo
    'bielleandro75@gmail.com',
    'ADMIN',                -- ← Role ADMIN (máximo controle)
    true,                   -- ← Ativo
    NULL                    -- ← Department (opcional)
)
ON CONFLICT (clerk_id) DO UPDATE SET
    organization_id = EXCLUDED.organization_id,
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active;

-- Verificar se foi criado
SELECT 
    id,
    clerk_id,
    organization_id,
    full_name,
    email,
    role,
    is_active,
    created_at
FROM staff_members
WHERE clerk_id = 'user_362f7Ug2v5SRN';

