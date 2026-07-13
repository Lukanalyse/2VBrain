declare global {
  interface ResearchOSDesktopApi {
    selectVaultFolder?: () => Promise<string | null>;
    openPath?: (path: string) => Promise<{ ok: boolean; error?: string }>;
    revealPath?: (path: string) => Promise<{ ok: boolean; error?: string }>;
  }

  interface Window {
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
