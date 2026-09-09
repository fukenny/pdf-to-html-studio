(() => {
  // Update this value for every presentation or release build.
  const APP_VERSION = '0.1.0-alpha.2';
  const root = document.querySelector('.studio');
  const $ = (selector) => root.querySelector(selector);
  $('[data-version]').textContent = `v${APP_VERSION}`;
  const state = { jobId: '', html: '', css: '', history: [], image: null };
  const status = $('[data-status]');
  const refineStatus = $('[data-refine-status]');
  const rawCss = (css) => css.replace(/^\s*<style[^>]*>/i, '').replace(/<\/style>\s*$/i, '');

  function say(text, error = false) {
    status.textContent = text;
    status.classList.toggle('is-error', error);
  }

  function sayRefine(text, error = false) {
    refineStatus.textContent = text;
    refineStatus.classList.toggle('is-error', error);
  }

  function render() {
    const document = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>${rawCss(state.css)}</style></head><body>${state.html}</body></html>`;
    $('[data-preview]').srcdoc = document;
    $('[data-html]').value = state.html;
    $('[data-css]').value = state.css;
    $('[data-undo]').disabled = !state.history.length;
  }

  async function responseJson(response) {
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || 'Something went wrong.');
    return body;
  }

  $('[data-file]').addEventListener('change', (event) => {
    $('[data-file-label]').textContent = event.target.files[0]?.name || 'Choose a PDF';
  });

  $('[data-feedback-image]').addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
      event.target.value = '';
      state.image = null;
      return sayRefine('Choose a PNG, JPEG, or WebP image smaller than 5 MB.', true);
    }
    const reader = new FileReader();
    reader.addEventListener('load', () => {
      const dataUrl = String(reader.result);
      state.image = { mimeType: file.type, data: dataUrl.split(',', 2)[1], name: file.name };
      $('[data-image-thumbnail]').src = dataUrl;
      $('[data-image-preview]').hidden = false;
      sayRefine(`${file.name} will be shared with Gemini for this correction.`);
    });
    reader.readAsDataURL(file);
  });

  $('[data-remove-image]').addEventListener('click', () => {
    state.image = null;
    $('[data-feedback-image]').value = '';
    $('[data-image-thumbnail]').removeAttribute('src');
    $('[data-image-preview]').hidden = true;
    sayRefine('Screenshot removed.');
  });

  $('[data-upload]').addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector('button');
    button.disabled = true;
    $('[data-progress]').hidden = false;
    say('Converting selected pages…');
    try {
      const result = await responseJson(await fetch('/api/convert', {
        method: 'POST', body: new FormData(event.currentTarget)
      }));
      Object.assign(state, { jobId: result.jobId, html: result.html, css: result.css, history: [] });
      const figures = result.pages.map((page) => {
        const figure = document.createElement('figure');
        const image = document.createElement('img');
        const caption = document.createElement('figcaption');
        image.src = page.imageUrl;
        image.alt = `Original PDF page ${page.number}`;
        caption.textContent = `Page ${page.number}`;
        figure.append(image, caption);
        return figure;
      });
      $('[data-source]').replaceChildren(...figures);
      $('[data-count]').textContent = `${result.pages.length} page${result.pages.length === 1 ? '' : 's'}`;
      $('[data-export]').href = `/jobs/${state.jobId}/export.zip`;
      $('[data-workspace]').hidden = false;
      $('[data-editor]').hidden = false;
      render();
      const note = result.qualityMode === 'infographic-reconstruction'
        ? 'Infographics reconstructed as responsive HTML and CSS.'
        : 'Basic extraction complete; complex infographics still require a correction pass.';
      say(`Converted ${result.fileName}. ${note}`);
    } catch (error) {
      say(error.message, true);
    } finally {
      button.disabled = false;
      $('[data-progress]').hidden = true;
    }
  });

  $('[data-update]').addEventListener('click', () => {
    state.history.push({ html: state.html, css: state.css });
    state.html = $('[data-html]').value;
    state.css = $('[data-css]').value;
    render();
    say('Preview updated from your code.');
  });

  $('[data-refine]').addEventListener('click', async () => {
    const feedback = $('[data-feedback]').value.trim();
    if (!feedback) return sayRefine('Describe what should change first.', true);
    const button = $('[data-refine]');
    button.disabled = true;
    button.textContent = 'Applying…';
    sayRefine('Sending this correction to Gemini…');
    try {
      const result = await responseJson(await fetch('/api/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback, html: state.html, css: state.css, image: state.image })
      }));
      state.history.push({ html: state.html, css: state.css });
      state.html = result.html;
      state.css = result.css;
      render();
      sayRefine(result.summary || 'Correction applied. Review the preview above.');
    } catch (error) {
      sayRefine(error.message, true);
    } finally {
      button.disabled = false;
      button.textContent = 'Apply with Gemini';
    }
  });

  $('[data-undo]').addEventListener('click', () => {
    const previous = state.history.pop();
    if (!previous) return;
    state.html = previous.html;
    state.css = previous.css;
    render();
    say('Last change undone.');
  });
  $('[data-copy-html]').addEventListener('click', async () => {
    await navigator.clipboard.writeText(state.html);
    say('Section HTML copied.');
  });
  $('[data-copy-css]').addEventListener('click', async () => {
    await navigator.clipboard.writeText(state.css);
    say('Style block copied.');
  });
  root.querySelectorAll('[data-tab]').forEach((tab) => tab.addEventListener('click', () => {
    root.querySelectorAll('[data-tab]').forEach((item) => item.classList.toggle('is-active', item === tab));
    $('[data-html]').hidden = tab.dataset.tab !== 'html';
    $('[data-css]').hidden = tab.dataset.tab !== 'css';
  }));
})();
