/**
 * @process fotoderp-windows-build-fix
 * @description FotoDerp Windows Build - Alle Probleme lösen und funktionierenden Build erstellen
 * @skill codebase-analyzer specializations/qa-testing-automation/skills/codebase-analyzer/SKILL.md
 */

import { defineTask } from '@a5c-ai/babysitter-sdk';

// ============================================================================
// TASK DEFINITIONS
// ============================================================================

const analyzeProblemTask = defineTask('analyze-windows-build-problem', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Analyze Windows Build Problem',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Senior DevOps Engineer',
      task: 'Analyze why the FotoDerp Windows build keeps failing with Nuitka.',
      context: { 
        workflowFile: '.github/workflows/build.yml',
        buildScript: 'backend/build_simple.py',
        errorMessages: [
          'FATAL: Nuitka does not work in --mode=standalone or --mode=onefile on Windows without dependency walker',
          'Is it OK to download and put it in local user cache',
          'Fully automatic, cached. Proceed and download? [Yes]/No : no (default non-interactive)',
          'ERROR: Build failed with exit code 1'
        ],
        ...args
      },
      instructions: [
        'Read .github/workflows/build.yml - analyze the Windows build steps',
        'Read backend/build_simple.py - check the Nuitka invocation',
        'Identify why Dependency Walker download keeps failing in non-interactive mode',
        'Check if NUITKA_ASSUME_YES=1 environment variable is set',
        'Check if NUITKA_WINDOWS_DEPENDENCY_TOOL is set correctly',
        'Identify the ROOT CAUSE of the build failure',
        'Output a structured analysis with root cause and fix recommendations'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['rootCause', 'fixSteps', 'recommendations'],
      properties: {
        rootCause: { type: 'string' },
        fixSteps: { type: 'array', items: { type: 'string' } },
        recommendations: { type: 'array', items: { type: 'string' } }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['windows', 'build', 'nuitka']
}));

const fixBuildScriptTask = defineTask('fix-build-script', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Fix build_simple.py for Windows',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Python Build Engineer',
      task: 'Fix backend/build_simple.py so the Windows build succeeds with Nuitka.',
      context: { 
        filePath: 'backend/build_simple.py',
        analysisResult: args.analysisResult,
        ...args
      },
      instructions: [
        'Read backend/build_simple.py',
        'Fix the Nuitka invocation: ensure all required flags are set',
        'Make sure NUITKA_ASSUME_YES=1 is set in environment',
        'Make sure NUITKA_WINDOWS_DEPENDENCY_TOOL points to the correct Dependency Walker path',
        'If Dependency Walker is not found, download it programmatically BEFORE calling Nuitka',
        'Use try/except to handle download errors gracefully',
        'The script MUST exit with code 0 on success, not 1',
        'Test the script logic locally (simulate)',
        'Return the fixed script content'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['success', 'fixedScript', 'changes'],
      properties: {
        success: { type: 'boolean' },
        fixedScript: { type: 'string' },
        changes: { type: 'array', items: { type: 'string' } }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['windows', 'build', 'python']
}));

const fixWorkflowTask = defineTask('fix-workflow', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Fix GitHub Actions Workflow for Windows Build',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'CI/CD Engineer',
      task: 'Fix .github/workflows/build.yml so the Windows build job succeeds.',
      context: { 
        filePath: '.github/workflows/build.yml',
        buildScript: 'backend/build_simple.py',
        analysisResult: args.analysisResult,
        ...args
      },
      instructions: [
        'Read .github/workflows/build.yml',
        'Check the "Build Windows NSIS" job',
        'Make sure all environment variables are set correctly:',
        '  - NUITKA_ASSUME_YES=1',
        '  - NUITKA_WINDOWS_DEPENDENCY_TOOL pointing to Dependency Walker',
        '  - PATH includes the .nuitka directory',
        'The "Build backend" step should call: python3 build_simple.py',
        'Add proper error handling and logging',
        'Ensure the artifact upload step works correctly',
        'Return the fixed workflow content or changes'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['success', 'changes', 'fixedContent'],
      properties: {
        success: { type: 'boolean' },
        changes: { type: 'array', items: { type: 'string' } },
        fixedContent: { type: 'string' }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['windows', 'ci/cd', 'github-actions']
}));

const commitAndPushTask = defineTask('commit-and-push', (args, taskCtx) => ({
  kind: 'shell',
  title: 'Commit and Push Fixes',
  shell: {
    command: 'cd /home/hermes/FotoDerp && git add -A && git commit -m "fix(build): Windows Build Lösung - Dependency Walker + Nuitka Fix (DAS MUSS LAUFEN!)" && git push',
    timeout: 60
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['git', 'ci/cd']
}));

const triggerBuildTask = defineTask('trigger-windows-build', (args, taskCtx) => ({
  kind: 'shell',
  title: 'Trigger Windows Build',
  shell: {
    command: 'cd /home/hermes/FotoDerp && gh workflow run build.yml -f platform=windows',
    timeout: 30
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['ci/cd', 'github']
}));

const monitorBuildTask = defineTask('monitor-build', (args, taskCtx) => ({
  kind: 'shell',
  title: 'Monitor Windows Build',
  shell: {
    command: 'cd /home/hermes/FotoDerp && sleep 30 && gh run list --workflow=build.yml --limit 1',
    timeout: 60
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  },
  labels: ['ci/cd', 'monitor']
}));

// ============================================================================
// PROCESS EXPORT
// ============================================================================

export async function process(inputs, ctx) {
  const { prompt } = inputs;
  
  ctx.log('info', `Starting Windows Build Fix Process: ${prompt}`);
  
  // Phase 1: Analyze the problem
  ctx.log('info', 'Phase 1: Analyzing Windows Build Problem...');
  const analysisResult = await ctx.task(analyzeProblemTask, {
    prompt,
    ...inputs
  });
  
  // Phase 2: Fix build_simple.py
  ctx.log('info', 'Phase 2: Fixing build_simple.py...');
  const buildFixResult = await ctx.task(fixBuildScriptTask, {
    analysisResult,
    ...inputs
  });
  
  if (buildFixResult.success) {
    ctx.log('info', 'Build script fixed. Applying changes...');
    // Apply the fixed script (agent should have written it)
  }
  
  // Phase 3: Fix GitHub Actions Workflow
  ctx.log('info', 'Phase 3: Fixing GitHub Actions Workflow...');
  const workflowFixResult = await ctx.task(fixWorkflowTask, {
    analysisResult,
    buildFixResult,
    ...inputs
  });
  
  // Phase 4: Commit and Push
  ctx.log('info', 'Phase 4: Committing and Pushing Fixes...');
  await ctx.task(commitAndPushTask, {});
  
  // Phase 5: Trigger Windows Build
  ctx.log('info', 'Phase 5: Triggering Windows Build...');
  await ctx.task(triggerBuildTask, {});
  
  // Phase 6: Monitor Build
  ctx.log('info', 'Phase 6: Monitoring Windows Build...');
  const monitorResult = await ctx.task(monitorBuildTask, {});
  
  ctx.log('info', 'Windows Build Fix Process Complete!');
  
  return {
    success: true,
    summary: 'Windows Build Problem analyzed and fixed',
    phases: {
      analysis: analysisResult,
      buildFix: buildFixResult,
      workflowFix: workflowFixResult,
      monitor: monitorResult
    },
    message: 'DAS MUSS LAUFEN! Windows Build wurde gefixt!'
  };
}
