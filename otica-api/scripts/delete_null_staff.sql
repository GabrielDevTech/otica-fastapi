-- SQL para deletar registro de staff_members com store_id e department_id NULL
-- ATENÇÃO: Este comando irá DELETAR permanentemente o registro

DELETE FROM staff_members 
WHERE id = 1 
  AND organization_id = 'org_362OYRBaXMAnCkLlLmpYqPWOe8z'
  AND store_id IS NULL 
  AND department_id IS NULL;

-- Verificar se foi deletado
SELECT * FROM staff_members WHERE id = 1;

