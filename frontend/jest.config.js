const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/.next/',
    // See tsconfig.json: these suites import ../components/PuzzleBookList and
    // ../components/CreatePuzzleBookWizard, neither of which has ever existed
    // on any branch. They fail at import, so they cannot be skipped in-file.
    '<rootDir>/src/modules/specialty-books/puzzles/',
    '<rootDir>/src/modules/specialty-books/coloring/',
  ],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
};

module.exports = createJestConfig(customJestConfig);
