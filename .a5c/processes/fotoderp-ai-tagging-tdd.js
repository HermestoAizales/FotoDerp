/**
 * @process fotoderp-ai-tagging-tdd
 * @description FotoDerp AI Auto-Tagging Implementation mit TDD
 * @skill codebase-analyzer specializations/qa-testing-automation/skills/codebase-analyzer/SKILL.md
 * @skill test-generator specializations/qa-testing-automation/skills/test-generator/SKILL.md
 */

import { defineTask } from '@a5c-ai/babysitter-sdk';

// ============================================================================
// TASK DEFINITIONS FOR AI-TAGGING IMPLEMENTATION
// ============================================================================

const analyzeFeatureTask = defineTask('analyze-feature', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Analyze AI-Tagging Feature Requirements',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Senior Software Architect',
      task: 'Analyze the current FotoDerp codebase and define requirements for completing the AI Auto-Tagging feature',
      context: { 
        projectRoot: args.projectRoot || '/home/hermes/FotoDerp',
        backendServices: ['analysis.py', 'openapi_adapter.py', 'search.py', 'culling.py'],
        databaseModels: args.databaseModels || ['Photo', 'AnalysisResult', 'Tag'],
        ...args 
      },
      instructions: [
        'Review backend/fotoerp_backend/services/analysis.py for current implementation',
        'Review backend/fotoerp_backend/services/openapi_adapter.py for AI model integration',
        'Review backend/fotoerp_backend/models.py for data models',
        'Review backend/fotoerp_backend/database.py for database functions',
        'Identify what is implemented and what is missing for AI auto-tagging',
        'Define testable requirements: API endpoints, service methods, database operations',
        'List dependencies and integration points',
        'Output a structured feature specification with testable criteria'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['featureSpec', 'missingComponents', 'testCriteria'],
      properties: {
        featureSpec: { type: 'object' },
        missingComponents: { type: 'array', items: { type: 'string' } },
        testCriteria: { type: 'array', items: { type: 'string' } }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['fotoderp', 'ai-tagging', 'analysis']
}));

const writeTestsTask = defineTask('write-tests', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Write Failing Tests (TDD RED Phase)',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'TDD Developer - RED Phase',
      task: 'Write comprehensive failing tests for the AI-Tagging feature based on the feature specification',
      context: { ...args },
      instructions: [
        'Write pytest tests for backend/fotoerp_backend/services/analysis.py',
        'Test all public methods: analyze_photo, generate_embedding, analyze_photo_batch',
        'Mock the OpenAPIAdapter to avoid actual AI model calls',
        'Test error handling and edge cases',
        'Tests MUST fail initially (RED phase)',
        'Use proper pytest fixtures and mocking',
        'Place tests in backend/tests/ directory',
        'Run tests with: cd backend && python -m pytest tests/ -v',
        'Document test results as RED phase evidence'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['testsCreated', 'testResults', 'evidence'],
      properties: {
        testsCreated: { type: 'array', items: { type: 'string' } },
        testResults: { type: 'object' },
        evidence: { type: 'string' }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['tdd', 'red', 'testing']
}));

const implementFeatureTask = defineTask('implement-feature', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Implement AI-Tagging (TDD GREEN Phase)',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Python Developer - GREEN Phase',
      task: 'Implement the minimal code to make all failing tests pass for AI-Tagging feature',
      context: { ...args },
      instructions: [
        'Read the failing test output to understand expected behavior',
        'Implement missing functionality in backend/fotoerp_backend/services/analysis.py',
        'Implement missing functionality in backend/fotoerp_backend/services/openapi_adapter.py if needed',
        'Update backend/fotoerp_backend/database.py with required functions',
        'Do NOT over-engineer - only implement what tests require',
        'Run tests after each change: cd backend && python -m pytest tests/ -v',
        'All tests MUST pass (GREEN phase)',
        'Document test results as GREEN phase evidence'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['implementationComplete', 'testResults', 'evidence'],
      properties: {
        implementationComplete: { type: 'boolean' },
        testResults: { type: 'object' },
        evidence: { type: 'string' }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['tdd', 'green', 'implementation']
}));

const refactorTask = defineTask('refactor', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Refactor Code (TDD REFACTOR Phase)',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Senior Developer - REFACTOR Phase',
      task: 'Refactor the implemented code while keeping all tests green',
      context: { ...args },
      instructions: [
        'Review the implemented code for code smells and improvement opportunities',
        'Improve code quality: naming, structure, error handling',
        'Ensure all tests still pass after refactoring',
        'Run tests: cd backend && python -m pytest tests/ -v',
        'Document refactoring changes',
        'Ensure code meets project conventions (snake_case, docstrings, etc.)'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['refactorComplete', 'testResults'],
      properties: {
        refactorComplete: { type: 'boolean' },
        testResults: { type: 'object' }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['tdd', 'refactor', 'quality']
}));

const verifyIntegrationTask = defineTask('verify-integration', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Verify Integration with API Endpoints',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Integration Tester',
      task: 'Verify that the AI-Tagging service integrates correctly with the API endpoints',
      context: { ...args },
      instructions: [
        'Review backend/fotoerp_backend/main.py for /api/analyze endpoints',
        'Test that the API endpoints correctly call the analysis service',
        'Verify error handling in API layer',
        'Test with mock data if AI models are not available',
        'Ensure database operations work correctly',
        'Run integration tests',
        'Document integration test results'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['integrationVerified', 'testResults'],
      properties: {
        integrationVerified: { type: 'boolean' },
        testResults: { type: 'object' }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['integration', 'verification']
}));

// ============================================================================
// PROCESS EXPORT
// ============================================================================

/**
 * FotoDerp AI-Tagging TDD Process
 * @param {Object} inputs - Process inputs
 * @param {Object} ctx - Process context
 */
export async function process(inputs, ctx) {
  const { 
    projectRoot = '/home/hermes/FotoDerp',
    ...args 
  } = inputs;
  
  ctx.log('info', `Starting AI-Tagging TDD process for FotoDerp`);
  
  // Phase 1: Analyze feature requirements
  const analysisResult = await ctx.task(analyzeFeatureTask, {
    projectRoot,
    ...args
  });
  
  // Phase 2: TDD RED - Write failing tests
  const redResult = await ctx.task(writeTestsTask, {
    featureSpec: analysisResult.featureSpec,
    missingComponents: analysisResult.missingComponents,
    projectRoot,
    ...args
  });
  
  // Phase 3: TDD GREEN - Implement feature
  const greenResult = await ctx.task(implementFeatureTask, {
    testResults: redResult.testResults,
    featureSpec: analysisResult.featureSpec,
    projectRoot,
    ...args
  });
  
  // Phase 4: TDD REFACTOR - Improve code
  const refactorResult = await ctx.task(refactorTask, {
    implementationResults: greenResult,
    projectRoot,
    ...args
  });
  
  // Phase 5: Verify integration
  const integrationResult = await ctx.task(verifyIntegrationTask, {
    implementationResults: greenResult,
    refactorResults: refactorResult,
    projectRoot,
    ...args
  });
  
  ctx.log('info', 'AI-Tagging TDD process completed successfully');
  
  return {
    success: true,
    summary: 'AI-Tagging feature implemented with TDD',
    phases: {
      analysis: analysisResult,
      red: redResult,
      green: greenResult,
      refactor: refactorResult,
      integration: integrationResult
    }
  };
}
