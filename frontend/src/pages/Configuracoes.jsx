import { useState } from 'react';
import {
  Activity, ChevronRight, Database, Edit3, Fingerprint, Globe, KeyRound,
  Mail, MapPin, Phone, Plus, Shield, ShieldCheck, Clock,
} from 'lucide-react';

/* Switch on/off */
function Toggle({ on }) {
  const [v, setV] = useState(on);
  return (
    <button
      type="button"
      onClick={() => setV(!v)}
      style={{
        width: 38, height: 22, borderRadius: 12, flexShrink: 0,
        background: v ? '#22c55e' : 'rgba(148,163,184,.25)',
        position: 'relative', transition: 'background .18s',
      }}
    >
      <span style={{
        position: 'absolute', top: 2, left: v ? 18 : 2, width: 18, height: 18, borderRadius: '50%',
        background: '#fff', transition: 'left .18s', boxShadow: '0 1px 3px rgba(0,0,0,.4)',
      }} />
    </button>
  );
}

function CardBox({ icon: Icon, title, footer, children, style }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', ...style }}>
      <div className="card-header" style={{ paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
        <h3>{Icon && <Icon size={15} style={{ color: 'var(--blue)' }} />} {title}</h3>
      </div>
      <div className="card-body" style={{ flex: 1, paddingTop: 14 }}>{children}</div>
      {footer && (
        <div style={{ padding: '0 20px 16px' }}>
          <span className="inline-link">{footer} <ChevronRight size={13} /></span>
        </div>
      )}
    </div>
  );
}

/* Linha label + valor à direita */
function Line({ icon: Icon, label, sub, right }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 0', borderBottom: '1px solid var(--border-soft)' }}>
      {Icon && <Icon size={15} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{label}</div>
        {sub && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{sub}</div>}
      </div>
      {right}
    </div>
  );
}

const THRESHOLDS = [
  ['Muito Alto', '#f43f5e', '≥ 75'],
  ['Alto', '#f97316', '50 – 74'],
  ['Moderado', '#facc15', '25 – 49'],
  ['Baixo', '#4ade80', '10 – 24'],
  ['Muito Baixo', '#22c55e', '< 10'],
];

const INTEGRATIONS = [
  ['INMET', 'Instituto Nacional de Meteorologia', '15/05/2025 09:41'],
  ['CEMADEN', 'Centro Nacional de Monitoramento', '15/05/2025 09:40'],
  ['DATASUS', 'Departamento de Informática do SUS', '15/05/2025 09:39'],
  ['IBGE', 'Instituto Brasileiro de Geografia', '15/05/2025 09:38'],
  ['NASA EarthData', 'NASA Earth Observing System', '15/05/2025 09:37'],
];

const TOKENS = [
  ['API Dashboard', 'Leitura · Municípios · Alertas', 'Criado em 02/05/2025'],
  ['Integração Externa', 'Leitura · Relatórios · Indicadores', 'Criado em 18/04/2025'],
  ['Webhook Alertas', 'Leitura · Alertas', 'Criado em 10/04/2025'],
];

const ACCENTS = ['#3b82f6', '#0ea5e9', '#22c55e', '#8b5cf6', '#f97316', '#f43f5e'];

export default function Configuracoes() {
  const [accent, setAccent] = useState('#3b82f6');
  const [theme, setTheme] = useState('Escuro');
  const [density, setDensity] = useState('Padrão');

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <button type="button" className="btn btn-primary">Salvar alterações</button>
      </div>

      {/* Linha 1 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, alignItems: 'start', marginBottom: 16 }}>
        <CardBox icon={Shield} title="Perfil do usuário" footer="Editar perfil">
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 14 }}>
            <div className="topbar-avatar" style={{ width: 56, height: 56, fontSize: 18 }}>CR</div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Camila Rocha</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Administradora</div>
            </div>
          </div>
          <Line icon={Mail} label="camila.rocha@vectra.com.br" />
          <Line icon={Phone} label="+55 (71) 99999-1234" />
          <Line icon={MapPin} label="America/Sao_Paulo (UTC-3)" />
          <Line icon={Clock} label="Último acesso: 15/05/2025 09:42" />
        </CardBox>

        <CardBox icon={ShieldCheck} title="Permissões e papéis" footer="Gerenciar usuários e papéis">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, fontSize: 13 }}>
            <span style={{ color: 'var(--text-muted)' }}>Papel atual</span>
            <span className="risk-badge" style={{ background: 'var(--blue-light)', color: '#93c5fd', border: '1px solid rgba(59,130,246,.3)' }}>Administradora</span>
          </div>
          {[
            ['Acesso completo à plataforma', 'Visualize e edite todas as funcionalidades.'],
            ['Gerenciar usuários e papéis', 'Crie, edite e remova usuários e permissões.'],
            ['Gerenciar integrações e APIs', 'Configure integrações, tokens e webhooks.'],
            ['Auditoria e conformidade', 'Acesse logs, auditorias e relatórios.'],
          ].map(([l, s]) => <Line key={l} label={l} sub={s} />)}
        </CardBox>

        <CardBox icon={Activity} title="Preferências de notificação" footer="Gerenciar contatos">
          {[
            ['Alertas críticos', 'Notificações para riscos muito altos', true],
            ['Alertas importantes', 'Notificações para riscos altos', true],
            ['Relatórios diários', 'Resumo diário de indicadores', false],
            ['Boletins semanais', 'Resumo semanal de tendências', true],
            ['Atualizações da plataforma', 'Novidades e comunicados', false],
          ].map(([l, s, on]) => <Line key={l} label={l} sub={s} right={<Toggle on={on} />} />)}
        </CardBox>

        <CardBox icon={Activity} title="Limiares de alerta" footer="Editar limiares">
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>Limiares usados para classificação de risco.</div>
          {THRESHOLDS.map(([l, c, range]) => (
            <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 0', borderBottom: '1px solid var(--border-soft)' }}>
              <span style={{ width: 9, height: 9, borderRadius: '50%', background: c, flexShrink: 0 }} />
              <span style={{ flex: 1, fontSize: 13, fontWeight: 600 }}>{l}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', padding: '4px 10px', borderRadius: 7, background: 'var(--bg-inset)', border: '1px solid var(--border)' }}>{range}</span>
            </div>
          ))}
        </CardBox>
      </div>

      {/* Linha 2 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, alignItems: 'start', marginBottom: 16 }}>
        <CardBox icon={Database} title="Integrações ativas" footer="Gerenciar todas as integrações">
          {INTEGRATIONS.map(([name, desc, sync]) => (
            <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 0', borderBottom: '1px solid var(--border-soft)' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{desc}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600, color: 'var(--green)' }}>
                  <span className="status-dot active" style={{ margin: 0 }} /> Ativo
                </span>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{sync}</div>
              </div>
              <span className="inline-link" style={{ fontSize: 11 }}>Configurar</span>
            </div>
          ))}
        </CardBox>

        <CardBox icon={KeyRound} title="APIs e tokens" footer="Gerenciar APIs e tokens">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Tokens ativos</span>
            <button type="button" className="btn btn-secondary btn-sm"><Plus size={12} /> Gerar novo token</button>
          </div>
          {TOKENS.map(([name, scope, when]) => (
            <div key={name} style={{ padding: '10px 12px', borderRadius: 9, background: 'var(--bg-inset)', border: '1px solid var(--border)', marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 700 }}>{name}</span>
                <span className="risk-badge baixo" style={{ fontSize: 9 }}>Ativo</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', margin: '3px 0' }}>{scope}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{when}</div>
            </div>
          ))}
        </CardBox>

        <CardBox icon={ShieldCheck} title="Governança e auditoria" footer="Acessar centro de governança">
          <Line label="Logs de auditoria" sub="Visualize atividades e alterações" right={<ChevronRight size={15} style={{ color: 'var(--text-muted)' }} />} />
          <Line label="Exportar relatórios de auditoria" sub="Relatórios para compliance" right={<ChevronRight size={15} style={{ color: 'var(--text-muted)' }} />} />
          <Line label="Retenção de dados" sub="Política atual: 24 meses" right={<span className="risk-badge" style={{ background: 'var(--bg-inset)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>24 meses</span>} />
          <Line label="Classificação de dados" sub="Dados sensíveis e críticos" right={<span className="risk-badge baixo" style={{ fontSize: 9 }}>Ativo</span>} />
        </CardBox>
      </div>

      {/* Linha 3 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, alignItems: 'start' }}>
        <CardBox icon={Activity} title="Preferências de tema">
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8 }}>Tema da interface</div>
          <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
            {['Escuro', 'Claro', 'Sistema'].map((t) => (
              <button key={t} type="button" onClick={() => setTheme(t)} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{
                  height: 48, borderRadius: 8, marginBottom: 6,
                  background: t === 'Claro' ? '#e2e8f0' : t === 'Sistema' ? 'linear-gradient(90deg,#0e1520 50%,#e2e8f0 50%)' : '#0e1520',
                  border: theme === t ? `2px solid ${accent}` : '1px solid var(--border)',
                  boxShadow: theme === t ? `0 0 0 3px ${accent}33` : 'none',
                }} />
                <span style={{ fontSize: 12, fontWeight: theme === t ? 700 : 500, color: theme === t ? accent : 'var(--text-secondary)' }}>{t}</span>
              </button>
            ))}
          </div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8 }}>Cor de destaque</div>
          <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
            {ACCENTS.map((c) => (
              <button key={c} type="button" onClick={() => setAccent(c)} style={{
                width: 26, height: 26, borderRadius: '50%', background: c,
                boxShadow: accent === c ? `0 0 0 2px var(--bg-card), 0 0 0 4px ${c}` : 'none',
              }} />
            ))}
          </div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8 }}>Densidade da interface</div>
          <div style={{ display: 'flex', gap: 16 }}>
            {['Padrão', 'Compacta'].map((d) => (
              <label key={d} onClick={() => setDensity(d)} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: 'var(--text-secondary)' }}>
                <span style={{ width: 15, height: 15, borderRadius: '50%', border: `2px solid ${density === d ? accent : 'var(--border-strong)'}`, display: 'grid', placeItems: 'center' }}>
                  {density === d && <span style={{ width: 7, height: 7, borderRadius: '50%', background: accent }} />}
                </span>
                {d}
              </label>
            ))}
          </div>
        </CardBox>

        <CardBox icon={Fingerprint} title="Segurança da conta">
          <Line icon={ShieldCheck} label="Autenticação de dois fatores (2FA)" sub="Proteja sua conta com uma camada extra" right={<Toggle on />} />
          <Line icon={Activity} label="Sessões ativas" sub="Dispositivos conectados à sua conta" right={<span style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>3 ativas <ChevronRight size={14} /></span>} />
          <Line icon={KeyRound} label="Alterar senha" sub="Atualize sua senha regularmente" right={<ChevronRight size={15} style={{ color: 'var(--text-muted)' }} />} />
          <Line icon={Shield} label="Política de senha" sub="Senha forte · Expiração: 90 dias" right={<span className="risk-badge baixo" style={{ fontSize: 9 }}>Ativo</span>} />
        </CardBox>

        <CardBox icon={Globe} title="Configurações da plataforma" footer="Outras configurações avançadas">
          {[
            ['Idioma', 'Português (Brasil)'],
            ['Fuso horário', 'America/Sao_Paulo (UTC-3)'],
            ['Unidade de medida', 'Métrico (°C, mm, km/h)'],
            ['Formato de data', 'dd/mm/aaaa'],
          ].map(([k, v]) => (
            <div key={k} style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{k}</div>
              <select className="filter-select"><option>{v}</option></select>
            </div>
          ))}
        </CardBox>
      </div>

      <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-muted)', marginTop: 24 }}>
        © 2025 Vectra. Todos os direitos reservados. • Versão 2.4.1
      </div>
    </>
  );
}
