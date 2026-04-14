"""Serves the self-contained embeddable review widget JS."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

widget_router = APIRouter()


# The widget is a single self-contained vanilla-JS IIFE. It:
#   - locates its own <script> tag and reads data-* attributes;
#   - fetches the public reviews JSON endpoint;
#   - renders into a <div> inserted right after the script tag;
#   - never uses innerHTML with user-supplied content (uses textContent or
#     escape helpers exclusively) — that is what keeps it XSS-safe;
#   - supports data-theme="auto" using prefers-color-scheme.
#
# Keep this file under ~8KB uncompressed.
WIDGET_JS = r"""(function(){
  var SCRIPT = document.currentScript;
  if (!SCRIPT) {
    var scripts = document.getElementsByTagName('script');
    SCRIPT = scripts[scripts.length - 1];
  }
  var apiBase = SCRIPT.getAttribute('data-api') ||
    (SCRIPT.src ? SCRIPT.src.replace(/\/widget\/reviews\.js.*$/, '') : '');
  var bookId = SCRIPT.getAttribute('data-book-id') || '';
  var style = (SCRIPT.getAttribute('data-style') || 'compact').toLowerCase();
  var theme = (SCRIPT.getAttribute('data-theme') || 'light').toLowerCase();
  var max = parseInt(SCRIPT.getAttribute('data-max') || '3', 10);
  if (isNaN(max) || max < 0) max = 3;
  if (max > 10) max = 10;

  if (!bookId) {
    console.warn('[SPF review widget] Missing data-book-id');
    return;
  }
  if (theme === 'auto') {
    var mq = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
    theme = (mq && mq.matches) ? 'dark' : 'light';
  }
  var dark = theme === 'dark';

  var host = document.createElement('div');
  host.setAttribute('data-spf-widget', bookId);
  host.setAttribute('data-spf-style', style);
  SCRIPT.parentNode.insertBefore(host, SCRIPT.nextSibling);

  var palette = dark
    ? { bg:'#1a1a1a', fg:'#f5f5f5', muted:'#aaa', border:'#333', star:'#ffcc00' }
    : { bg:'#ffffff', fg:'#111', muted:'#666', border:'#e5e5e5', star:'#f5a623' };

  host.style.cssText = [
    'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif',
    'background:' + palette.bg,
    'color:' + palette.fg,
    'border:1px solid ' + palette.border,
    'border-radius:8px',
    'padding:16px',
    'max-width:520px',
    'box-sizing:border-box',
    'line-height:1.45',
    'font-size:14px'
  ].join(';');

  function el(tag, cssText, text) {
    var n = document.createElement(tag);
    if (cssText) n.style.cssText = cssText;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }

  function stars(rating) {
    var full = Math.floor(rating);
    var half = (rating - full) >= 0.5;
    var out = '';
    for (var i = 0; i < full; i++) out += '\u2605';
    if (half) out += '\u00BD';
    while (out.replace('\u00BD','').length + (out.indexOf('\u00BD')>=0?1:0) < 5) {
      out += '\u2606';
    }
    var span = el('span', 'color:' + palette.star + ';letter-spacing:1px');
    span.textContent = out.slice(0, 6);
    return span;
  }

  function renderLoading() {
    host.appendChild(el('div', 'color:' + palette.muted, 'Loading reviews\u2026'));
  }
  function renderError(msg) {
    host.textContent = '';
    host.appendChild(el('div', 'color:' + palette.muted, msg || 'Reviews unavailable.'));
  }
  function footer() {
    var f = el('div', 'margin-top:12px;font-size:11px;color:' + palette.muted);
    f.textContent = 'Powered by SelfPublisherForge';
    return f;
  }

  function renderBadge(data) {
    host.textContent = '';
    var row = el('div', 'display:flex;align-items:center;gap:6px');
    row.appendChild(stars(data.rating || 0));
    row.appendChild(el('span', 'font-weight:600', (data.rating || 0).toFixed(1)));
    row.appendChild(el('span', 'color:' + palette.muted,
      '(' + (data.review_count || 0) + ')'));
    host.appendChild(row);
  }

  function renderCompact(data) {
    host.textContent = '';
    var header = el('div', 'display:flex;align-items:center;gap:8px;margin-bottom:10px');
    header.appendChild(stars(data.rating || 0));
    header.appendChild(el('strong', '', (data.rating || 0).toFixed(1) + ' out of 5'));
    header.appendChild(el('span', 'color:' + palette.muted,
      '(' + (data.review_count || 0) + ' reviews)'));
    host.appendChild(header);

    (data.reviews || []).forEach(function(r) {
      var row = el('div',
        'padding:8px 0;border-top:1px solid ' + palette.border);
      if (r.body_excerpt) {
        var body = el('div', 'margin-bottom:4px');
        body.textContent = '"' + r.body_excerpt + '"';
        row.appendChild(body);
      }
      var meta = el('div', 'color:' + palette.muted + ';font-size:12px');
      var who = r.reviewer_name || 'Verified reader';
      meta.textContent = '\u2014 ' + who + '  ';
      var s = stars(r.rating || 0);
      s.style.fontSize = '12px';
      meta.appendChild(s);
      row.appendChild(meta);
      host.appendChild(row);
    });

    host.appendChild(footer());
  }

  function renderFull(data) {
    // Currently the same as compact but without the 3-review cap.
    renderCompact(data);
  }

  renderLoading();
  var url = apiBase + '/api/v1/public/reviews/' + encodeURIComponent(bookId) +
    '?max=' + max + '&style=' + encodeURIComponent(style);
  fetch(url, { credentials: 'omit' })
    .then(function(resp) {
      if (!resp.ok) throw new Error('http ' + resp.status);
      return resp.json();
    })
    .then(function(data) {
      if (style === 'badge') renderBadge(data);
      else if (style === 'full') renderFull(data);
      else renderCompact(data);
    })
    .catch(function(err) {
      console.warn('[SPF review widget]', err);
      renderError('Reviews unavailable.');
    });
})();
"""


@widget_router.get("/widget/reviews.js", include_in_schema=False)
async def serve_widget_js() -> Response:
    """Return the widget JS with immutable caching headers."""
    return Response(
        content=WIDGET_JS,
        media_type="application/javascript; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=300",
            "X-Content-Type-Options": "nosniff",
        },
    )
