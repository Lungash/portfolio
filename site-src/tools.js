// Progressive enhancement for /tools/: search, tag filters and a compact list view.
// The tool list is already in the HTML, so nothing here is needed to read it.
(function () {
  var list = document.getElementById('tool-list');
  if (!list) return;
  var cards = [].slice.call(list.children);
  if (cards.length <= 6) return;                 // filters only earn their space past ~6 tools

  var params = new URLSearchParams(location.search);
  var state = { q: params.get('q') || '', tag: params.get('tag') || '' };

  var counts = {};
  cards.forEach(function (c) {
    c.getAttribute('data-tags').split(' ').forEach(function (t) { if (t) counts[t] = (counts[t] || 0) + 1; });
  });
  var tags = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a] || (a < b ? -1 : 1); });

  var bar = document.createElement('div');
  bar.className = 'toolbar';
  bar.setAttribute('role', 'search');
  var search = document.createElement('input');
  search.type = 'search'; search.placeholder = 'Search tools'; search.value = state.q;
  search.setAttribute('aria-label', 'Search tools');
  var filters = document.createElement('div');
  filters.className = 'filters';
  filters.setAttribute('role', 'group'); filters.setAttribute('aria-label', 'Filter by tag');
  var views = document.createElement('div');
  views.className = 'views';
  views.setAttribute('role', 'group'); views.setAttribute('aria-label', 'Layout');
  var count = document.createElement('p');
  count.className = 'count'; count.setAttribute('aria-live', 'polite');

  function button(label, pressed, fn) {
    var b = document.createElement('button');
    b.type = 'button'; b.textContent = label; b.setAttribute('aria-pressed', pressed ? 'true' : 'false');
    b.addEventListener('click', fn);
    return b;
  }
  var tagButtons = [{ tag: '', label: 'all' }].concat(tags.map(function (t) { return { tag: t, label: t }; })).map(function (o) {
    var b = button(o.label, state.tag === o.tag, function () { state.tag = o.tag; apply(); });
    b.setAttribute('data-tag', o.tag);
    filters.appendChild(b);
    return b;
  });
  var gridBtn = button('grid', true, function () { setView(false); });
  var listBtn = button('list', false, function () { setView(true); });
  views.appendChild(gridBtn); views.appendChild(listBtn);
  bar.appendChild(search); bar.appendChild(filters); bar.appendChild(views);
  list.parentNode.insertBefore(bar, list);
  list.parentNode.insertBefore(count, list);

  function setView(isList) {
    list.classList.toggle('is-list', isList);
    gridBtn.setAttribute('aria-pressed', isList ? 'false' : 'true');
    listBtn.setAttribute('aria-pressed', isList ? 'true' : 'false');
    try { localStorage.setItem('tools-view', isList ? 'list' : 'grid'); } catch (e) {}
  }
  function apply() {
    var q = search.value.trim().toLowerCase(), shown = 0;
    state.q = search.value;
    cards.forEach(function (c) {
      var ok = (!state.tag || (' ' + c.getAttribute('data-tags') + ' ').indexOf(' ' + state.tag + ' ') > -1) &&
               (!q || c.getAttribute('data-text').indexOf(q) > -1);
      c.hidden = !ok;
      if (ok) shown++;
    });
    tagButtons.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-tag') === state.tag ? 'true' : 'false'); });
    count.textContent = shown === cards.length ? cards.length + ' tools' : shown + ' of ' + cards.length + ' tools';
    if (!shown) count.textContent = 'Nothing matches. Try another tag or clear the search.';
    var p = new URLSearchParams();
    if (state.tag) p.set('tag', state.tag);
    if (q) p.set('q', search.value.trim());
    try { history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : '')); } catch (e) {}
  }
  search.addEventListener('input', apply);
  try { if (localStorage.getItem('tools-view') === 'list') setView(true); } catch (e) {}
  apply();
})();
