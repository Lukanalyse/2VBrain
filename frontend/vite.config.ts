import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, type Plugin } from 'vite';

// PDF.js resolves its decoders, fonts and character maps by filename at runtime.
// Keep these resources local and available in both Vite and the packaged app.
function pdfResources(): Plugin {
  const require = createRequire(import.meta.url);
  const root = dirname(require.resolve('pdfjs-dist/package.json'));
  const files = new Map<string, Buffer>();
  for (const directory of ['wasm', 'cmaps', 'standard_fonts', 'iccs']) {
    for (const name of readdirSync(join(root, directory))) {
      files.set(
        `pdfjs/${directory}/${name}`,
        readFileSync(join(root, directory, name))
      );
    }
  }
  return {
    name: 'pdf-resources',
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const path = (request.url ?? '').split('?')[0].replace(/^\//, '');
        const contents = files.get(path);
        if (!contents) return next();
        response.setHeader(
          'Content-Type',
          path.endsWith('.js')
            ? 'text/javascript'
            : path.endsWith('.wasm')
              ? 'application/wasm'
              : 'application/octet-stream'
        );
        response.end(contents);
      });
    },
    generateBundle() {
      for (const [fileName, source] of files)
        this.emitFile({ type: 'asset', fileName, source });
    }
  };
}

export default defineConfig({
  plugins: [pdfResources(), sveltekit()]
});
