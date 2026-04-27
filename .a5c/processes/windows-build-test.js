/**
 * @process windows-build-test
 * @description Trigger Windows build via GitHub Actions, wait for completion, and test the build
 */

import { defineTask } from '@a5c-ai/babysitter-sdk';

/**
 * Windows Build Test Process
 * Triggers GitHub Actions workflow for Windows build and monitors the result
 */
export async function process(inputs, ctx) {
  const { platform = 'windows' } = inputs;
  
  ctx.log(`Starting Windows build test process for platform: ${platform}`);
  
  // Task 1: Trigger the build
  const triggerResult = await ctx.execute(defineTask('trigger-build', () => ({
    kind: 'shell',
    title: 'Trigger Windows Build via GitHub Actions',
    shell: {
      command: 'gh',
      args: [
        'workflow', 'run', 'build.yml',
        '--field', `platform=${platform}`
      ]
    }
  })));
  
  ctx.log(`Build triggered: ${JSON.stringify(triggerResult)}`);
  
  // Task 2: Wait for workflow to complete
  const waitResult = await ctx.execute(defineTask('wait-for-build', () => ({
    kind: 'shell',
    title: 'Wait for Build to Complete',
    shell: {
      command: 'bash',
      args: ['-c', `
        echo "Waiting for workflow to complete..."
        for i in {1..60}; do
          STATUS=$(gh run list --workflow build.yml --json status,conclusion --limit 1 2>/dev/null | jq -r '.[0].status // "unknown"')
          CONCLUSION=$(gh run list --workflow build.yml --json status,conclusion --limit 1 2>/dev/null | jq -r '.[0].conclusion // "unknown"')
          echo "Attempt $i: Status=$STATUS, Conclusion=$CONCLUSION"
          
          if [ "$STATUS" = "completed" ]; then
            if [ "$CONCLUSION" = "success" ]; then
              echo "SUCCESS: Build completed successfully!"
              exit 0
            else
              echo "FAILED: Build failed with conclusion: $CONCLUSION"
              exit 1
            fi
          fi
          
          sleep 30
        done
        echo "TIMEOUT: Waiting for build timed out"
        exit 1
      `]
    }
  })));
  
  ctx.log(`Wait result: ${JSON.stringify(waitResult)}`);
  
  if (!waitResult.success) {
    throw new Error(`Build failed or timed out: ${waitResult.error || 'Unknown error'}`);
  }
  
  // Task 3: Download artifacts
  const downloadResult = await ctx.execute(defineTask('download-artifacts', () => ({
    kind: 'shell',
    title: 'Download Build Artifacts',
    shell: {
      command: 'bash',
      args: ['-c', `
        mkdir -p artifacts
        RUN_ID=$(gh run list --workflow build.yml --json databaseId --limit 1 | jq -r '.[0].databaseId // empty')
        if [ -z "$RUN_ID" ]; then
          echo "No run found"
          exit 1
        fi
        echo "Downloading artifacts from run $RUN_ID..."
        gh run download $RUN_ID --dir artifacts --pattern "fotoerp-windows*"
        echo "Download complete"
        ls -la artifacts/
      `]
    }
  })));
  
  ctx.log(`Download result: ${JSON.stringify(downloadResult)}`);
  
  // Task 4: Verify artifact
  const verifyResult = await ctx.execute(defineTask('verify-artifact', () => ({
    kind: 'shell',
    title: 'Verify Windows Artifact',
    shell: {
      command: 'bash',
      args: ['-c', `
        ARTIFACT=$(find artifacts/ -name "*.exe" -type f | head -1)
        if [ -z "$ARTIFACT" ]; then
          echo "No Windows executable found in artifacts"
          exit 1
        fi
        SIZE=$(stat -c%s "$ARTIFACT" 2>/dev/null || stat -f%z "$ARTIFACT" 2>/dev/null)
        echo "Found artifact: $ARTIFACT"
        echo "Size: $SIZE bytes"
        if [ "$SIZE" -lt 1000000 ]; then
          echo "Artifact seems too small (less than 1MB), might be corrupted"
          exit 1
        fi
        echo "VALID: Artifact looks valid (size > 1MB)"
        echo "{\"valid\": true, \"path\": \"$ARTIFACT\", \"size\": $SIZE}" > result.json
      `]
    }
  })));
  
  ctx.log(`Verify result: ${JSON.stringify(verifyResult)}`);
  
  return {
    success: true,
    message: 'Windows build completed and artifact downloaded',
    artifact: verifyResult.output || 'See logs'
  };
}
