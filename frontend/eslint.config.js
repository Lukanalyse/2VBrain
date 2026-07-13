import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import ts from 'typescript-eslint';

export default [
  {
    ignores: ['.svelte-kit/**', 'build/**', 'node_modules/**']
  },
  js.configs.recommended,
  ...ts.configs.recommended,
  ...svelte.configs['flat/recommended'],
  {
    rules: {
      'no-undef': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_'
        }
      ],
      'svelte/no-at-html-tags': 'off'
    }
  },
  {
    files: ['**/*.svelte'],
    languageOptions: {
      parserOptions: {
        parser: ts.parser
      }
    }
  }
];
