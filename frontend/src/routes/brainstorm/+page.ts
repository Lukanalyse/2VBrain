import { redirect } from '@sveltejs/kit';

// This space was consolidated into the unified Library (IA refactor: 9 → 3 spaces).
export const load = () => {
  throw redirect(307, '/library?type=brainstorm');
};
