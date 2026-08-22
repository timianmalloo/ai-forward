// Render proof for docs/backtest/optimize-graph/index.html — E11: prove the rendered surface.
// No jsdom available, so this is a minimal DOM shim that EXECUTES the page's real inline script
// and asserts #root actually fills. A syntax check (node --check) would NOT catch a render failure
// (defect class PACK-H / PACK-G).
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const dir = path.join(__dirname, '..', 'docs', 'backtest', 'optimize-graph');
const htmlPath = path.join(dir, 'index.html');
const dataPath = path.join(dir, 'backtest-data.js');

function Node(tag) {
  this.tagName = (tag || '').toUpperCase();
  this.children = [];
  this.attributes = {};
  this.dataset = {};
  this.style = {};
  this._text = '';
  this._html = '';
  this.className = '';
}
Node.prototype.appendChild = function (c) { this.children.push(c); c.parentNode = this; return c; };
Node.prototype.setAttribute = function (k, v) { this.attributes[k] = String(v); };
Node.prototype.getAttribute = function (k) { return this.attributes[k]; };
Object.defineProperty(Node.prototype, 'textContent', {
  get() { return this._text || this.children.map(c => c.textContent).join(''); },
  set(v) { this._text = String(v); this.children = []; }
});
Object.defineProperty(Node.prototype, 'innerHTML', {
  get() { return this._html; },
  set(v) { this._html = String(v); this.children = []; }
});
Node.prototype.querySelectorAll = function (sel) {
  const want = sel.replace(/[^a-z]/gi, '').toUpperCase();
  const out = [];
  (function walk(n) {
    n.children.forEach(c => { if (c.tagName === want) out.push(c); walk(c); });
  })(this);
  return out;
};
// crude text size of the rendered tree, including innerHTML blobs
function renderedLength(n) {
  let len = (n._text || '').length + (n._html || '').length;
  n.children.forEach(c => { len += renderedLength(c); });
  return len;
}
function countNodes(n) {
  let c = 1;
  n.children.forEach(k => { c += countNodes(k); });
  return c;
}

const root = new Node('main');
const fallback = new Node('div');
fallback.style = {};
const byId = { root, fallback };

const document = {
  createElement: (t) => new Node(t),
  getElementById: (id) => byId[id] || null
};

const sandbox = {
  document,
  window: {},
  setTimeout,
  clearTimeout,
  console,
  Math,
  Array,
  String,
  Number,
  Object,
  JSON
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

// 1. load the data file exactly as the <script src> would
vm.runInContext(fs.readFileSync(dataPath, 'utf8'), sandbox, { filename: 'backtest-data.js' });

// 2. extract and run the page's real inline script
const html = fs.readFileSync(htmlPath, 'utf8');
const inline = [...html.matchAll(/<script(?![^>]*\ssrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (inline.length !== 1) { console.error('FAIL expected 1 inline script, found ' + inline.length); process.exit(1); }
vm.runInContext(inline[0], sandbox, { filename: 'index.html:inline' });

// 3. assert the surface actually filled
const kids = root.children.length;
const chars = renderedLength(root);
const nodes = countNodes(root);
const cases = (sandbox.window.BACKTEST && sandbox.window.BACKTEST.cases || []).length;
const fallbackShown = fallback.style.display === 'block';

const flat = JSON.stringify(root, (k, v) => (k === 'parentNode' ? undefined : v));
const checks = [
  ['data loaded (12 cases)', cases === 12],
  ['#root has children', kids > 0],
  ['#root rendered substantial content', chars > 8000],
  ['fallback NOT shown', !fallbackShown],
  ['every case id present in output', (sandbox.window.BACKTEST.cases).every(c => flat.includes(c.id))],
  ['integrity banner rendered', flat.includes('modeled')],
  ['aggregate KPIs rendered', flat.includes('Time to execute')],
  ['controls rendered (filter buttons)', root.querySelectorAll('button').length >= 8]
];

let ok = true;
checks.forEach(([label, pass]) => { if (!pass) ok = false; console.log((pass ? 'PASS  ' : 'FAIL  ') + label); });
console.log('---');
console.log('root children=' + kids + '  dom nodes=' + nodes + '  rendered chars=' + chars + '  cases=' + cases);
console.log(ok ? 'VERDICT: MOUNTED' : 'VERDICT: BLANK/BROKEN');
process.exit(ok ? 0 : 1);
