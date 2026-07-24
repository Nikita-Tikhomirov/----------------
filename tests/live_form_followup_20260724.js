const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUTPUT = path.resolve('output/live-form-followup-2026-07-24');
const BROWSER_EXECUTABLE = process.env.BROWSER_EXECUTABLE
  || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const SUCCESS = /успешно отправлено|сообщение отправлено|спасибо/i;

function intersects(a, b, tolerance = 1) {
  return a.left < b.right - tolerance
    && a.right > b.left + tolerance
    && a.top < b.bottom - tolerance
    && a.bottom > b.top + tolerance;
}

async function geometry(form) {
  return form.locator('[name="phone-name"], [name="phone-phone"], [type="submit"]')
    .evaluateAll(elements => elements.map(element => {
      const rect = element.getBoundingClientRect();
      return {
        name: element.getAttribute('name') || element.getAttribute('type'),
        left: rect.left,
        right: rect.right,
        top: rect.top,
        bottom: rect.bottom,
        width: rect.width,
        height: rect.height,
      };
    }));
}

async function openLegacyForm(page, domain) {
  const url = process.env.EXACT_ROOT === '1'
    ? `https://${domain}/`
    : `https://${domain}/?csf_followup=${Date.now()}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1500);
  const form = page.locator('input[name="form-action"][value="phone"]').first().locator('xpath=..');
  const panel = form.locator('xpath=..');
  await page.locator('.infographic .info3').first().hover();
  await panel.waitFor({ state: 'visible', timeout: 10000 });
  await panel.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1200);
  return form;
}

function verifyStable(before, after, failures) {
  if (before.length !== 3 || after.length !== 3) {
    failures.push('expected three callback controls');
    return;
  }
  for (let index = 0; index < 3; index += 1) {
    for (const key of ['left', 'right', 'top', 'bottom', 'width', 'height']) {
      if (Math.abs(before[index][key] - after[index][key]) > 1) {
        failures.push(`${before[index].name} ${key} changed after success`);
      }
    }
  }
  if (intersects(after[0], after[1]) || intersects(after[1], after[2])) {
    failures.push('callback controls overlap after success');
  }
}

async function checkLegacyDesktop(browser, domain) {
  const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
  const consoleErrors = [];
  const responses = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('response', async response => {
    if (!/admin-ajax\.php/.test(response.url())) return;
    responses.push({ status: response.status(), body: (await response.text().catch(() => '')).slice(0, 500) });
  });
  const form = await openLegacyForm(page, domain);
  const before = await geometry(form);
  await form.locator('[name="phone-name"]').fill('Follow-up 24.07');
  await form.locator('[name="phone-phone"]').fill('+79990000000');
  await form.locator('[type="submit"]').click();
  const result = form.locator('.csf-inline-result.is-visible');
  await result.waitFor({ state: 'visible', timeout: 20000 });
  const message = (await result.innerText()).trim();
  const after = await geometry(form);
  const failures = [];
  verifyStable(before, after, failures);
  if (!SUCCESS.test(message)) failures.push(`unexpected result: ${message}`);
  if (!responses.some(item => item.status === 200 && /success/.test(item.body))) {
    failures.push('no successful live handler response');
  }
  await page.screenshot({ path: path.join(OUTPUT, `${domain}-desktop-success.png`), fullPage: false });
  await page.close();
  return { domain, viewport: 'desktop', before, after, message, responses, consoleErrors, failures };
}

async function checkLegacyMobile(browser, domain) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const consoleErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.goto(`https://${domain}/?csf_followup=${Date.now()}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1500);
  const form = page.locator('input[name="form-action"][value="phone"]').first().locator('xpath=..');
  if (!await form.isVisible()) {
    await page.screenshot({ path: path.join(OUTPUT, `${domain}-mobile-page.png`), fullPage: false });
    await page.close();
    return {
      domain,
      viewport: 'mobile',
      skipped: 'legacy infographic callback is hidden by the site mobile layout',
      consoleErrors,
      failures: [],
    };
  }
  const before = await geometry(form);
  await form.locator('.csf-inline-result').evaluate(element => {
    element.textContent = 'Спасибо за Ваше сообщение. Оно успешно отправлено';
    element.classList.add('is-visible');
  });
  await page.waitForTimeout(100);
  const after = await geometry(form);
  const failures = [];
  verifyStable(before, after, failures);
  const formBox = await form.boundingBox();
  if (!formBox || formBox.x < -1 || formBox.x + formBox.width > 391) failures.push('callback form overflows mobile viewport');
  await page.screenshot({ path: path.join(OUTPUT, `${domain}-mobile-success.png`), fullPage: false });
  await page.close();
  return { domain, viewport: 'mobile', before, after, formBox, consoleErrors, failures };
}

async function checkApreal(browser, viewport, suffix) {
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.goto(`https://apreal.ru/?csf_followup=${Date.now()}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.locator('.info3').first().hover();
  const form = page.locator('#apreal-inline-callback');
  await form.waitFor({ state: 'visible', timeout: 10000 });
  await form.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1200);
  const metrics = await form.evaluate(element => {
    const formRect = element.getBoundingClientRect();
    const nameRect = element.querySelector('[name="phone-name"]').getBoundingClientRect();
    return { formLeft: formRect.left, formRight: formRect.right, nameLeft: nameRect.left, inset: nameRect.left - formRect.left };
  });
  const failures = [];
  if (metrics.inset < 10) failures.push(`left inset is only ${metrics.inset}px`);
  if (metrics.formLeft < -1 || metrics.formRight > viewport.width + 1) failures.push('callback form overflows viewport');
  await page.screenshot({ path: path.join(OUTPUT, `apreal.ru-${suffix}.png`), fullPage: false });
  await page.close();
  return { domain: 'apreal.ru', viewport: suffix, metrics, consoleErrors, failures };
}

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: BROWSER_EXECUTABLE, headless: true });
  const results = [];
  const domains = process.env.TARGET_DOMAIN
    ? [process.env.TARGET_DOMAIN]
    : ['apreal.spb.ru', 'license39.ru', 'apreal-nn.ru'];
  try {
    for (const domain of domains) {
      results.push(await checkLegacyDesktop(browser, domain));
      results.push(await checkLegacyMobile(browser, domain));
    }
    results.push(await checkApreal(browser, { width: 1360, height: 900 }, 'desktop'));
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(OUTPUT, 'results.json'), JSON.stringify(results, null, 2));
  const failures = results.flatMap(result => result.failures.map(failure => `${result.domain} ${result.viewport}: ${failure}`));
  if (failures.length) {
    console.error(failures.join('\n'));
    process.exit(1);
  }
  console.log('LIVE_FORM_FOLLOWUP_20260724_OK');
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
