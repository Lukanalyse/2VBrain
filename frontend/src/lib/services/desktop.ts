export function hasDesktopIntegration(): boolean {
  return (
    typeof window !== 'undefined' &&
    Boolean(window.__TAURI__?.core?.invoke || window.researchOSDesktop)
  );
}

export async function selectVaultFolder(): Promise<string | null> {
  if (window.__TAURI__?.core?.invoke) {
    return window.__TAURI__.core.invoke<string | null>('select_vault_folder');
  }
  return window.researchOSDesktop?.selectVaultFolder?.() ?? null;
}

export async function openPath(path: string): Promise<string | null> {
  if (window.__TAURI__?.core?.invoke) {
    try {
      await window.__TAURI__.core.invoke<void>('open_path', { path });
      return null;
    } catch (error) {
      return error instanceof Error ? error.message : String(error);
    }
  }
  const result = await window.researchOSDesktop?.openPath?.(path);
  if (!result) return 'Native desktop integration is unavailable in this browser session.';
  return result.ok ? null : (result.error ?? 'Unable to open the selected folder.');
}

export async function revealPath(path: string): Promise<string | null> {
  if (window.__TAURI__?.core?.invoke) {
    try {
      await window.__TAURI__.core.invoke<void>('reveal_path', { path });
      return null;
    } catch (error) {
      return error instanceof Error ? error.message : String(error);
    }
  }
  const result = await window.researchOSDesktop?.revealPath?.(path);
  if (!result) return 'Native desktop integration is unavailable in this browser session.';
  return result.ok ? null : (result.error ?? 'Unable to reveal the selected folder.');
}
