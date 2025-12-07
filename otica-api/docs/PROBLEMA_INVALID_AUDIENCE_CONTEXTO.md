# Contexto do Problema: "Invalid audience" no Supabase Auth

## 📋 Resumo Executivo

O backend está retornando erro `401 Unauthorized` com a mensagem `"Token inválido: Invalid audience"` ao tentar validar tokens JWT do Supabase, mesmo após múltiplas tentativas de correção. O problema persiste mesmo com validação manual de assinatura implementada.

---

## 🔍 Estado Atual do Problema

### Sintoma Principal
- **Erro**: `Token inválido: Invalid audience`
- **Status HTTP**: `401 Unauthorized`
- **Ocorrência**: Todas as requisições autenticadas à API
- **Token**: JWT do Supabase usando algoritmo `HS256`

### Informações do Token
- **Algoritmo**: `HS256` (simétrico)
- **Key ID (kid)**: `Tcjrp1XPkjTUYgh/`
- **Audience (aud)**: `authenticated`
- **organization_id**: Presente em `app_metadata` ✅
- **Expiração**: Token válido (não expirado) ✅

### Configuração do Backend
- **AUTH_PROVIDER**: `supabase` ✅
- **SUPABASE_URL**: Configurado ✅
- **SUPABASE_ANON_KEY**: Configurado ✅
- **SUPABASE_SERVICE_KEY**: Configurado ✅

---

## 🛠️ Tentativas de Correção Realizadas

### 1. Primeira Tentativa: Desabilitar verificação de `aud`
**Arquivo**: `app/core/auth/supabase_provider.py`

```python
options={
    "verify_signature": True,
    "verify_aud": False,  # Desabilita verificação de audience
    "verify_iss": False,
    "verify_exp": True,
    ...
}
```

**Resultado**: ❌ Falhou - `python-jose` ainda valida `aud` mesmo com `verify_aud: False`

### 2. Segunda Tentativa: Workaround com decodificação não verificada
**Estratégia**: Decodificar sem validar, depois validar apenas assinatura

```python
unverified_payload = jwt.decode(token, "", options={"verify_signature": False})
# Depois tenta validar apenas assinatura
```

**Resultado**: ❌ Falhou - `python-jose` ainda valida `aud` durante `jwt.decode()`

### 3. Terceira Tentativa: Validação manual de assinatura HS256
**Arquivo**: `app/core/auth/supabase_provider.py`
**Função adicionada**: `verify_hmac_signature()`

**Implementação**:
```python
def verify_hmac_signature(self, token: str, secret: str) -> bool:
    """Valida a assinatura HS256 de um token JWT manualmente usando HMAC."""
    parts = token.split('.')
    header_payload = f"{parts[0]}.{parts[1]}"
    signature_received = parts[2]
    
    # Calcula assinatura esperada
    signature_bytes = hmac.new(
        secret.encode('utf-8'),
        header_payload.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    expected_signature = base64.urlsafe_b64encode(signature_bytes).decode('utf-8').rstrip('=')
    
    return hmac.compare_digest(signature_received.rstrip('='), expected_signature.rstrip('='))
```

**Uso no código**:
```python
if actual_alg == "HS256":
    # Valida assinatura manualmente (ignora completamente validação de aud)
    if not self.verify_hmac_signature(token, self.service_key):
        raise HTTPException(...)
    
    payload = unverified_payload
    # Valida expiração manualmente
```

**Resultado**: ❌ **AINDA FALHA** - O erro "Invalid audience" persiste

---

## 🔬 Análise do Problema

### Por que ainda está falhando?

1. **O código de validação manual foi implementado**, mas o erro persiste
2. **Possíveis causas**:
   - O servidor não foi reiniciado após as mudanças
   - Há outro ponto no código que ainda usa `jwt.decode()` com validação de `aud`
   - A função `verify_hmac_signature()` pode ter um bug
   - O `SUPABASE_SERVICE_KEY` pode não ser a chave correta para validar tokens de acesso

### Pontos de Atenção

#### 1. Diferença entre `SUPABASE_SERVICE_KEY` e chave JWT secreta
- **`SUPABASE_SERVICE_KEY`**: É um JWT em si, usado para autenticação admin
- **Chave JWT secreta**: É a chave usada para assinar tokens de acesso (`access_token`)
- **Problema potencial**: Estamos usando `SUPABASE_SERVICE_KEY` (que é um JWT) como chave secreta para validar tokens HS256, mas pode não ser a chave correta

#### 2. Tokens HS256 do Supabase
- Tokens de acesso (`access_token`) do Supabase podem ser assinados com uma chave secreta diferente da `SERVICE_KEY`
- A chave secreta JWT pode estar em outro lugar (configurações do projeto Supabase)

#### 3. Validação de assinatura manual
- A função `verify_hmac_signature()` pode estar calculando a assinatura incorretamente
- Pode haver diferença entre base64url e base64 padrão
- O `kid` no header pode indicar qual chave usar, mas estamos ignorando isso

---

## 📁 Estrutura do Código Atual

### Arquivo Principal: `app/core/auth/supabase_provider.py`

**Fluxo de validação atual**:

1. Tenta obter JWKS (para RS256)
2. Se JWKS vazio ou não disponível:
   - Decodifica token sem validar para ver algoritmo
   - Se `HS256`:
     - Valida assinatura manualmente com `verify_hmac_signature()`
     - Valida expiração manualmente
     - Usa `unverified_payload`
3. Extrai `organization_id` do payload
4. Retorna dados do token

**Problema identificado**: Mesmo com validação manual, o erro "Invalid audience" ainda ocorre, sugerindo que:
- O código pode não estar entrando no bloco correto
- Pode haver outro ponto de validação que ainda usa `jwt.decode()`
- A validação manual pode estar falhando silenciosamente

---

## 🧪 Testes Realizados

### Script de Teste: `scripts/test_token_api.py`

**O que o script faz**:
1. ✅ Faz login no Supabase
2. ✅ Obtém token JWT
3. ✅ Decodifica token manualmente (sem validação)
4. ⚠️ Tenta validar assinatura (falha com "Signature verification failed")
5. ✅ Valida expiração manualmente
6. ❌ Testa requisições à API (todas falham com "Invalid audience")

**Resultados**:
- Token é válido (não expirado)
- `organization_id` está presente
- Assinatura não pode ser validada localmente (mas isso é esperado se a chave estiver errada)
- **Backend ainda retorna "Invalid audience"** mesmo após implementação de validação manual

---

## 🔍 Possíveis Causas Raiz

### 1. Servidor não reiniciado
**Probabilidade**: Alta
- As mudanças no código podem não estar ativas
- Python pode ter cache de módulos

**Solução**: Reiniciar servidor completamente

### 2. Chave incorreta para validação HS256
**Probabilidade**: Média
- `SUPABASE_SERVICE_KEY` pode não ser a chave correta para validar `access_token`
- Tokens de acesso podem usar uma chave JWT secreta diferente

**Solução**: Verificar documentação do Supabase sobre qual chave usar

### 3. Bug na função `verify_hmac_signature()`
**Probabilidade**: Média
- Cálculo de assinatura pode estar incorreto
- Diferença entre base64url e base64 padrão

**Solução**: Testar função isoladamente e comparar com resultado esperado

### 4. Outro ponto de validação no código
**Probabilidade**: Baixa
- Pode haver outro lugar no código que valida o token
- Middleware ou decorator adicional

**Solução**: Buscar por todas as ocorrências de `jwt.decode()` no código

### 5. `python-jose` valida `aud` mesmo com `verify_aud: False`
**Probabilidade**: Alta (já confirmado)
- `python-jose` pode ter comportamento inconsistente
- Pode validar `aud` antes de chegar às opções

**Solução**: Usar validação completamente manual (já implementado, mas pode ter bug)

---

## 💡 Soluções Propostas

### Solução 1: Verificar se servidor foi reiniciado
```bash
# Parar servidor completamente
# Deletar __pycache__ se existir
find . -type d -name __pycache__ -exec rm -r {} +
# Reiniciar servidor
python -m uvicorn app.main:app --reload
```

### Solução 2: Extrair chave JWT secreta do Supabase
- A chave JWT secreta pode estar nas configurações do projeto Supabase
- Pode ser necessário usar a API Admin do Supabase para obter a chave correta
- Ou usar o `kid` do token para identificar qual chave usar

### Solução 3: Usar validação via API do Supabase
Em vez de validar localmente, fazer uma requisição à API do Supabase para validar o token:
```python
async def verify_token_via_api(self, token: str) -> dict:
    """Valida token fazendo requisição à API do Supabase."""
    url = f"{self.supabase_url}/auth/v1/user"
    headers = {"Authorization": f"Bearer {token}"}
    # Se retornar 200, token é válido
```

### Solução 4: Decodificar completamente sem validação e confiar no Supabase
- Decodificar token sem validar assinatura
- Validar apenas expiração
- Confiar que o token veio do Supabase (se a requisição veio do frontend com token válido)

### Solução 5: Usar biblioteca diferente para JWT
- Trocar `python-jose` por `PyJWT` que pode ter comportamento diferente
- Ou usar `jwt` (PyJWT) que é mais comum e pode ter melhor suporte

---

## 📊 Estado do Código

### Arquivos Modificados
1. `app/core/auth/supabase_provider.py`
   - Adicionada função `verify_hmac_signature()`
   - Modificada validação HS256 para usar validação manual
   - Adicionados imports: `hmac`, `hashlib`

2. `scripts/test_token_api.py`
   - Script de teste criado
   - Testa login, decodificação, validação e requisições à API

### Arquivos de Documentação
1. `docs/FRONTEND_TROUBLESHOOTING.md` - Guia de troubleshooting para frontend
2. `docs/FRONTEND_SUPABASE_AUTH.md` - Guia de integração Supabase para frontend

---

## 🎯 Próximos Passos Recomendados

### Imediato
1. **Verificar se servidor foi reiniciado** após última mudança
2. **Adicionar logs detalhados** no `supabase_provider.py` para ver qual caminho o código está seguindo
3. **Testar função `verify_hmac_signature()` isoladamente** com um token conhecido

### Curto Prazo
1. **Investigar qual chave usar para validar tokens HS256 do Supabase**
2. **Considerar usar validação via API do Supabase** em vez de validação local
3. **Testar com PyJWT** em vez de `python-jose`

### Longo Prazo
1. **Documentar processo de validação de tokens Supabase**
2. **Criar testes automatizados** para validação de tokens
3. **Considerar migrar para RS256** se possível (mais seguro e padrão)

---

## 📝 Notas Técnicas

### Sobre tokens HS256 do Supabase
- Tokens de acesso (`access_token`) podem usar HS256 ou RS256
- A chave para HS256 pode não ser a `SERVICE_KEY`
- O `kid` no header pode indicar qual chave usar

### Sobre `python-jose`
- Pode validar `aud` mesmo com `verify_aud: False` em algumas versões
- Comportamento pode variar entre versões
- Alternativa: `PyJWT` (biblioteca `jwt`)

### Sobre validação manual
- Validação manual de assinatura HS256 é possível e segura
- Requer cálculo correto de HMAC-SHA256
- Deve usar base64url (não base64 padrão)

---

## 🔗 Referências

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [JWT.io](https://jwt.io/) - Para decodificar e testar tokens
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

**Última atualização**: 2024-12-19  
**Status**: Problema persistente - Requer investigação adicional  
**Prioridade**: Alta - Bloqueia autenticação completa
