/**
 * @process fotoderp-ai-tagging-simple
 * @description Einfache FotoDerp AI-Tagging Implementierung
 */

import { defineTask } from '@a5c-ai/babysitter-sdk';

const analyzeTask = defineTask('analyze', (args, taskCtx) => ({
  kind: 'agent',
  title: 'Analyze and Implement AI-Tagging',
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Full Stack Developer',
      task: args.request || args.prompt || 'Implementiere AI-Tagging Feature für FotoDerp',
      context: {
        projectRoot: '/home/hermes/FotoDerp',
        backendPath: 'backend/fotoerp_backend',
        ...args
      },
      instructions: [
        'Analysiere den aktuellen Stand der FotoDerp Implementierung',
        'Fokus auf AI-Tagging in backend/fotoerp_backend/services/analysis.py',
        'Prüfe was fehlt für vollständige AI-Tagging Funktionalität',
        'Implementiere fehlende Features mit Tests (TDD Ansatz)',
        'Stelle sicher, dass die API-Endpunkte in main.py korrekt funktionieren',
        'Verwende bestehende Services: openapi_adapter.py für KI-Modell-Zugriff',
        'Erstelle notwendige Tests in backend/tests/',
        'Dokumentiere die Änderungen'
      ],
      outputFormat: 'JSON'
    },
    outputSchema: {
      type: 'object',
      required: ['success', 'summary'],
      properties: {
        success: { type: 'boolean' },
        summary: { type: 'string' },
        implemented: { type: 'array', items: { type: 'string' } }
      }
    }
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
  }
}));

export async function process(inputs, ctx) {
  const request = inputs.request || inputs.prompt || 'Implementiere AI-Tagging Feature';
  
  ctx.log('info', `Starting simple AI-Tagging process: ${request.substring(0, 50)}...`);
  
  const result = await ctx.task(analyzeTask, {
    request,
    ...inputs
  });
  
  ctx.log('info', 'AI-Tagging process completed');
  
  return {
    success: true,
    summary: result.summary || 'AI-Tagging Feature bearbeitet',
    result
  };
}
