import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Braces,
  Check,
  FileSpreadsheet,
  ScanSearch,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import logo from "../assets/autonexus-logo.png";

const reveal = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0 },
};

const features = [
  {
    icon: ScanSearch,
    title: "Know the shape of your data",
    body: "Types, missing values, cardinality, imbalance, and leakage signals are computed locally before a plan is made.",
  },
  {
    icon: Workflow,
    title: "Get an explainable ML strategy",
    body: "Review preprocessing choices, candidate models, and the evaluation approach before you receive a line of code.",
  },
  {
    icon: ShieldCheck,
    title: "Inspect code with confidence",
    body: "Every generated pipeline is statically checked. Your data is never sent to the model and code is never executed here.",
  },
];

function PipelinePreview() {
  const reduceMotion = useReducedMotion();
  const flow = reduceMotion ? undefined : { duration: 2.6, repeat: Infinity, ease: "easeInOut" as const };

  return (
    <motion.div
      className="landing-console relative overflow-hidden rounded-[1.5rem] border border-white/[0.09] p-3 sm:p-4"
      initial={{ opacity: 0, scale: 0.96, y: 24 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="landing-console__glow" aria-hidden />
      <div className="relative overflow-hidden rounded-xl border border-white/[0.08] bg-[#0b0d13]/90">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-3 sm:px-5">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-[#ff6258]" />
            <span className="size-2 rounded-full bg-[#ffbd2e]" />
            <span className="size-2 rounded-full bg-[#28c840]" />
            <span className="ml-2 font-mono text-[10px] text-white/35">analysis.workspace</span>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-cyan-200/70">Ready</span>
        </div>

        <div className="grid min-h-[23rem] gap-px bg-white/[0.06] md:grid-cols-[1.08fr_0.92fr]">
          <div className="relative overflow-hidden bg-[#0d1018] p-5 sm:p-7">
            <div className="absolute inset-0 landing-grid opacity-30" aria-hidden />
            <div className="relative">
              <div className="flex items-center justify-between gap-3">
                <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-white/35">Your workflow</p>
                <span className="rounded-full border border-white/[0.08] px-2 py-1 font-mono text-[9px] uppercase tracking-[0.1em] text-white/35">Example</span>
              </div>
              <div className="mt-6 space-y-2.5">
                {[
                  [FileSpreadsheet, "Map the dataset", "Types, gaps, and shape"],
                  [ScanSearch, "Understand the target", "Task and metric selection"],
                  [Braces, "Review the pipeline", "Readable Python, static checks"],
                ].map(([Icon, label, detail], index) => (
                  <motion.div
                    key={label as string}
                    className="relative flex items-center gap-3 rounded-lg border border-white/[0.08] bg-white/[0.035] px-3 py-3 backdrop-blur-sm"
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.13, duration: 0.45 }}
                  >
                    <div className="flex size-8 items-center justify-center rounded-md border border-cyan-300/15 bg-cyan-300/[0.08] text-cyan-200">
                      <Icon className="size-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white/90">{label as string}</p>
                      <p className="mt-0.5 font-mono text-[10px] text-white/38">{detail as string}</p>
                    </div>
                    <motion.span
                      className="ml-auto size-2 rounded-full bg-cyan-300"
                      animate={reduceMotion ? undefined : { opacity: [0.35, 1, 0.35], scale: [0.8, 1.15, 0.8] }}
                      transition={flow}
                    />
                  </motion.div>
                ))}
              </div>
              <div className="landing-preview-facts mt-6 grid grid-cols-3 gap-2 border-t border-white/[0.07] pt-4">
                {[
                  ["Column types", "Detected"],
                  ["Data quality", "Flagged"],
                  ["Metric", "Selected"],
                ].map(([label, value]) => (
                  <div key={label} className="landing-preview-fact">
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[#111520] p-5 sm:p-7">
            <div className="flex items-center justify-between">
              <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-white/35">Before you run it</p>
              <ShieldCheck className="size-4 text-emerald-300" />
            </div>
            <p className="mt-4 max-w-[24ch] text-sm leading-relaxed text-white/55">A strategy is useful when you can see what it is based on.</p>
            <div className="mt-6 space-y-3">
              {[
                "Safe imports only",
                "Known columns referenced",
                "Target is preserved",
                "Pipeline structure checked",
              ].map((check, index) => (
                <motion.div
                  key={check}
                  className="flex items-center gap-3"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.92 + index * 0.12, duration: 0.36 }}
                >
                  <span className="flex size-5 items-center justify-center rounded-full border border-emerald-300/20 bg-emerald-300/10 text-emerald-200">
                    <Check className="size-3" strokeWidth={2.5} />
                  </span>
                  <span className="text-sm text-white/70">{check}</span>
                </motion.div>
              ))}
            </div>
            <div className="mt-7 rounded-lg border border-white/[0.1] bg-white/[0.035] p-4">
              <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-white/40">A clear boundary</p>
              <p className="mt-2 text-sm leading-relaxed text-white/65">Your CSV stays on this server. Generated code is yours to inspect and run in your own environment.</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export function LandingScreen({ onStart }: { onStart: () => void }) {
  const heroTransition = { duration: 0.72, ease: "easeOut" as const };

  return (
    <div className="landing-page overflow-hidden">
      <div className="landing-orb landing-orb--one" aria-hidden />
      <div className="landing-orb landing-orb--two" aria-hidden />
      <header className="relative mx-auto flex h-20 max-w-[78rem] items-center justify-between px-6 sm:px-8">
        <button type="button" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} className="group flex items-center gap-2 text-left">
          <span className="landing-brand-mark">
            <img src={logo} alt="" />
          </span>
          <span className="text-[15px] font-semibold tracking-[-0.03em] text-white">AutoNexus</span>
        </button>
        <p className="hidden font-mono text-[10px] uppercase tracking-[0.12em] text-white/35 sm:block">Private by design</p>
      </header>

      <main>
        <section className="relative mx-auto grid max-w-[78rem] gap-12 px-6 pb-20 pt-16 sm:px-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-center lg:pb-28 lg:pt-24">
          <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.1 } } }}>
            <motion.div variants={reveal} transition={heroTransition} className="landing-kicker">
              <span className="landing-kicker__dot" /> A considered start for every dataset
            </motion.div>
            <motion.h1 variants={reveal} transition={heroTransition} className="landing-title mt-6">
              From CSV to a pipeline you can <span>actually understand.</span>
            </motion.h1>
            <motion.p variants={reveal} transition={heroTransition} className="mt-6 max-w-xl text-[1.05rem] leading-8 text-white/56 sm:text-lg">
              AutoNexus maps your data, recommends a grounded ML strategy, and writes a validated scikit-learn pipeline - without pretending it ran your model.
            </motion.p>
            <motion.div variants={reveal} transition={heroTransition} className="mt-9 flex flex-wrap items-center gap-4">
              <button type="button" onClick={onStart} className="landing-primary-cta" aria-label="Analyze a dataset and upload a CSV">
                Analyze a dataset <ArrowRight className="size-4" />
              </button>
              <p className="font-mono text-[11px] leading-5 text-white/36">CSV in. Clear plan out.<br />Your raw rows stay private.</p>
            </motion.div>
          </motion.div>
          <PipelinePreview />
        </section>

        <section className="relative mx-auto max-w-[78rem] px-6 pb-24 sm:px-8 lg:pb-32">
          <div className="border-t border-white/[0.08] pt-8 sm:pt-10">
            <motion.div
              className="grid gap-6 md:grid-cols-3"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.25 }}
              variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
            >
              {features.map(({ icon: Icon, title, body }) => (
                <motion.article key={title} variants={reveal} transition={heroTransition} className="landing-feature">
                  <span className="landing-feature__icon"><Icon className="size-4" /></span>
                  <h2>{title}</h2>
                  <p>{body}</p>
                </motion.article>
              ))}
            </motion.div>
          </div>
        </section>
      </main>

      <footer className="relative mx-auto flex max-w-[78rem] flex-wrap items-center justify-between gap-3 border-t border-white/[0.07] px-6 py-6 font-mono text-[10px] uppercase tracking-[0.12em] text-white/28 sm:px-8">
        <span>AutoNexus</span>
        <span>Profile. Plan. Validate.</span>
      </footer>
    </div>
  );
}
