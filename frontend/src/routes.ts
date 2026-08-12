/**
 * Screen names as URLs.
 *
 * Hand-rolled over the History API rather than react-router. Routing here is a
 * single path segment with no params, no nesting and no data loaders, so a
 * router would mean a new dependency - which this project does not add without
 * asking - to replace about forty lines.
 *
 * The dataset id is deliberately absent from the path. There is no auth (see
 * docs/not-building.md item 10), so the id is the only thing between a URL and
 * the profile behind it, and a path is the least private place to keep one: it
 * lands in browser history, in the Referer header of any outbound link, and in
 * anything that logs URLs. It stays in sessionStorage, which is where the
 * existing recovery already reads it from.
 */

import type { Screen } from "./state";

/**
 * `code` is the screen's name in the state machine; `/pipeline` is what it is
 * to someone reading the address bar. Rename in this table, never in state.ts,
 * so the two vocabularies stay independent.
 */
const PATHS = {
  landing: "/",
  upload: "/upload",
  target: "/target",
  profile: "/profile",
  strategy: "/strategy",
  code: "/pipeline",
} as const satisfies Record<Screen, string>;

/**
 * Titles name the history entry, so they have to read well in a back-button
 * dropdown where there is no other context. Hyphen separator, not an em dash.
 */
const TITLES = {
  landing: "AutoNexus",
  upload: "Upload data - AutoNexus",
  target: "Choose target - AutoNexus",
  profile: "Data profile - AutoNexus",
  strategy: "ML strategy - AutoNexus",
  code: "Pipeline code - AutoNexus",
} as const satisfies Record<Screen, string>;

const SCREENS = Object.keys(PATHS) as Screen[];

export function pathForScreen(screen: Screen): string {
  return PATHS[screen];
}

export function titleForScreen(screen: Screen): string {
  return TITLES[screen];
}

/**
 * Null for anything unrecognised. A typed URL is untrusted input like any
 * other, and the caller decides what to do about a miss rather than being
 * handed a fabricated screen.
 */
export function screenForPath(pathname: string): Screen | null {
  // "/profile/" and "/Profile" are the same request as far as a person typing
  // is concerned. Root stays "/" rather than collapsing to "".
  const normalised = pathname.toLowerCase().replace(/\/+$/, "") || "/";
  return SCREENS.find((screen) => PATHS[screen] === normalised) ?? null;
}
