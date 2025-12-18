/* eslint-env node */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2020: true,
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  ignorePatterns: ['dist/', 'node_modules/'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  plugins: ['@typescript-eslint', 'react', 'react-hooks', 'jsx-a11y', 'import'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    // Turn off formatting rules that conflict with Prettier
    'prettier',
  ],
  rules: {
    // React 17+ JSX transform
    'react/react-in-jsx-scope': 'off',
    // TS already handles this well; also noisy with TS types
    'react/prop-types': 'off',
  },
};


