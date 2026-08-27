declare global {
  interface TauriCoreApi {
    invoke<T>(command: string, args?: Record<string, unknown>): Promise<T>;
  }

  interface TauriGlobalApi {
    core: TauriCoreApi;
  }

  interface ResearchOSDesktopApi {
    selectVaultFolder?: () => Promise<string | null>;
    openPath?: (path: string) => Promise<{ ok: boolean; error?: string }>;
    revealPath?: (path: string) => Promise<{ ok: boolean; error?: string }>;
  }

  interface Window {
    __TAURI__?: TauriGlobalApi;
    researchOSDesktop?: ResearchOSDesktopApi;
  }

  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }
}

export {};
