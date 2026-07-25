const assert = require('node:assert/strict');

const url = 'https://medlic.spb.ru/';

async function main() {
  const response = await fetch(url);
  const html = await response.text();

  assert.equal(response.status, 200, 'The home page must respond with HTTP 200.');
  assert.match(html, /<title>[^<]+<\/title>/i, 'The home page must have a title.');
  assert.match(
    html,
    /<meta\s+name=["']description["'][^>]+content=["'][^"']+/i,
    'The home page must have a meta description.'
  );
  assert.doesNotMatch(
    html,
    /<meta\s+name=["']robots["']\s+content=["'][^"']*\bnoindex\b/i,
    'The public home page must not block indexing with noindex.'
  );

  console.log('medlic.spb.ru SEO indexing check passed');
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
