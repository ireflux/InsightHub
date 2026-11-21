(() => {
  const input = document.getElementById('searchInput');
  const tagFilter = document.getElementById('tagFilter');
  const list = document.getElementById('postList');
  const pagination = document.getElementById('pagination');
  if (!input || !tagFilter || !list) return;

  const defaultHtml = list.innerHTML;
  const defaultPagination = pagination ? pagination.style.display : '';
  let allPosts = [];

  function safe(text) {
    return String(text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function card(post) {
    const safeTitle = safe(post.title);
    const safeDate = safe(post.date);
    const safeSummary = safe(post.summary);
    const safeUrl = post.url || '/';
    const tags = Array.isArray(post.tags)
      ? post.tags.map((t) => `<span class="tag">${safe(t)}</span>`).join('')
      : '';
    return `<article class="card panel"><p class="meta">${safeDate}</p><h2><a href="${safeUrl}">${safeTitle}</a></h2><p class="excerpt">${safeSummary}</p><div class="tags">${tags}</div></article>`;
  }

  function applyFilter() {
    const q = input.value.trim().toLowerCase();
    const tag = tagFilter.value.trim().toLowerCase();
    if (!q && !tag) {
      list.innerHTML = defaultHtml;
      if (pagination) pagination.style.display = defaultPagination;
      return;
    }

    const filtered = allPosts.filter((p) => {
      const hay = `${p.title || ''} ${p.summary || ''} ${(p.tags || []).join(' ')}`.toLowerCase();
      const tagHit = !tag || (p.tags || []).map((x) => String(x).toLowerCase()).includes(tag);
      return tagHit && (!q || hay.includes(q));
    });

    list.innerHTML = filtered.length ? filtered.map(card).join('') : '<p class="empty">No matching posts.</p>';
    if (pagination) pagination.style.display = 'none';
  }

  const basePath = window.__INSIGHTHUB_BASE_PATH__ || '';
  fetch(`${basePath}/search-index.json`)
    .then((r) => (r.ok ? r.json() : []))
    .then((data) => {
      allPosts = Array.isArray(data) ? data : [];
    })
    .catch(() => {
      allPosts = [];
    });

  input.addEventListener('input', applyFilter);
  tagFilter.addEventListener('change', applyFilter);
})();
