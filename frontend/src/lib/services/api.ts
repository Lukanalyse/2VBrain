import { API_BASE_URL } from '$lib/config/api';

export type HealthResponse = {
  status: 'ok';
};

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error('Unable to reach Research OS API.');
  }

  return response.json() as Promise<HealthResponse>;
}
