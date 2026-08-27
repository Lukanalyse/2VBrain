import type { StorageStatus, VaultValidation } from '$lib/types/storage';

import { API_BASE_URL } from '$lib/config/api';
import {
  cachedQuery,
  invalidateQueries,
  primeQuery
} from '$lib/services/queryCache';

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
  return cachedQuery(
    'storage:status',
    () => request<StorageStatus>('/storage'),
    2_000
  );
}

export async function waitForStorageStatus(
  attempts = 20,
  delayMs = 250
): Promise<StorageStatus> {
  let lastError: unknown;

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await getStorageStatus();
    } catch (error) {
      lastError = error;
      if (attempt < attempts - 1) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }

  throw lastError instanceof Error
    ? lastError
    : new Error('Research OS local service is unavailable.');
}

export function validateVault(vaultPath: string): Promise<VaultValidation> {
  return request<VaultValidation>('/storage/vault/validate', {
    method: 'POST',
    body: JSON.stringify({ vault_path: vaultPath })
  });
}

export function saveVaultPath(vaultPath: string): Promise<StorageStatus> {
  invalidateQueries('storage:');
  return request<StorageStatus>('/storage/vault', {
    method: 'PUT',
    body: JSON.stringify({ vault_path: vaultPath })
  }).then((status) => {
    primeQuery('storage:status', status, 2_000);
    return status;
  });
}
