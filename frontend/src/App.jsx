import { useEffect, useState } from 'react';
import {
  Activity, AlertTriangle, BarChart3, Bell, Check, ChevronDown,
  Home, Map, Moon, Search, Settings, Shield, Zap,
} from 'lucide-react';
import { fetchHealth } from './api/vectraApi.js';
import vectraLogo from './assets/vectra-logo.png';

import VisaoGeral       from './pages/VisaoGeral.jsx';
import MapaDeRisco      from './pages/MapaDeRisco.jsx';
import CentralDeAlertas from './pages/CentralDeAlertas.jsx';
import CopilotPage      from './pages/CopilotPage.jsx';
import AcoesAprovacao   from './pages/AcoesAprovacao.jsx';
import Relatorios       from './pages/Relatorios.jsx';
import Configuracoes    from './pages/Configuracoes.jsx';

const NAV = [
  { id: 'overview',  label: 'Visão Geral',       icon: Home },
  { id: 'map',       label: 'Mapa de Risco',      icon: Map },
  { id: 'alerts',    label: 'Alertas',            icon: AlertTriangle, badge: 'BETA' },
  { id: 'actions',   label: 'Ações e Aprovação',  icon: Shield },
  { id: 'reports',   label: 'Relatórios',         icon: BarChart3 },
  { id: 'copilot',   label: 'Copilot',            icon: Zap, badge: 'BETA' },
  { id: 'settings',  label: 'Configurações',      icon: Settings },
];

const INTEGRATIONS = [
  { name: 'eSUS APS' },
  { name: 'SINAN' },
  { name: 'SIVEP-Gripe' },
  { name: 'IBGE' },
  { name: 'OpenDataSUS' },
];

const PAGE_META = {
  overview: { title: 'Visão Geral',                sub: 'Panorama executivo da situação epidemiológica e climática.' },
  map:      { title: 'Mapa de Risco',              sub: 'Visualize e analise o risco em nível municipal e identifique áreas prioritárias.' },
  alerts:   { title: 'Central de Alertas',         sub: 'Monitore, analise e gerencie alertas sanitários em tempo real.', beta: true },
  actions:  { title: 'Ações e Aprovação',          sub: 'Decisões críticas com apoio da IA. Você tem o controle final.' },
  reports:  { title: 'Análises e Explicabilidade', sub: 'Entenda o desempenho dos modelos, fatores de risco e justificativas por região.' },
  copilot:  { title: 'Assistente de Decisão',      sub: 'Inteligência para decisões em saúde pública com foco, contexto e ação.', beta: true },
  settings: { title: 'Configurações',              sub: 'Gerencie preferências, permissões, integrações e segurança da plataforma.' },
};

export default function App() {
  const [page, setPage]           = useState('map');
  const [apiHealth, setApiHealth] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then(setApiHealth)
      .catch(() => setApiHealth({ status: 'offline', model_loaded: false }));
  }, []);

  const meta = PAGE_META[page] || PAGE_META.overview;

  function renderPage() {
    switch (page) {
      case 'overview': return <VisaoGeral       onNavigate={setPage} />;
      case 'map':      return <MapaDeRisco      />;
      case 'alerts':   return <CentralDeAlertas />;
      case 'copilot':  return <CopilotPage      />;
      case 'actions':  return <AcoesAprovacao   />;
      case 'reports':  return <Relatorios       />;
      case 'settings': return <Configuracoes    />;
      default:
        return (
          <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Settings size={48} style={{ margin: '0 auto 16px', opacity: .2, display: 'block' }} />
            <p style={{ fontSize: 15 }}>Página em desenvolvimento</p>
          </div>
        );
    }
  }

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img className="sidebar-logo-img" src={vectraLogo} alt="Vectra Health" />
          <span className="sidebar-logo-sub">Inteligência Epidemiológica</span>
        </div>

        <nav className="sidebar-nav">
          {NAV.map(({ id, label, icon: Icon, badge }) => (
            <button
              key={id}
              type="button"
              className={`sidebar-nav-item${page === id ? ' active' : ''}`}
              onClick={() => setPage(id)}
            >
              <Icon size={16} />
              {label}
              {badge && <span className="sidebar-badge">{badge}</span>}
            </button>
          ))}

          <div className="sidebar-section-title">Integrações Ativas</div>
          {INTEGRATIONS.map(({ name }) => (
            <div key={name} className="sidebar-integration">
              {name}
              <span className="status-dot active" />
            </div>
          ))}
          <button
            type="button"
            className="sidebar-nav-item"
            style={{ marginTop: 4, fontSize: 12, opacity: .6 }}
            onClick={() => setPage('settings')}
          >
            Ver todas integrações →
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-tagline">
            Dados protegidos e processados com segurança.<br />
            Decisões melhores, vidas protegidas.
          </div>
          <div className="sidebar-theme-toggle">
            <Moon size={14} />
            <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 500 }}>Tema</span>
            <span>Escuro</span>
          </div>
        </div>
      </aside>

      {/* ── Main area ───────────────────────────── */}
      <div className="main-area">
        {/* Topbar principal */}
        <header className="topbar">
          <div className="topbar-page-info">
            <h1>
              {meta.title}
              {meta.beta && <span className="topbar-badge-beta">BETA</span>}
            </h1>
            <p>{meta.sub}</p>
          </div>

          <div className="topbar-search">
            <Search size={14} />
            <input placeholder="Buscar municípios, regiões, alertas..." />
            <kbd>⌘K</kbd>
          </div>

          <div className="topbar-actions">
            <span className="topbar-live-chip">
              <Check size={13} /> Atualizado há 2 min
            </span>
            <button type="button" className="topbar-icon-btn" aria-label="Notificações">
              <Bell size={18} />
              <span className="topbar-notif-badge">2</span>
            </button>
            <div className="topbar-user">
              <div className="topbar-avatar">CR</div>
              <div className="topbar-user-info">
                <strong>Camila Rocha</strong>
                <span>Administradora</span>
              </div>
              <ChevronDown size={15} style={{ color: 'var(--text-muted)' }} />
            </div>
          </div>
        </header>

        {/* Status bar */}
        <div className="topbar-status-bar">
          <span className="live-dot" />
          <span style={{ color: 'var(--green)', fontWeight: 600 }}>Tempo real</span>
          <div className="divider" />
          <Activity size={12} />
          <span>{apiHealth?.model_loaded ? 'Modelo ativo' : 'Demo resiliente'}</span>
          <div className="divider" />
          <span style={{ marginLeft: 'auto', fontSize: 11, opacity: .6 }}>Versão 2.4.1 · Build 2025.05.14</span>
        </div>

        {/* Conteúdo da página */}
        <div className="page-content">{renderPage()}</div>
      </div>
    </div>
  );
}
