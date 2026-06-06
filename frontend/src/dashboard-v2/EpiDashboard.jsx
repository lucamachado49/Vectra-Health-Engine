import { useState } from 'react';
import {
  Card,
  Metric,
  Text,
  BadgeDelta,
  Badge,
  SparkAreaChart,
  AreaChart,
  DonutChart,
  ProgressBar,
} from '@tremor/react';
import {
  LayoutDashboard,
  Map as MapIcon,
  Bell,
  ShieldCheck,
  FileBarChart,
  Bot,
  Settings,
  Search,
  Droplets,
  CloudRain,
  Thermometer,
  Users,
  Building2,
  AlertTriangle,
  ChevronRight,
  Activity,
  ArrowUpRight,
  Megaphone,
  ShieldAlert,
} from 'lucide-react';
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarSection,
  SidebarItem,
} from './components/ui/sidebar';
import { Button } from './components/ui/button';

/* Páginas existentes (reaproveitadas pela navegação) */
import MapaDeRisco from '../pages/MapaDeRisco.jsx';
import CentralDeAlertas from '../pages/CentralDeAlertas.jsx';
import AcoesAprovacao from '../pages/AcoesAprovacao.jsx';
import Relatorios from '../pages/Relatorios.jsx';
import CopilotPage from '../pages/CopilotPage.jsx';
import Configuracoes from '../pages/Configuracoes.jsx';

/* =========================================================================
   MOCK — Surtos de Dengue / NDWI / Chuva Acumulada (Bahia)
   ========================================================================= */

const NAV_PRIMARY = [
  { id: 'overview', label: 'Visão Geral', icon: LayoutDashboard },
  { id: 'map', label: 'Mapa de Risco', icon: MapIcon },
  { id: 'alerts', label: 'Central de Alertas', icon: Bell, badge: '18', badgeColor: 'rose' },
  { id: 'actions', label: 'Ações & Aprovação', icon: ShieldCheck },
  { id: 'reports', label: 'Relatórios', icon: FileBarChart },
  { id: 'copilot', label: 'Copilot', icon: Bot, badge: 'IA', badgeColor: 'blue' },
];
const NAV_SECONDARY = [{ id: 'settings', label: 'Configurações', icon: Settings }];

const PAGE_META = {
  overview: { title: 'Visão Geral', sub: 'Painel de surtos de Dengue · Estado da Bahia' },
  map: { title: 'Mapa de Risco', sub: 'Risco em nível municipal e áreas prioritárias' },
  alerts: { title: 'Central de Alertas', sub: 'Monitore e gerencie alertas sanitários em tempo real' },
  actions: { title: 'Ações & Aprovação', sub: 'Decisões com apoio da IA — você tem o controle final' },
  reports: { title: 'Relatórios', sub: 'Desempenho dos modelos, fatores e explicabilidade' },
  copilot: { title: 'Copilot', sub: 'Assistente de decisão em saúde pública' },
  settings: { title: 'Configurações', sub: 'Preferências, integrações e segurança' },
};

const spark = (vals) => vals.map((v, i) => ({ m: `S${i + 1}`, v }));

const KPIS = [
  {
    title: 'Risco Global — Dengue',
    metric: '86,4',
    suffix: ' /100',
    badge: { label: 'Muito Alto', color: 'rose' },
    delta: '+9,4 pts',
    deltaType: 'increase',
    isIncreasePositive: false,
    sub: 'Percentil nacional: 94º',
    spark: spark([62, 64, 67, 71, 76, 80, 84, 86.4]),
    sparkColor: 'rose',
  },
  {
    title: 'Municípios em Alerta',
    metric: '132',
    suffix: ' / 417',
    badge: { label: '+18 hoje', color: 'amber' },
    delta: '+15,8%',
    deltaType: 'increase',
    isIncreasePositive: false,
    sub: '31,7% do território monitorado',
    spark: spark([78, 84, 90, 99, 108, 117, 126, 132]),
    sparkColor: 'amber',
  },
  {
    title: 'População Afetada',
    metric: '2,8 mi',
    suffix: ' hab.',
    badge: { label: 'Áreas críticas', color: 'rose' },
    delta: '+320 mil',
    deltaType: 'increase',
    isIncreasePositive: false,
    sub: 'em zonas de risco alto/crítico',
    spark: spark([2.1, 2.2, 2.3, 2.45, 2.55, 2.65, 2.72, 2.8]),
    sparkColor: 'rose',
  },
  {
    title: 'Impacto Evitável',
    metric: '42%',
    suffix: '',
    badge: { label: 'Com ação', color: 'emerald' },
    delta: '+7 p.p.',
    deltaType: 'increase',
    isIncreasePositive: true,
    sub: 'dos casos, com ação preventiva',
    spark: spark([31, 33, 34, 36, 38, 39, 41, 42]),
    sparkColor: 'emerald',
  },
  {
    title: 'Confiança do Modelo',
    metric: '92%',
    suffix: '',
    badge: { label: 'Alta', color: 'emerald' },
    delta: '+2 p.p.',
    deltaType: 'increase',
    isIncreasePositive: true,
    sub: 'precisão validada (backtesting)',
    spark: spark([85, 86, 87, 88, 89, 90, 91, 92]),
    sparkColor: 'emerald',
  },
];

const TREND_30D = [
  { data: '15/04', 'Casos Prováveis': 520, 'Índice de Risco': 62 },
  { data: '19/04', 'Casos Prováveis': 610, 'Índice de Risco': 65 },
  { data: '23/04', 'Casos Prováveis': 720, 'Índice de Risco': 69 },
  { data: '27/04', 'Casos Prováveis': 845, 'Índice de Risco': 73 },
  { data: '01/05', 'Casos Prováveis': 980, 'Índice de Risco': 77 },
  { data: '05/05', 'Casos Prováveis': 1075, 'Índice de Risco': 80 },
  { data: '09/05', 'Casos Prováveis': 1180, 'Índice de Risco': 83 },
  { data: '14/05', 'Casos Prováveis': 1280, 'Índice de Risco': 86 },
];

const RISK_DISTRIBUTION = [
  { name: 'Muito Alto', value: 132 },
  { name: 'Alto', value: 121 },
  { name: 'Moderado', value: 100 },
  { name: 'Baixo', value: 52 },
  { name: 'Muito Baixo', value: 12 },
];

const RISK_FACTORS = [
  { name: 'Chuva acumulada (7 dias)', value: '142 mm', level: 88, color: 'rose', impact: 'Alto', icon: CloudRain, note: '+56 mm vs. semana anterior' },
  { name: 'NDWI — índice de água', value: '0,41', level: 92, color: 'rose', impact: 'Muito Alto', icon: Droplets, note: 'água superficial → criadouros' },
  { name: 'Temperatura da superfície', value: '28,6 °C', level: 64, color: 'amber', impact: 'Médio', icon: Thermometer, note: 'faixa ótima de proliferação do vetor' },
  { name: 'Densidade populacional', value: '+5%', level: 58, color: 'amber', impact: 'Médio', icon: Users, note: 'exposição elevada em área urbana' },
];

const TOP_REGIONS = [
  { name: 'Salvador', score: 92, casos: '1.240', level: 'critico' },
  { name: 'Feira de Santana', score: 90, casos: '780', level: 'critico' },
  { name: 'Vitória da Conquista', score: 85, casos: '410', level: 'alto' },
  { name: 'Ilhéus', score: 82, casos: '300', level: 'alto' },
  { name: 'Itabuna', score: 78, casos: '260', level: 'alto' },
];

const RECENT_ALERTS = [
  { title: 'Surto de dengue em expansão', region: 'Salvador, Lauro de Freitas +3', time: '5 min', level: 'critico' },
  { title: 'Chuva acima da média prevista', region: 'Recôncavo Baiano', time: '22 min', level: 'alto' },
  { title: 'NDWI cruzou o limiar de risco', region: 'Feira de Santana e entorno', time: '1 h', level: 'alto' },
  { title: 'Aumento de casos prováveis', region: 'Sul da Bahia', time: '2 h', level: 'medio' },
];

const RECOMMENDED_ACTIONS = [
  { title: 'Intensificar bloqueio vetorial', scope: '12 municípios críticos', priority: 'Alta', icon: ShieldAlert },
  { title: 'Mobilizar equipes de campo', scope: 'Salvador e Região Metropolitana', priority: 'Alta', icon: Users },
  { title: 'Mutirão de eliminação de criadouros', scope: 'áreas com NDWI elevado', priority: 'Média', icon: Droplets },
  { title: 'Comunicação de risco à população', scope: 'rede municipal de saúde', priority: 'Média', icon: Megaphone },
];

const LEVEL = {
  critico: { color: 'rose', dot: 'bg-rose-500' },
  alto: { color: 'rose', dot: 'bg-rose-400' },
  medio: { color: 'amber', dot: 'bg-amber-500' },
  baixo: { color: 'emerald', dot: 'bg-emerald-500' },
};
const PRIORITY = { Alta: 'rose', Média: 'amber', Baixa: 'emerald' };

const cardCls = 'rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg shadow-black/20 ring-0';
const intFmt = (n) => Intl.NumberFormat('pt-BR').format(n);

/* =========================================================================
   SUB-COMPONENTES
   ========================================================================= */

function KpiCard({ kpi }) {
  return (
    <Card className={cardCls}>
      <div className="flex items-start justify-between gap-2">
        <Text className="text-xs font-medium text-slate-400">{kpi.title}</Text>
        <Badge color={kpi.badge.color} size="xs" className="rounded-md">
          {kpi.badge.label}
        </Badge>
      </div>
      <div className="mt-2 flex items-baseline gap-1">
        <Metric className="text-slate-50">{kpi.metric}</Metric>
        {kpi.suffix && <span className="text-sm font-medium text-slate-500">{kpi.suffix}</span>}
      </div>
      <SparkAreaChart
        data={kpi.spark}
        categories={['v']}
        index="m"
        colors={[kpi.sparkColor]}
        className="mt-3 h-9 w-full"
        showGradient
      />
      <div className="mt-3 flex items-center justify-between border-t border-slate-800 pt-2.5">
        <BadgeDelta deltaType={kpi.deltaType} isIncreasePositive={kpi.isIncreasePositive} size="xs">
          {kpi.delta}
        </BadgeDelta>
        <span className="text-[11px] text-slate-500">{kpi.sub}</span>
      </div>
    </Card>
  );
}

function SectionTitle({ icon: Icon, title, subtitle, action }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div className="flex items-center gap-2.5">
        {Icon && (
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-800 text-slate-300">
            <Icon className="h-4 w-4" />
          </span>
        )}
        <div>
          <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

/* =========================================================================
   CONTEÚDO — Visão Geral (Tremor)
   ========================================================================= */

function OverviewContent() {
  const donutColors = ['rose', 'orange', 'amber', 'emerald', 'teal'];
  const legendDot = ['bg-rose-500', 'bg-orange-500', 'bg-amber-500', 'bg-emerald-500', 'bg-teal-500'];
  const total = RISK_DISTRIBUTION.reduce((a, b) => a + b.value, 0);

  return (
    <div className="space-y-6 p-6">
      {/* KPIs */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {KPIS.map((kpi) => (
          <KpiCard key={kpi.title} kpi={kpi} />
        ))}
      </section>

      {/* Tendência + Distribuição */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className={`${cardCls} lg:col-span-2`}>
          <SectionTitle
            icon={Activity}
            title="Casos prováveis de dengue — últimos 30 dias"
            subtitle="Notificações estimadas e índice de risco integrado"
            action={
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-rose-500" /> Casos Prováveis
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-amber-500" /> Índice de Risco
                </span>
              </div>
            }
          />
          <AreaChart
            data={TREND_30D}
            index="data"
            categories={['Casos Prováveis', 'Índice de Risco']}
            colors={['rose', 'amber']}
            valueFormatter={intFmt}
            showLegend={false}
            showGradient
            yAxisWidth={44}
            className="h-72"
          />
        </Card>

        <Card className={cardCls}>
          <SectionTitle icon={ShieldAlert} title="Distribuição do risco" subtitle="417 municípios monitorados" />
          <DonutChart
            data={RISK_DISTRIBUTION}
            category="value"
            index="name"
            colors={donutColors}
            valueFormatter={intFmt}
            className="mx-auto h-44"
            showLabel
          />
          <div className="mt-4 space-y-2">
            {RISK_DISTRIBUTION.map((d, i) => (
              <div key={d.name} className="flex items-center gap-2 text-xs">
                <span className={`h-2.5 w-2.5 rounded-sm ${legendDot[i]}`} />
                <span className="flex-1 text-slate-300">{d.name}</span>
                <span className="font-semibold text-slate-100">{d.value}</span>
                <span className="w-10 text-right text-slate-500">{Math.round((d.value / total) * 100)}%</span>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* Fatores + Regiões */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className={cardCls}>
          <SectionTitle icon={CloudRain} title="Por que o risco está alto?" subtitle="Principais fatores ambientais e climáticos" />
          <div className="space-y-4">
            {RISK_FACTORS.map((f) => {
              const Icon = f.icon;
              return (
                <div key={f.name}>
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-800 text-slate-400">
                        <Icon className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="text-sm font-medium text-slate-200">{f.name}</p>
                        <p className="text-xs text-slate-500">{f.note}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-100">{f.value}</p>
                      <Badge color={f.color} size="xs" className="rounded-md">
                        {f.impact}
                      </Badge>
                    </div>
                  </div>
                  <ProgressBar value={f.level} color={f.color} className="mt-2" />
                </div>
              );
            })}
          </div>
        </Card>

        <Card className={cardCls}>
          <SectionTitle
            icon={Building2}
            title="Principais regiões em atenção"
            subtitle="Ranking por índice de risco previsto"
            action={
              <Button variant="ghost" size="sm" className="text-blue-400 hover:bg-slate-800">
                Ver mapa <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            }
          />
          <div className="space-y-3">
            {TOP_REGIONS.map((r, i) => (
              <div key={r.name} className="flex items-center gap-3">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-slate-800 text-xs font-bold text-slate-400">
                  {i + 1}
                </span>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-200">{r.name}</p>
                    <span className="text-xs text-slate-500">{r.casos} casos</span>
                  </div>
                  <ProgressBar value={r.score} color={LEVEL[r.level].color} className="mt-1.5" />
                </div>
                <Badge color={LEVEL[r.level].color} size="xs" className="w-12 justify-center rounded-md tabular-nums">
                  {(r.score / 10).toFixed(1)}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* Alertas + Ações */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className={cardCls}>
          <SectionTitle icon={AlertTriangle} title="Alertas recentes" subtitle="Eventos detectados em tempo real" />
          <div className="divide-y divide-slate-800">
            {RECENT_ALERTS.map((a) => (
              <div key={a.title} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${LEVEL[a.level].dot}`} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-200">{a.title}</p>
                  <p className="text-xs text-slate-500">{a.region}</p>
                </div>
                <span className="whitespace-nowrap text-[11px] text-slate-500">{a.time}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className={cardCls}>
          <SectionTitle icon={ShieldCheck} title="Ações recomendadas para hoje" subtitle="Geradas pelo agente, sujeitas à aprovação humana" />
          <div className="space-y-2.5">
            {RECOMMENDED_ACTIONS.map((act) => {
              const Icon = act.icon;
              return (
                <div
                  key={act.title}
                  className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-800/40 p-3 transition-colors hover:border-slate-700 hover:bg-slate-800"
                >
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-900 text-blue-400 shadow-sm ring-1 ring-slate-700">
                    <Icon className="h-[18px] w-[18px]" />
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-200">{act.title}</p>
                    <p className="text-xs text-slate-500">{act.scope}</p>
                  </div>
                  <Badge color={PRIORITY[act.priority]} size="xs" className="rounded-md">
                    {act.priority}
                  </Badge>
                </div>
              );
            })}
          </div>
          <Button variant="primary" className="mt-4 w-full">
            Revisar plano de ação <ArrowUpRight className="h-4 w-4" />
          </Button>
        </Card>
      </section>

      <p className="pt-2 text-center text-xs text-slate-600">
        Vectra Health · Inteligência Epidemiológica — dados de demonstração (Dengue / Bahia)
      </p>
    </div>
  );
}

/* =========================================================================
   APP SHELL (escuro)
   ========================================================================= */

export default function EpiDashboard() {
  const [page, setPage] = useState('overview');
  const meta = PAGE_META[page] || PAGE_META.overview;

  function renderPage() {
    switch (page) {
      case 'overview':
        return <OverviewContent />;
      case 'map':
        return <div className="page-content">{<MapaDeRisco />}</div>;
      case 'alerts':
        return <div className="page-content">{<CentralDeAlertas />}</div>;
      case 'actions':
        return <div className="page-content">{<AcoesAprovacao />}</div>;
      case 'reports':
        return <div className="page-content">{<Relatorios />}</div>;
      case 'copilot':
        return <div className="page-content">{<CopilotPage />}</div>;
      case 'settings':
        return <div className="page-content">{<Configuracoes />}</div>;
      default:
        return <OverviewContent />;
    }
  }

  return (
    <div className="dark flex h-screen overflow-hidden bg-slate-950 font-sans text-slate-100">
      {/* Sidebar */}
      <Sidebar>
        <SidebarHeader>
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-blue-600 text-white">
            <Activity className="h-[18px] w-[18px]" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-bold tracking-wide text-white">VECTRA</p>
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-500">
              Inteligência Epidemiológica
            </p>
          </div>
        </SidebarHeader>

        <SidebarContent>
          <SidebarSection label="Operação">
            {NAV_PRIMARY.map((item) => (
              <SidebarItem
                key={item.id}
                icon={item.icon}
                label={item.label}
                badge={item.badge}
                badgeColor={item.badgeColor}
                active={page === item.id}
                onClick={() => setPage(item.id)}
              />
            ))}
          </SidebarSection>
          <SidebarSection label="Sistema">
            {NAV_SECONDARY.map((item) => (
              <SidebarItem
                key={item.id}
                icon={item.icon}
                label={item.label}
                active={page === item.id}
                onClick={() => setPage(item.id)}
              />
            ))}
          </SidebarSection>
        </SidebarContent>

        <SidebarFooter>
          <div className="flex items-center gap-2 rounded-lg bg-slate-800/60 px-3 py-2.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            <div className="leading-tight">
              <p className="text-xs font-medium text-slate-200">Modelo ativo</p>
              <p className="text-[10px] text-slate-500">Atualizado há 2 min</p>
            </div>
          </div>
        </SidebarFooter>
      </Sidebar>

      {/* Área principal */}
      <div className="flex flex-1 flex-col pl-64">
        {/* Top navigation — sem avatar/perfil, só busca + notificações */}
        <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-slate-800 bg-slate-900/80 px-6 backdrop-blur">
          <div>
            <h1 className="text-lg font-semibold leading-tight text-slate-100">{meta.title}</h1>
            <p className="text-xs text-slate-500">{meta.sub}</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="relative hidden md:block">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Buscar municípios, alertas, indicadores…"
                className="h-9 w-80 rounded-lg border border-slate-700 bg-slate-800 pl-9 pr-3 text-sm text-slate-200 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
              />
            </div>
            <Button
              variant="outline"
              size="icon"
              className="relative border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
              aria-label="Notificações"
            >
              <Bell className="h-[18px] w-[18px]" />
              <span className="absolute -right-1 -top-1 grid h-4 w-4 place-items-center rounded-full bg-rose-600 text-[10px] font-bold text-white">
                3
              </span>
            </Button>
          </div>
        </header>

        {/* Conteúdo */}
        <main className="flex min-h-0 flex-1 flex-col overflow-y-auto">{renderPage()}</main>
      </div>
    </div>
  );
}
