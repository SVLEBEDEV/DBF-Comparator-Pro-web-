type DesktopRuntimeConfig = {
  apiBaseUrl?: string;
  platform?: string;
  mode?: string;
};

declare global {
  interface Window {
    __DBF_COMPARATOR_RUNTIME__?: DesktopRuntimeConfig;
  }
}

export function getRuntimeConfig(): DesktopRuntimeConfig {
  if (typeof window === "undefined") {
    return {};
  }

  return window.__DBF_COMPARATOR_RUNTIME__ ?? {};
}
