const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BROWSER_EXECUTABLE = process.env.BROWSER_EXECUTABLE
  || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const OUTPUT = path.resolve('output/live-form-qa-2026-07-24');

async function openPage(browser, url, viewport) {
  const page = await browser.newPage({ viewport });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1800);
  return page;
}

async function captureLegacy(browser, domain) {
  const page = await openPage(browser, `https://${domain}/`, { width: 1920, height: 1080 });
  const marker = page.locator('input[name="form-action"][value="phone"]').first();
  const form = marker.locator('xpath=..');
  await page.locator('.infographic .info3').first().hover();
  await form.waitFor({ state: 'visible', timeout: 10000 });
  await form.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1800);
  if (!await form.isVisible()) throw new Error(`${domain} legacy form closed before capture`);
  await page.screenshot({ path: path.join(OUTPUT, `${domain}-legacy-1920.png`) });
  await page.close();
}

async function captureApreal(browser) {
  const page = await openPage(browser, 'https://apreal.ru/', { width: 1920, height: 1080 });
  await page.locator('.info3').first().hover();
  await page.locator('#apreal-inline-callback').waitFor({ state: 'visible', timeout: 10000 });
  await page.locator('#apreal-inline-callback').scrollIntoViewIfNeeded();
  await page.waitForTimeout(1800);
  if (!await page.locator('#apreal-inline-callback').isVisible()) {
    throw new Error('apreal.ru callback form closed before capture');
  }
  await page.screenshot({ path: path.join(OUTPUT, 'apreal.ru-callback-1920.png') });
  await page.close();
}

async function captureNousroModal(browser, viewport, suffix) {
  const page = await openPage(browser, 'https://nousro-nn.ru/', viewport);
  await page.locator('#mail-us').click({ force: true });
  const modal = page.locator('.csf-modal[data-modal="callback"]');
  await modal.waitFor({ state: 'visible', timeout: 10000 });
  const metrics = await modal.evaluate(element => {
    const rect = element.getBoundingClientRect();
    const close = element.querySelector('.csf-close').getBoundingClientRect();
    const visibleChat = Array.from(document.querySelectorAll('body > jdiv'))
      .filter(item => getComputedStyle(item).display !== 'none').length;
    return {
      modal: { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom },
      close: { left: close.left, right: close.right, top: close.top, bottom: close.bottom },
      visibleChat,
    };
  });
  if (metrics.modal.left < 0 || metrics.modal.right > viewport.width
      || metrics.modal.top < 0 || metrics.modal.bottom > viewport.height) {
    throw new Error(`nousro-nn modal overflows ${suffix}`);
  }
  if (metrics.close.left < metrics.modal.left || metrics.close.right > metrics.modal.right
      || metrics.close.top < metrics.modal.top || metrics.close.bottom > metrics.modal.bottom) {
    throw new Error(`nousro-nn close is outside ${suffix}`);
  }
  if (metrics.visibleChat !== 0) throw new Error(`nousro-nn chat remains visible in ${suffix}`);
  await page.screenshot({ path: path.join(OUTPUT, `nousro-nn-modal-${suffix}.png`) });
  await page.close();
  return { viewport, metrics };
}

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: BROWSER_EXECUTABLE, headless: true });
  const results = [];
  try {
    for (const domain of ['apreal.spb.ru', 'license39.ru', 'apreal-nn.ru']) {
      await captureLegacy(browser, domain);
    }
    await captureApreal(browser);
    results.push(await captureNousroModal(browser, { width: 1360, height: 900 }, 'desktop'));
    results.push(await captureNousroModal(browser, { width: 390, height: 844 }, 'mobile'));
  } finally {
    await browser.close();
  }
  fs.writeFileSync(
    path.join(OUTPUT, 'visual-results.json'),
    JSON.stringify(results, null, 2),
  );
  console.log('LIVE_VISUAL_20260724_OK');
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
