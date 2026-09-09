(() => {
  const root = document.querySelector('[data-pdf-tool]');
  if (!root) return;
  const $ = (selector) => root.querySelector(selector);
  const state = { jobId: '', html: '', css: '', history: [] };
  const status = $('[data-status]');
  const token = root.querySelector('input[name="__RequestVerificationToken"]')?.value || '';

  function say(message, error = false) {
    status.textContent = message;
    status.classList.toggle('is-error', error);
  }

  function fragment(html) { return html; }
  function rawCss(css) {
    return css.replace(/^\s*<style[^>]*>/i, '').replace(/<\/style>\s*$/i, '');
  }

  function render() {
    const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>${rawCss(state.css)}</style></head><body>${state.html}</body></html>`;
    $('[data-preview]').srcdoc = html;
    $('[data-html]').value = state.html;
    $('[data-css]').value = state.css;
    $('[data-undo]').disabled = state.history.length === 0;
  }

  async function readJson(response) {
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || 'Something went wrong.');
    return body;
  }

  $('[data-upload-form]').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const file = $('[data-file]').files[0];
    if (!file) return say('Choose a PDF first.', true);
    say('Converting… larger or graphic-heavy pages may take a minute.');
    form.querySelector('button[type="submit"]').disabled = true;
    try {
      const response = await fetch('/api/pdf-converter/convert', {
        method: 'POST', headers: { RequestVerificationToken: token }, body: new FormData(form)
      });
      const result = await readJson(response);
      Object.assign(state, { jobId: result.jobId, html: result.html, css: result.css, history: [] });
      $('[data-source]').replaceChildren(...result.pages.map((page) => {
        const figure = document.createElement('figure');
        const image = document.createElement('img');
        image.src = page.imageUrl; image.alt = `Original PDF page ${page.number}`;
        const caption = document.createElement('figcaption'); caption.textContent = `Page ${page.number}`;
        figure.append(image, caption); return figure;
      }));
      $('[data-page-count]').textContent = `${result.pages.length} page${result.pages.length === 1 ? '' : 's'}`;
      $('[data-export]').href = `/api/pdf-converter/jobs/${state.jobId}/export`;
      $('[data-workspace]').hidden = false; $('[data-refine]').hidden = false; $('[data-code]').hidden = false;
      render();
      say(result.warnings.length ? `Converted. ${result.warnings.join(' ')}` : 'Converted. Review the preview before publishing.');
    } catch (error) { say(error.message, true); }
    finally { form.querySelector('button[type="submit"]').disabled = false; }
  });

  $('[data-regenerate]').addEventListener('click', async () => {
    const feedback = $('[data-feedback]').value.trim();
    if (!feedback) return say('Describe what you want changed first.', true);
    say('Applying your feedback with Gemini…');
    try {
      const response = await fetch('/api/pdf-converter/refine', {
        method: 'POST', headers: { 'Content-Type': 'application/json', RequestVerificationToken: token },
        body: JSON.stringify({ jobId: state.jobId, html: state.html, css: state.css, feedback })
      });
      const result = await readJson(response);
      state.history.push({ html: state.html, css: state.css });
      state.html = result.html; state.css = result.css; render();
      say(result.summary || 'Changes applied.');
    } catch (error) { say(error.message, true); }
  });

  $('[data-undo]').addEventListener('click', () => {
    const previous = state.history.pop(); if (!previous) return;
    state.html = previous.html; state.css = previous.css; render(); say('Last change undone.');
  });
  $('[data-copy-html]').addEventListener('click', async () => { await navigator.clipboard.writeText(fragment(state.html)); say('HTML copied.'); });
  $('[data-copy-css]').addEventListener('click', async () => { await navigator.clipboard.writeText(state.css); say('CSS copied.'); });
})();
