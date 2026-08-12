/**
 * The generated pipeline. The code itself is the content: a dark panel
 * against the light shell, as in the step 5 mock, with a chrome bar carrying
 * the filename and the only two actions it needs.
 *
 * Highlighting runs client-side via shiki (already a project dependency, no
 * new one added) through its fine-grained core API, not the top-level
 * `codeToHtml` convenience import. That convenience import selects a
 * language/theme by a runtime string against shiki's full bundle of every
 * grammar it ships, which Rollup cannot tree-shake - it added every language
 * shiki knows (tsx, wasm, cpp, emacs-lisp, wolfram...) to the production
 * build, multiple megabytes for an app that only ever highlights Python.
 * Statically importing exactly python.mjs and one theme, plus the pure-JS
 * regex engine instead of the WASM oniguruma one, keeps this to what the app
 * actually uses.
 */

import { useEffect, useState } from "react";
import { createHighlighterCore, type HighlighterCore } from "shiki/core";
import { createJavaScriptRegexEngine } from "shiki/engine/javascript";
import pythonLang from "shiki/langs/python.mjs";
import darkTheme from "shiki/themes/github-dark.mjs";
import { CheckCircleIcon, CopyIcon, DownloadArrowIcon } from "../shared/icons";

const COPY_RESET_MS = 1800;

let highlighterPromise: Promise<HighlighterCore> | null = null;

function getHighlighter(): Promise<HighlighterCore> {
  highlighterPromise ??= createHighlighterCore({
    langs: [pythonLang],
    themes: [darkTheme],
    engine: createJavaScriptRegexEngine(),
  });
  return highlighterPromise;
}

export function CodeBlock({ code, filename = "pipeline.py" }: { code: string; filename?: string }) {
  const [html, setHtml] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setHtml(null);
    getHighlighter().then((highlighter) => {
      if (cancelled) return;
      setHtml(highlighter.codeToHtml(code, { lang: "python", theme: "github-dark" }));
    });
    return () => {
      cancelled = true;
    };
  }, [code]);

  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), COPY_RESET_MS);
    return () => window.clearTimeout(timer);
  }, [copied]);

  async function handleCopy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
  }

  function handleDownload() {
    const blob = new Blob([code], { type: "text/x-python" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  const lineCount = code.split("\n").length;

  return (
    <div className="overflow-hidden rounded-lg border border-code-border bg-code-bg">
      <div className="flex items-center justify-between gap-4 border-b border-code-border bg-code-chrome px-4 py-2.5">
        <div className="flex min-w-0 items-baseline gap-3">
          <span className="truncate font-mono text-data text-code-text">{filename}</span>
          <span className="label-caps shrink-0 text-code-gutter">{lineCount} lines</span>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <ToolbarButton onClick={handleCopy} icon={copied ? CheckCircleIcon : CopyIcon}>
            {copied ? "Copied" : "Copy"}
          </ToolbarButton>
          <ToolbarButton onClick={handleDownload} icon={DownloadArrowIcon}>
            Download
          </ToolbarButton>
        </div>
      </div>

      <div className="max-h-[36rem] overflow-auto">
        {html ? (
          <div className="shiki-wrapper content-fade-in" dangerouslySetInnerHTML={{ __html: html }} />
        ) : (
          // Shaped like code, not a spinner: indented bars of varying width
          // in the same rhythm the real lines will occupy.
          <div className="space-y-2 p-4 pl-16" aria-label="Highlighting code">
            {Array.from({ length: 14 }).map((_, index) => (
              <div
                key={index}
                className="h-3 rounded-tag bg-white/[0.06]"
                style={{ width: `${35 + ((index * 17) % 50)}%` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolbarButton({
  onClick,
  icon: Icon,
  children,
}: {
  onClick: () => void;
  icon: typeof CopyIcon;
  children: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1.5 rounded-sm px-2.5 py-1.5 font-mono text-data-sm font-medium text-code-text/70 transition-colors duration-150 hover:bg-white/10 hover:text-code-text"
    >
      <Icon className="size-3.5" />
      {children}
    </button>
  );
}
