import type { Component } from 'svelte';

export type NavigationItem = {
  label: string;
  href: string;
  icon: Component;
};

export type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};
