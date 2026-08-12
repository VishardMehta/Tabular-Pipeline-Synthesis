import { motion, useReducedMotion } from "framer-motion";
import { Orbit } from "lucide-react";
import type { ReactNode } from "react";

export function StageIntro({
  stage,
  title,
  description,
  trail,
  action,
}: {
  stage: number;
  title: string;
  description: ReactNode;
  trail?: ReactNode;
  action?: ReactNode;
}) {
  const reducedMotion = useReducedMotion();
  const item = (delay: number) => ({
    initial: { opacity: 0, y: reducedMotion ? 0 : 10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: reducedMotion ? 0.01 : 0.42, delay, ease: "easeOut" as const },
  });

  return (
    <header className="stage-intro">
      <div className="stage-intro__copy">
        <motion.div {...item(0)} className="stage-intro__eyebrow">
          <span className="stage-intro__orb"><Orbit className="size-3.5" /></span>
          Stage {String(stage).padStart(2, "0")} <span>/</span> {trail ?? "Guided analysis"}
        </motion.div>
        <motion.h1 {...item(0.06)}>{title}</motion.h1>
        <motion.div {...item(0.12)} className="stage-intro__description">{description}</motion.div>
      </div>
      {action ? <motion.div {...item(0.18)} className="stage-intro__action">{action}</motion.div> : null}
    </header>
  );
}
