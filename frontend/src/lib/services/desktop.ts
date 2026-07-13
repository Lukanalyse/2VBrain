export function hasDesktopIntegration(): boolean {
  return typeof window !== 'undefined' && Boolean(window.researchOSDesktop);
}

export async function selectVaultFolder(): Promise<string | null> {
  return window.researchOSDesktop?.selectVaultFolder?.() ?? null;
}

export async function openPath(path: string): Promise<string | null> {
  const result = await window.researchOSDesktop?.openPath?.(path);
  if (!result) return 'Native desktop integration is unavailable in this browser session.';
  return result.ok ? null : (result.error ?? 'Unable to open the selected folder.');
}

export async function revealPath(path: string): Promise<string | null> {
  const result = await window.researchOSDesktop?.revealPath?.(path);
  if (!result) return 'Native desktop integration is unavailable in this browser session.';
  return result.ok ? null : (result.error ?? 'Unable to reveal the selected folder.');
}
