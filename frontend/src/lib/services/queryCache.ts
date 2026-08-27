type CacheEntry = {
  expiresAt: number;
  value?: unknown;
  promise?: Promise<unknown>;
};

const cache = new Map<string, CacheEntry>();

export async function cachedQuery<T>(
  key: string,
  loader: () => Promise<T>,
  ttlMs = 3_000
): Promise<T> {
  const now = Date.now();
  const existing = cache.get(key);
  if (existing?.value !== undefined && existing.expiresAt > now) {
    return existing.value as T;
  }
  if (existing?.promise) return existing.promise as Promise<T>;

  const promise = loader()
    .then((value) => {
      cache.set(key, { value, expiresAt: Date.now() + ttlMs });
      return value;
    })
    .catch((error) => {
      cache.delete(key);
      throw error;
    });
  cache.set(key, { expiresAt: now + ttlMs, promise });
  return promise;
}

export function primeQuery<T>(key: string, value: T, ttlMs = 3_000): void {
  cache.set(key, { value, expiresAt: Date.now() + ttlMs });
}

export function invalidateQueries(prefix: string): void {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
}
