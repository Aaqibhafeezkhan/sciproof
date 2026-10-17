// Fails the build on broken INTERNAL links and anchors in the built site (website/dist).
// External links are not checked here; the daily workflow runs lychee on the live site for them.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { BASE } from '../site.config.mjs';

const dist = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../dist');
if (!fs.existsSync(dist)) {
  console.error('check-links: website/dist does not exist; run the build first');
  process.exit(1);
}

const htmlFiles = [];
(function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith('.html')) htmlFiles.push(full);
  }
})(dist);

const idCache = new Map();
const idsOf = (file) => {
  if (!idCache.has(file)) {
    const html = fs.readFileSync(file, 'utf8');
    idCache.set(file, new Set([...html.matchAll(/\s(?:id|name)="([^"]+)"/g)].map((m) => m[1])));
  }
  return idCache.get(file);
};

function resolveTarget(pathname) {
  const candidates = [path.join(dist, pathname)];
  if (pathname.endsWith('/')) candidates.unshift(path.join(dist, pathname, 'index.html'));
  else candidates.push(path.join(dist, pathname, 'index.html'));
  return candidates.find((c) => fs.existsSync(c) && fs.statSync(c).isFile());
}

const problems = [];
let checked = 0;
for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const pageUrl = '/' + path.relative(dist, file).replace(/\\/g, '/').replace(/index\.html$/, '');
  const fullPage = pageUrl.startsWith(BASE) ? pageUrl : BASE + pageUrl;
  for (const match of html.matchAll(/\s(?:href|src)="([^"]*)"/g)) {
    const raw = match[1].replace(/&amp;/g, '&');
    if (!raw || /^([a-z][a-z0-9+.-]*:|\/\/)/i.test(raw)) continue; // external, mailto:, data:
    const [withoutHash, hash = ''] = raw.split('#');
    const [pathPart] = withoutHash.split('?');
    let absolute;
    if (pathPart === '') absolute = fullPage;
    else if (pathPart.startsWith('/')) absolute = pathPart;
    else absolute = path.posix.normalize(path.posix.join(fullPage, pathPart));
    if (!absolute.startsWith(BASE + '/') && absolute !== BASE) {
      problems.push(`${fullPage}: ${raw} points outside ${BASE}/`);
      continue;
    }
    checked++;
    const target = resolveTarget(absolute.slice(BASE.length) || '/');
    if (!target) {
      problems.push(`${fullPage}: ${raw} -> not found`);
      continue;
    }
    if (hash && target.endsWith('.html') && !idsOf(target).has(decodeURIComponent(hash))) {
      problems.push(`${fullPage}: ${raw} -> anchor #${hash} not found`);
    }
  }
}

if (problems.length) {
  console.error(`check-links: ${problems.length} broken internal link(s):\n  ` + [...new Set(problems)].join('\n  '));
  process.exit(1);
}
console.log(`check-links: ${checked} internal links in ${htmlFiles.length} pages are fine`);
