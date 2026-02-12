# Como Usar o Sistema de Validação no Frontend

## Páginas Existentes

### 1. ExportPage.tsx - **Exportação BPA**
**Localização:** `frontend/src/pages/ExportPage.tsx`

**O que adicionar:**
1. Botão "Validar Antes de Exportar"
2. Modal mostrando relatório de validação
3. Bloquear exportação se houver erros críticos

**Código exemplo para adicionar:**

```typescript
// No ExportPage.tsx, adicionar função de validação
const validateBeforeExport = async () => {
  setLoading(true);
  try {
    const response = await fetch('http://localhost:8000/api/export/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        cnes: selectedCnes,
        competencia: selectedCompetencia,
        tipo: 'bpa-i',
        apenas_nao_exportados: true
      })
    });
    
    const data = await response.json();
    
    if (data.validation.records_with_errors > 0) {
      // Mostra modal com erros
      setValidationReport(data.validation);
      setShowValidationModal(true);
    } else if (data.validation.records_with_warnings > 0) {
      // Mostra avisos, permite continuar
      setValidationReport(data.validation);
      setShowWarningsModal(true);
    } else {
      // Tudo OK, pode export direto
      handleExport();
    }
  } catch (error) {
    console.error('Erro na validação:', error);
  } finally {
    setLoading(false);
  }
};
```

---

### 2. Firebird Management - **NOVA PÁGINA**

**Você precisa criar:** `frontend/src/pages/FirebirdManagementPage.tsx`

**Funcionalidades:**
- ✅ Visualizar estatísticas do Firebird
- ✅ Limpar dados (total ou por competência)
- ✅ Testar conexão
- ✅ Histórico de operações

**Template da página:**

```typescript
import React, { useEffect, useState } from 'react';
import { Database, Trash2, Activity } from 'lucide-react';

const FirebirdManagementPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // Busca estatísticas
  const loadStats = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/firebird/stats');
      const data = await response.json();
      setStats(data.stats);
    } catch (error) {
      console.error('Erro ao carregar stats:', error);
    }
  };

  // Limpa dados
  const clearData = async (competencia?: string) => {
    if (!confirm('Tem certeza que deseja limpar os dados?')) return;
    
    try {
      const url = competencia 
        ? `http://localhost:8001/api/firebird/clear?competencia=${competencia}`
        : 'http://localhost:8001/api/firebird/clear';
      
      const response = await fetch(url, { method: 'POST' });
      const data = await response.json();
      
      alert(data.message);
      loadStats(); // Recarrega estatísticas
    } catch (error) {
      console.error('Erro ao limpar:', error);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Gerenciamento Firebird</h2>
      
      {/* Estatísticas */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-gray-600">Total de Registros</h3>
          <p className="text-3xl font-bold">{stats?.total_records || 0}</p>
        </div>
        {/* Mais cards... */}
      </div>
      
      {/* Botões de ação */}
      <div className="space-x-4">
        <button onClick={() => clearData()} className="btn-danger">
          <Trash2 className="w-4 h-4" />
          Limpar Todos os Dados
        </button>
        {/* Mais botões... */}
      </div>
    </div>
  );
};

export default FirebirdManagementPage;
```

---

## Como Adicionar no Menu

**Arquivo:** `frontend/src/App.tsx`

Já existe a estrutura, basta adicionar a rota:

```typescript
// Importar a nova página
import FirebirdManagementPage from './pages/FirebirdManagementPage';

// Adicionar rota (já deve ter estrutura similar)
<Route
  path="/firebird-management"
  element={
    <ProtectedRoute>
      <MainLayout>
        <FirebirdManagementPage />
      </MainLayout>
    </ProtectedRoute>
  }
/>
```

E adicionar item no menu (se for admin):

```typescript
{user?.is_admin && (
  <NavLink to="/firebird-management">
    <Database className="w-5 h-5" />
    Gerenciar Firebird
  </NavLink>
)}
```

---

## Resumo

### Para validação (rápido):
1. Modifique `ExportPage.tsx`
2. Adicione botão "Validar"
3. Chame `/api/export/validate`
4. Mostre modal com resultados

### Para gerenciamento completo:
1. Crie `FirebirdManagementPage.tsx`
2. Adicione rota no `App.tsx`
3. Adicione menu na sidebar
4. Use endpoints:
   - `GET /api/firebird/stats`
   - `POST /api/firebird/clear`
   - `GET /api/firebird/connection-test`

**Quer que eu implemente um deles agora?**
