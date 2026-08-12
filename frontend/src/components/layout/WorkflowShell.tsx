import { motion } from "framer-motion";
import {
  Braces,
  Check,
  ChevronRight,
  CircleDotDashed,
  FileUp,
  PanelLeftClose,
  PanelLeftOpen,
  ScanSearch,
  Sparkles,
  Target,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import type { Screen } from "../../state";
import logo from "../../assets/autonexus-logo.png";

type Stage = Exclude<Screen, "landing">;

const stages: { screen: Stage; label: string; detail: string; icon: LucideIcon }[] = [
  { screen: "upload", label: "Bring in data", detail: "CSV dataset", icon: FileUp },
  { screen: "target", label: "Set the target", detail: "Prediction objective", icon: Target },
  { screen: "profile", label: "Read the data", detail: "Computed profile", icon: ScanSearch },
  { screen: "strategy", label: "Shape the plan", detail: "ML strategy", icon: Sparkles },
  { screen: "code", label: "Inspect the code", detail: "Validated pipeline", icon: Braces },
];

function stageState(index: number, activeIndex: number, busy: boolean) {
  if (index < activeIndex) return "done";
  if (index === activeIndex) return busy ? "working" : "active";
  return "waiting";
}

export function WorkflowShell({
  activeScreen,
  busy,
  filename,
  availableScreens,
  onNavigate,
  onHome,
  children,
}: {
  activeScreen: Stage;
  busy: boolean;
  filename?: string | null;
  availableScreens: Stage[];
  onNavigate: (screen: Stage) => void;
  onHome: () => void;
  children: ReactNode;
}) {
  const activeIndex = stages.findIndex((stage) => stage.screen === activeScreen);
  const activeStage = stages[activeIndex];
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("automl-sidebar-collapsed") === "true");

  useEffect(() => {
    localStorage.setItem("automl-sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  return (
    <div className={`workspace-shell min-h-screen ${collapsed ? "workspace-shell--collapsed" : ""}`}>
      <aside className="workspace-rail">
        <div className="workspace-rail__top">
          <button type="button" onClick={onHome} className="workspace-brand" aria-label="Return to AutoNexus home" title="AutoNexus home">
            <span className="workspace-brand__mark"><img src={logo} alt="" /></span>
            <span className="workspace-brand__name">AutoNexus</span>
          </button>
          <button
            type="button"
            className="workspace-rail__toggle"
            onClick={() => setCollapsed((value) => !value)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
          </button>
          <p className="workspace-rail__eyebrow">Guided workspace</p>
        </div>

        <nav aria-label="Pipeline stages" className="workspace-stages">
          {stages.map((stage, index) => {
            const Icon = stage.icon;
            const state = stageState(index, activeIndex, busy);
            const selectable = availableScreens.includes(stage.screen);
            const isCurrent = state === "active" || state === "working";
            return (
              <motion.button
                key={stage.screen}
                type="button"
                disabled={!selectable || busy || isCurrent}
                onClick={() => onNavigate(stage.screen)}
                className={`workspace-stage workspace-stage--${state}`}
                title={collapsed ? `${stage.label}: ${stage.detail}` : undefined}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.055, duration: 0.35, ease: "easeOut" }}
              >
                <span className="workspace-stage__line" aria-hidden />
                <span className="workspace-stage__icon">
                  {state === "done" ? <Check className="size-3.5" strokeWidth={2.8} /> : state === "working" ? <CircleDotDashed className="size-4 animate-spin" /> : <Icon className="size-4" />}
                </span>
                <span className="workspace-stage__copy min-w-0 text-left">
                  <span className="workspace-stage__number">0{index + 1}</span>
                  <span className="workspace-stage__label">{stage.label}</span>
                  <span className="workspace-stage__detail">{stage.detail}</span>
                </span>
                {isCurrent ? <ChevronRight className="workspace-stage__arrow ml-auto size-3.5 text-accent" /> : null}
              </motion.button>
            );
          })}
        </nav>

        <div className="workspace-rail__footer">
          <span className="workspace-rail__status-dot" />
          <div>
            <p>Private workspace</p>
            <span>Raw rows stay on this server</span>
          </div>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="workspace-topbar">
          <div className="min-w-0">
            <p className="workspace-topbar__crumb">Workspace <span>/</span> Stage {activeIndex + 1} of {stages.length}</p>
            <p className="truncate font-mono text-[11px] text-text-tertiary">{filename ?? "New analysis"}</p>
          </div>
          <div className="workspace-topbar__state">
            <span className={busy ? "workspace-topbar__pulse" : "workspace-topbar__dot"} />
            {busy ? "Processing" : activeStage.label}
          </div>
        </header>
        <main className="workspace-content">{children}</main>
      </div>
    </div>
  );
}
