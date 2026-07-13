import { API_BASE_URL } from '$lib/config/api';
import type { LinkableObject } from '$lib/features/linking/types/linking';

export type LiteratureReviewDetail = {
  review: LinkableObject;
  content: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers
    }
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? 'Literature Review request failed.');
  }

  return response.json() as Promise<T>;
}

export async function listReviews(): Promise<LinkableObject[]> {
  const response = await request<{ reviews: LinkableObject[] }>(
    '/literature-reviews'
  );
  return response.reviews;
}

export function createReview(title: string): Promise<LiteratureReviewDetail> {
  return request<LiteratureReviewDetail>('/literature-reviews', {
    method: 'POST',
    body: JSON.stringify({ title })
  });
}

export function getReview(slug: string): Promise<LiteratureReviewDetail> {
  return request<LiteratureReviewDetail>(
    `/literature-reviews/${encodeURIComponent(slug)}`
  );
}

export function saveReview(
  slug: string,
  content: string
): Promise<LiteratureReviewDetail> {
  return request<LiteratureReviewDetail>(
    `/literature-reviews/${encodeURIComponent(slug)}`,
    {
      method: 'PUT',
      body: JSON.stringify({ content })
    }
  );
}
