/**
 * @process fotoderp-direct
 * @description FotoDerp Implementierung direkt über Agent
 */

import { defineTask } from '@a5c-ai/babysitter-sdk';

export async function process(inputs, ctx) {
  const request = inputs?.request || inputs?.prompt || 'Implementiere Features für FotoDerp';
  
  ctx.log('info', `Starte FotoDerp Implementierung: ${request.substring(0, 50)}...`);
  
  // Task direkt definieren
  const result = await ctx.task(
    defineTask('implement', (args, taskCtx) => ({
      kind: 'agent',
      title: 'Implementiere FotoDerp Features',
      agent: {
        name: 'general-purpose',
        prompt: {
          role: 'Senior Full Stack Developer',
          task: args.request,
          context: {
            projectRoot: '/home/hermes/FotoDerp',
            backendPath: 'backend/fotoerp_backend',
            focus: 'AI-Tagging, Face Recognition, Semantic Search'
          },
          instructions: [
            'Analysiere den aktuellen Stand der FotoDerp Implementierung',
            'Prüfe backend/fotoerp_backend/services/ für bestehende Services',
            'Implementiere fehlende Funktionalität mit Fokus auf:',
            '  1. AI Auto-Tagging (analysis.py)',
            '  2. Face Recognition Integration',
            '  3. Semantic Search (search.py)',
            '  4. API-Endpunkte in main.py',
            'Schreibe Tests für neue/deutige Features (TDD)',
            'Stelle sicher, dass der Code den Projekt-Konventionen entspricht',
            'Verwende Python snake_case, JS camelCase, umfassende Docstrings',
            'Dokumentiere alle Änderungen'
          ],
          outputFormat: 'JSON'
        },
        outputSchema: {
          type: 'object',
          required: ['success', 'summary', 'changes'],
          properties: {
            success: { type: 'boolean' },
            summary: { type: 'string' },
            changes: { type: 'array', items: { type: 'string' } }
          }
        }
      },
      io: {
        inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
        outputJsonPath: `tasks/${taskCtx.effectId}/result.json`
      }
    })),
    { request }
  );
  
  ctx.log('info', 'FotoDerp Implementierung abgeschlossen');
  
  return {
    success: result.success || true,
    summary: result.summary || 'Implementation abgeschlossen',
    changes: result.changes || []
  };
}
