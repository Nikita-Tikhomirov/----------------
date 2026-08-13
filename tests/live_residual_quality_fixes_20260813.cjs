const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'output', 'residual-quality-fixes-20260813', 'qa');
const CHROME = 'C:/Users/user/AppData/Local/ms-playwright/chromium-1232/chrome-win64/chrome.exe';

const LFSB_PAGES = [
  '/', '/404.php', '/contakt.php', '/dlyatreb.php', '/docum.php', '/fstec.php',
  '/fstec_dir.php', '/gt-dop.php', '/gt-per.php', '/gt-pon.php', '/info.php',
  '/kripto_dir.php', '/map.php', '/otkaz.php', '/pp333.php', '/pravo.php',
  '/price.php', '/sendlic.php', '/stroitelstvo.php', '/uslovia.php',
  '/uslugi.php', '/vidyde.php',
];

function pageAudit(page) {
  return page.evaluate(() => {
    const viewport = document.documentElement.clientWidth;
    const visibleOverflow = [...document.querySelectorAll('body *')]
      .filter((element) => {
        if (element.closest('.csf-overlay[hidden], .csf-modal[hidden]')) return false;
        const style = getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden') return false;
        const rect = element.getBoundingClientRect();
        return rect.width > 1 && (rect.left < -1 || rect.right > viewport + 1);
      })
      .slice(0, 15)
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          tag: element.tagName,
          id: element.id || '',
          className: String(element.className || '').slice(0, 100),
          left: Math.round(rect.left),
          right: Math.round(rect.right),
          width: Math.round(rect.width),
          text: (element.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
        };
      });
    return {
      title: document.title,
      viewport,
      scrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      viewportMeta: document.querySelector('meta[name="viewport"]')?.content || null,
      styleHref: document.querySelector('link[href*="style.css"]')?.getAttribute('href') || null,
      visibleOverflow,
    };
  });
}

async function openAndCheckForm(page, kind, screenshotName) {
  const label = kind === 'callback' ? 'ЗАКАЗАТЬ ЗВОНОК' : 'ЗАДАТЬ ВОПРОС';
  const action = page.locator('a:visible, button:visible, input[type="button"]:visible')
    .filter({ hasText: label })
    .first();
  await action.waitFor({ state: 'visible', timeout: 10000 });
  await action.click();
  const modal = page.locator(`.csf-modal[data-modal="${kind}"]`);
  await modal.waitFor({ state: 'visible', timeout: 5000 });
  const evidence = await modal.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const controls = [...element.querySelectorAll('input:not([type="hidden"]):not(.csf-honeypot), textarea, button.csf-submit')]
      .map((control) => {
        const box = control.getBoundingClientRect();
        const style = getComputedStyle(control);
        return {
          tag: control.tagName,
          name: control.getAttribute('name') || '',
          type: control.getAttribute('type') || '',
          width: Math.round(box.width),
          height: Math.round(box.height),
          fontSize: style.fontSize,
          border: style.border,
          visible: box.width > 0 && box.height > 0,
        };
      });
    return {
      rect: { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom },
      viewport: { width: innerWidth, height: innerHeight },
      heading: element.querySelector('h2')?.innerText || '',
      controls,
    };
  });
  await page.screenshot({ path: path.join(OUT, screenshotName), fullPage: false });
  await modal.locator('.csf-close').click();
  await modal.waitFor({ state: 'hidden', timeout: 5000 });
  return evidence;
}

async function auditUrl(browser, url, viewport, name, options = {}) {
  const context = await browser.newContext({ viewport, serviceWorkers: 'block' });
  await context.route('**/*', (route) => {
    const requestUrl = new URL(route.request().url());
    const allowed = requestUrl.hostname === 'lfsb.ru'
      || requestUrl.hostname === 'www.lfsb.ru'
      || requestUrl.hostname === 'medlic.spb.ru';
    if (allowed) return route.continue();
    return route.abort('blockedbyclient');
  });
  const page = await context.newPage();
  const consoleErrors = [];
  const failedRequests = [];
  const badResponses = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('requestfailed', (request) => {
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText || '' });
  });
  page.on('response', (response) => {
    if (response.status() >= 400) badResponses.push({ url: response.url(), status: response.status() });
  });
  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(700);
  const result = {
      url,
      viewport,
      status: response?.status() || null,
      metrics: await pageAudit(page),
      consoleErrors: consoleErrors.filter((message) => !message.includes('ERR_BLOCKED_BY_CLIENT')),
      failedRequests: failedRequests.filter((entry) => !entry.error.includes('BLOCKED_BY_CLIENT')),
      badResponses,
    };
    if (options.screenshot) {
      await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });
    }
    if (options.forms) {
      result.callback = await openAndCheckForm(page, 'callback', `${name}-callback.png`);
      result.question = await openAndCheckForm(page, 'question', `${name}-question.png`);
    }
    if (options.medlicText) {
      const text = await page.locator('body').innerText();
      result.text = {
        badAllProcesses: text.includes('Всеь процессы'),
        badRoszdrav: text.includes('Росздравнадзоррешает'),
        goodAllProcesses: text.includes('Все процессы'),
        goodRoszdrav: text.includes('Росздравнадзор решает'),
      };
    }
    return result;
  } finally {
    await context.close().catch(() => {});
  }
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--disable-gpu', '--disable-dev-shm-usage'],
  });
  const results = { createdAt: new Date().toISOString(), lfsb: [], medlic: [] };
  try {
    for (const route of LFSB_PAGES) {
      const base = route === '/' ? 'home' : route.replace(/^\//, '').replace(/\.php$/, '');
      console.log(`LFSB mobile: ${route}`);
      results.lfsb.push(await auditUrl(
        browser,
        `https://lfsb.ru${route}?qa=20260813-202604`,
        { width: 390, height: 844 },
        `lfsb-${base}-mobile`,
        {
          screenshot: ['/', '/contakt.php', '/fstec_dir.php', '/kripto_dir.php', '/sendlic.php'].includes(route),
          forms: route === '/',
        },
      ));
      fs.writeFileSync(path.join(OUT, 'checkpoint.json'), JSON.stringify(results, null, 2) + '\n', 'utf8');
    }
    results.lfsb.push(await auditUrl(
      browser,
      'https://lfsb.ru/?qa=20260813-202604',
      { width: 1440, height: 900 },
      'lfsb-home-desktop',
      { screenshot: true, forms: true },
    ));
    results.lfsb.push(await auditUrl(
      browser,
      'https://lfsb.ru/?qa=20260813-202604',
      { width: 320, height: 720 },
      'lfsb-home-mobile-320',
      { screenshot: true, forms: true },
    ));
    results.medlic.push(await auditUrl(
      browser,
      'https://medlic.spb.ru/?qa=20260813-202604',
      { width: 1440, height: 900 },
      'medlic-home-desktop',
      { screenshot: true, forms: true, medlicText: true },
    ));
    results.medlic.push(await auditUrl(
      browser,
      'https://medlic.spb.ru/?qa=20260813-202604',
      { width: 390, height: 844 },
      'medlic-home-mobile',
      { screenshot: true, forms: true, medlicText: true },
    ));
  } finally {
    await browser.close();
  }

  const failures = [];
  for (const item of [...results.lfsb, ...results.medlic]) {
    if (item.status !== 200) failures.push(`${item.url}: HTTP ${item.status}`);
    if (item.consoleErrors.length) failures.push(`${item.url}: ${item.consoleErrors.length} console errors`);
    if (item.failedRequests.length) failures.push(`${item.url}: ${item.failedRequests.length} failed requests`);
    if (item.badResponses.length) failures.push(`${item.url}: ${item.badResponses.length} HTTP error responses`);
    if (item.metrics.scrollWidth > item.metrics.viewport + 1) {
      failures.push(`${item.url}: horizontal overflow ${item.metrics.scrollWidth}/${item.metrics.viewport}`);
    }
    if (item.url.includes('lfsb.ru') && item.metrics.bodyScrollWidth > item.metrics.viewport + 1) {
      failures.push(`${item.url}: body overflow ${item.metrics.bodyScrollWidth}/${item.metrics.viewport}`);
    }
    if (item.url.includes('lfsb.ru') && item.metrics.visibleOverflow.length) {
      failures.push(`${item.url}: ${item.metrics.visibleOverflow.length} visible overflowing elements`);
    }
    for (const formName of ['callback', 'question']) {
      const form = item[formName];
      if (!form) continue;
      if (form.rect.left < -1 || form.rect.right > form.viewport.width + 1 || form.rect.top < -1 || form.rect.bottom > form.viewport.height + 1) {
        failures.push(`${item.url}: ${formName} modal is outside viewport`);
      }
      if (!form.controls.length || form.controls.some((control) => !control.visible || control.height < 30)) {
        failures.push(`${item.url}: ${formName} controls are not consistently visible`);
      }
    }
  }
  for (const item of results.medlic) {
    if (item.text.badAllProcesses || item.text.badRoszdrav || !item.text.goodAllProcesses || !item.text.goodRoszdrav) {
      failures.push(`${item.url}: MEDLIC text verification failed`);
    }
  }
  results.failures = failures;
  results.passed = failures.length === 0;
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(results, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({ passed: results.passed, failures, lfsbChecks: results.lfsb.length, medlicChecks: results.medlic.length }, null, 2));
  if (failures.length) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
