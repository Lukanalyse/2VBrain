import { Compass, Home, Library, PanelsTopLeft, Settings } from '@lucide/svelte';

import type { NavigationGroup, NavigationItem } from '$lib/types/navigation';

// Single source of truth. Home is intent-first; Workspace is active work;
// Library is the complete archive; Map is for exploration.
export const navigationGroups: NavigationGroup[] = [
  {
    label: 'Research',
    items: [
      { label: 'Home', href: '/', icon: Home },
      { label: 'Workspace', href: '/workspace', icon: PanelsTopLeft },
      { label: 'Library', href: '/library', icon: Library },
      { label: 'Map', href: '/connections', icon: Compass }
    ]
  },
  {
    label: 'System',
    items: [{ label: 'Settings', href: '/settings/storage', icon: Settings }]
  }
];

export const navigationItems: NavigationItem[] = navigationGroups.flatMap(
  (group) => group.items
);

export function findNavigationItem(pathname: string): NavigationItem {
  return (
    navigationItems.find((item) => item.href === pathname) ??
    navigationItems.find(
      (item) => item.href !== '/' && pathname.startsWith(item.href)
    ) ??
    navigationItems[0]
  );
}
