import type { StorageStatus, VaultValidation } from '$lib/types/storage';

import { API_BASE_URL } from '$lib/config/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    throw new Error('Research OS API request failed.');
  }

  return response.json() as Promise<T>;
}

export function getStorageStatus(): Promise<StorageStatus> {
  return request<StorageStatus>('/storage');
}

export function validateVault(vaultPath: string): Promise<VaultValidation> {
  return request<VaultValidation>('/storage/vault/validate', {
    method: 'POST',
    body: JSON.stringify({ vault_path: vaultPath })
  });
}

export function saveVaultPath(vaultPath: string): Promise<StorageStatus> {
  return request<StorageStatus>('/storage/vault', {
    method: 'PUT',
    body: JSON.stringify({ vault_path: vaultPath })
  });
}
