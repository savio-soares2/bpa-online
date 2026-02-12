import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Download,
  LogOut,
  TrendingUp,
  Shield,
  Database,
  Printer,
  BookOpen,
  Users,
  Building2
} from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import BPAIndividualizadoPage from './pages/BPAIndividualizadoPage';
import ExportPage from './pages/ExportPage';
import JuliaImportPage from './pages/JuliaImportPage';
import AdminPage from './pages/AdminPage';
import BpaConsolidadoPage from './pages/BpaConsolidadoPage';
import DataManagementPage from './pages/DataManagementPage';
import ReportsPage from './pages/ReportsPage';
import SigtapPage from './pages/SigtapPage';
import UnidadesListPage from './pages/UnidadesListPage';
import UnidadeDetalhePage from './pages/UnidadeDetalhePage';

// Componente de rota protegida
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Layout principal com sidebar
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 shadow-sm flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-primary-600">BPA Online</h1>
          <p className="text-sm text-gray-500">Sistema de Produção Ambulatorial</p>
        </div>

        <nav className="p-4 flex-1 flex flex-col">
          {/* Menu Principal - todos os usuários */}
          <ul className="space-y-2">
            <li>
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                <LayoutDashboard className="w-5 h-5" />
                Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/bpa-i"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                <FileText className="w-5 h-5" />
                BPA Individualizado
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/bpa-c"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                <TrendingUp className="w-5 h-5" />
                BPA Consolidado
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/reports"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                <Printer className="w-5 h-5" />
                Relatórios BPA
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/sigtap"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                <BookOpen className="w-5 h-5" />
                Gestão SIGTAP
              </NavLink>
            </li>
          </ul>

          {/* Menu Admin - apenas administradores */}
          {user?.is_admin && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <p className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Administração
              </p>
              <ul className="space-y-2">
                <li>
                  <NavLink
                    to="/biserver"
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                        ? 'bg-primary-50 text-primary-600 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                      }`
                    }
                  >
                    <Database className="w-5 h-5" />
                    Gerenciar Dados
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/export"
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                        ? 'bg-primary-50 text-primary-600 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                      }`
                    }
                  >
                    <Download className="w-5 h-5" />
                    Exportar Firebird
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/admin/unidades"
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                        ? 'bg-purple-50 text-purple-600 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                      }`
                    }
                  >
                    <Building2 className="w-5 h-5" />
                    Unidades
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/admin/usuarios"
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                        ? 'bg-purple-50 text-purple-600 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                      }`
                    }
                  >
                    <Users className="w-5 h-5" />
                    Usuários
                  </NavLink>
                </li>
              </ul>
            </div>
          )}
        </nav>

        {/* Usuário logado */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="mb-3">
            <p className="text-sm font-medium text-gray-800">{user?.nome}</p>
            <p className="text-xs text-gray-500">
              {user?.is_admin ? 'Administrador' : `CNES: ${user?.cnes}`}
            </p>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-gray-600 hover:text-danger-600 hover:bg-danger-50 rounded-lg transition-colors text-sm"
          >
            <LogOut className="w-4 h-4" />
            Sair
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
};



const AppRoutes: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <Routes>
      {/* Rota pública - Login */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />

      {/* Rotas protegidas */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout>
              <Dashboard />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/bpa-i"
        element={
          <ProtectedRoute>
            <MainLayout>
              <BPAIndividualizadoPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/bpa-c"
        element={
          <ProtectedRoute>
            <MainLayout>
              <BpaConsolidadoPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <MainLayout>
              <ReportsPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/sigtap"
        element={
          <ProtectedRoute>
            <MainLayout>
              <SigtapPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/export"
        element={
          <ProtectedRoute>
            <MainLayout>
              <ExportPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/julia"
        element={
          <ProtectedRoute>
            <MainLayout>
              <JuliaImportPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/biserver"
        element={
          <ProtectedRoute>
            <MainLayout>
              <DataManagementPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />



      {/* Rotas Admin */}
      <Route
        path="/admin"
        element={<Navigate to="/admin/unidades" replace />}
      />
      <Route
        path="/admin/unidades"
        element={
          <ProtectedRoute>
            <MainLayout>
              <UnidadesListPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/unidades/:cnes"
        element={
          <ProtectedRoute>
            <MainLayout>
              <UnidadeDetalhePage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/usuarios"
        element={
          <ProtectedRoute>
            <MainLayout>
              <AdminPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />

      {/* Redirect para login se rota não encontrada */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
};

export default App;
