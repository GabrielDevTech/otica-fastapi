# Configurar Senhas no Supabase Auth

## 🔐 Situação Atual

Durante a migração do Clerk para Supabase, os usuários foram criados **sem senha** por questões de segurança (o Clerk não permite exportar senhas). Isso significa que os usuários **não conseguem fazer login** até que configurem uma senha.

## ✅ Opções para Configurar Senhas

### Opção 1: Reset de Senha via Email (Recomendado)

Esta é a forma mais segura e recomendada. O Supabase enviará um email para cada usuário permitindo que eles definam sua própria senha.

#### Passos:

1. **No Supabase Dashboard:**
   - Acesse: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/auth/users
   - Para cada usuário, clique nos três pontos (⋯) → **"Send password reset email"**
   - O usuário receberá um email com link para definir senha

2. **Via Script (Automático):**
   - Execute o script `scripts/send_password_reset_emails.py` (será criado)
   - Ele enviará emails de reset para todos os usuários migrados

### Opção 2: Definir Senha Temporária Manualmente

Você pode definir uma senha temporária para cada usuário no Supabase Dashboard:

1. Acesse: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/auth/users
2. Clique no usuário
3. Na seção **"Password"**, clique em **"Set password"**
4. Defina uma senha temporária
5. Compartilhe a senha temporária com o usuário (por email, WhatsApp, etc.)
6. **Recomendação**: Peça ao usuário para alterar a senha no primeiro login

### Opção 3: Usar Script para Definir Senhas em Lote

Se você tem uma lista de senhas temporárias ou quer definir a mesma senha temporária para todos:

1. Execute o script `scripts/set_passwords_supabase.py` (será criado)
2. O script permite:
   - Definir senha individual por email
   - Definir senha padrão para todos os usuários
   - Ler senhas de um arquivo CSV

## 📧 Configuração de Email no Supabase

Antes de enviar emails de reset, verifique se o email está configurado:

1. Acesse: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/settings/auth
2. Na seção **"SMTP Settings"**:
   - **Opção A**: Use o SMTP padrão do Supabase (limitado, mas funciona)
   - **Opção B**: Configure seu próprio SMTP (recomendado para produção)

### Configurar SMTP Customizado:

1. Vá em **Settings** → **Auth** → **SMTP Settings**
2. Configure:
   - **Host**: smtp do seu provedor (ex: smtp.gmail.com)
   - **Port**: 587 (TLS) ou 465 (SSL)
   - **User**: seu email
   - **Password**: senha do app (não a senha normal)
   - **Sender email**: email que aparecerá como remetente
   - **Sender name**: nome do remetente

## 🔧 Scripts Disponíveis

### 1. Enviar Emails de Reset de Senha

```bash
# Envia email de reset para todos os usuários migrados
py scripts/send_password_reset_emails.py

# Envia para um usuário específico
py scripts/send_password_reset_emails.py --email usuario@example.com
```

### 2. Definir Senhas Manualmente

```bash
# Define senha para um usuário específico
py scripts/set_passwords_supabase.py --email usuario@example.com --password "SenhaTemporaria123"

# Define senha padrão para todos os usuários (CUIDADO!)
py scripts/set_passwords_supabase.py --all --password "SenhaTemporaria123"
```

## ⚠️ Importante

1. **Senhas do Clerk não podem ser migradas**: Por segurança, o Clerk não permite exportar senhas. Todos os usuários precisam definir novas senhas.

2. **Primeiro Login**: Recomende que os usuários alterem a senha temporária no primeiro login.

3. **Segurança**: 
   - Use senhas temporárias fortes
   - Compartilhe senhas temporárias por canal seguro
   - Não reutilize senhas antigas

4. **Email de Reset**: É a forma mais segura, pois o usuário define sua própria senha sem você precisar conhecê-la.

## 📋 Checklist

- [ ] Verificar configuração de SMTP no Supabase
- [ ] Decidir método de configuração de senhas (email reset, manual, ou script)
- [ ] Enviar emails de reset OU definir senhas temporárias
- [ ] Informar usuários sobre a necessidade de definir/alterar senha
- [ ] Testar login com pelo menos um usuário
- [ ] Documentar processo para novos usuários

## 🔗 Links Úteis

- **Supabase Auth Users**: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/auth/users
- **Supabase SMTP Settings**: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/settings/auth
- **Supabase Auth Docs**: https://supabase.com/docs/guides/auth

---

**Última atualização**: 2024-12-19  
**Projeto**: Otica API - Migração Clerk → Supabase
