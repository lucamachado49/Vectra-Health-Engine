import { cn } from '../../lib/utils';

/** Sidebar escura estilo shadcn/ui — estrutura de navegação. */
export function Sidebar({ className, children }) {
  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-slate-900 text-slate-300',
        className,
      )}
    >
      {children}
    </aside>
  );
}

export function SidebarHeader({ children }) {
  return <div className="flex h-16 items-center gap-2.5 border-b border-white/5 px-5">{children}</div>;
}

export function SidebarContent({ children }) {
  return <div className="flex-1 overflow-y-auto px-3 py-4">{children}</div>;
}

export function SidebarFooter({ children }) {
  return <div className="border-t border-white/5 px-3 py-3">{children}</div>;
}

export function SidebarSection({ label, children }) {
  return (
    <div className="mb-4">
      {label && (
        <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
          {label}
        </p>
      )}
      <nav className="space-y-1">{children}</nav>
    </div>
  );
}

export function SidebarItem({ icon: Icon, label, active = false, badge, badgeColor = 'slate', onClick }) {
  const badgeStyles = {
    slate: 'bg-slate-700 text-slate-200',
    blue: 'bg-blue-500/20 text-blue-300',
    rose: 'bg-rose-500/20 text-rose-300',
  };
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
        active
          ? 'bg-blue-600 text-white shadow-sm shadow-blue-900/40'
          : 'text-slate-400 hover:bg-slate-800 hover:text-white',
      )}
    >
      {active && <span className="absolute -left-3 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-blue-400" />}
      {Icon && (
        <Icon
          className={cn(
            'h-[18px] w-[18px] shrink-0',
            active ? 'text-white' : 'text-slate-500 group-hover:text-slate-300',
          )}
        />
      )}
      <span className="flex-1 text-left">{label}</span>
      {badge && (
        <span className={cn('rounded px-1.5 py-0.5 text-[10px] font-bold', badgeStyles[badgeColor])}>{badge}</span>
      )}
    </button>
  );
}
