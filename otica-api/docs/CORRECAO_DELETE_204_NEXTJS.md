# Correção: DELETE 204 com Proxy Next.js

## Problema Identificado

O endpoint `DELETE /api/v1/customers/{customer_id}` estava retornando status `204 No Content`, mas o proxy do Next.js estava gerando erro:

```
Proxy error: TypeError: Response constructor: Invalid response status code 204
```

### Causa

O proxy do Next.js (route handler) não estava configurado corretamente para lidar com respostas `204 No Content` que não têm body.

## Solução Implementada

### Opção 1: Retornar 200 com JSON (Implementada)

Alteramos o endpoint DELETE para retornar `200 OK` com um JSON simples em vez de `204 No Content`:

```python
@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(...):
    """Desativa um cliente (soft delete)."""
    # ... lógica de deleção ...
    customer.is_active = False
    await db.commit()
    
    return {"message": "Cliente deletado com sucesso", "id": customer_id}
```

**Vantagens:**
- ✅ Compatível com proxy Next.js
- ✅ Retorna informação útil (mensagem e ID)
- ✅ Frontend pode verificar o sucesso facilmente

**Desvantagens:**
- ⚠️ Não segue estritamente o padrão REST (DELETE deveria retornar 204)
- ⚠️ Retorna body quando tecnicamente não deveria

### Opção 2: Corrigir Proxy Next.js (Recomendado para futuro)

Se você quiser manter o padrão REST (204 No Content), ajuste o proxy do Next.js:

**Arquivo**: `app/api/backend/[...path]/route.ts` (ou similar)

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = `${process.env.BACKEND_URL}/api/v1/${path}`;
  
  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
      },
    });
    
    // Se for 204, retornar 204 sem body
    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }
    
    // Para outros status, retornar normalmente
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao processar requisição' },
      { status: 500 }
    );
  }
}
```

**Ou para todos os métodos:**

```typescript
export async function handler(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = `${process.env.BACKEND_URL}/api/v1/${path}`;
  
  try {
    const response = await fetch(url, {
      method: request.method,
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'Content-Type': request.headers.get('Content-Type') || 'application/json',
      },
      body: request.method !== 'GET' && request.method !== 'DELETE' 
        ? await request.text() 
        : undefined,
    });
    
    // Se for 204, retornar 204 sem body
    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }
    
    // Para outros status, retornar JSON
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao processar requisição' },
      { status: 500 }
    );
  }
}
```

## Comportamento Atual

### Endpoint DELETE

**Request:**
```http
DELETE /api/v1/customers/4
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "message": "Cliente deletado com sucesso",
  "id": 4
}
```

### Frontend

O frontend agora pode tratar a resposta assim:

```typescript
const response = await fetch(`/api/backend/api/v1/customers/${id}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});

if (response.ok) {
  const data = await response.json();
  console.log(data.message); // "Cliente deletado com sucesso"
  console.log(data.id); // 4
}
```

## Testes

### Backend (via Swagger/Postman)

1. Fazer DELETE em um cliente existente
2. **Esperado**: Status 200 com JSON `{"message": "Cliente deletado com sucesso", "id": X}`
3. Verificar que `is_active = False` no banco

### Frontend

1. Deletar cliente via interface
2. **Esperado**: Sem erro 500, cliente removido da lista
3. Verificar console para mensagem de sucesso

## Observações

- **Compatibilidade**: A solução atual (200 OK) é compatível com qualquer proxy
- **Padrão REST**: Se quiser seguir estritamente REST, use a Opção 2 (corrigir proxy)
- **Outros endpoints DELETE**: Se houver outros endpoints DELETE, considere aplicar a mesma lógica ou corrigir o proxy para todos

## Arquivos Modificados

Todos os endpoints DELETE foram corrigidos para retornar `200 OK` com JSON:

- `otica-api/app/routers/v1/customers.py`
  - `delete_customer()`: Alterado de `204 No Content` para `200 OK` com JSON

- `otica-api/app/routers/v1/product_frames.py`
  - `delete_product_frame()`: Alterado de `204 No Content` para `200 OK` com JSON

- `otica-api/app/routers/v1/product_lenses.py`
  - `delete_product_lens()`: Alterado de `204 No Content` para `200 OK` com JSON

- `otica-api/app/routers/v1/stores.py`
  - `delete_store()`: Alterado de `204 No Content` para `200 OK` com JSON

- `otica-api/app/routers/v1/departments.py`
  - `delete_department()`: Alterado de `204 No Content` para `200 OK` com JSON

## Próximos Passos (Opcional)

Se quiser voltar ao padrão REST (204 No Content):
1. Corrigir o proxy do Next.js conforme Opção 2
2. Reverter o endpoint DELETE para retornar 204
3. Testar que o proxy lida corretamente com 204

