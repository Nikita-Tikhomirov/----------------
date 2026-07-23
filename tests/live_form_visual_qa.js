const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BROWSER_EXECUTABLE = process.env.BROWSER_EXECUTABLE
  || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const OUTPUT = path.resolve('output/live-form-qa-2026-07-23');
const SUCCESS = /успешно отправлено|сообщение отправлено|спасибо/i;
const PHASE = process.env.LIVE_QA_PHASE || 'all';

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function collectResponse(response, bucket) {
  if (!/admin-ajax\.php|client-standard-mail\.php|\/mail\.php/.test(response.url())) return;
  bucket.push({
    url: response.url(),
    status: response.status(),
    body: (await response.text().catch(() => '')).slice(0, 1000),
  });
}

async function openPage(browser, url, viewport) {
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1200);
  return { page, consoleErrors };
}

async function fillStandardModal(modal, kind) {
  if (await modal.locator('[name="name"]').count()) {
    await modal.locator('[name="name"]').fill('Тест переноса 23.07');
  }
  await modal.locator('[name="phone"]').fill('+79990000000');
  if (kind === 'question' && await modal.locator('[name="question"]').count()) {
    await modal.locator('[name="question"]').fill('Тестовая проверка формы после исправления');
  }
  const captcha = modal.locator('[name="captcha"]');
  if (await captcha.count() && await captcha.getAttribute('type') !== 'hidden') {
    await captcha.fill('5');
  }
}

async function submitStandard(browser, item) {
  const responses = [];
  const { page, consoleErrors } = await openPage(browser, item.url, { width: 1360, height: 900 });
  page.on('response', response => collectResponse(response, responses));
  await page.locator(item.trigger).first().click({ force: true });
  const modal = page.locator(`.csf-modal[data-modal="${item.kind}"]`);
  await modal.waitFor({ state: 'visible', timeout: 10000 });
  await fillStandardModal(modal, item.kind);
  if (item.forceStaleNonce) {
    await modal.locator('[name="nonce"]').evaluate(field => {
      field.value = 'invalid-cached-nonce';
    });
  }
  await page.screenshot({ path: path.join(OUTPUT, `${item.name}-desktop-before.png`) });
  await modal.locator('button[type="submit"]').click();
  await modal.locator('.csf-result.is-visible').waitFor({ timeout: 20000 });
  const message = (await modal.locator('.csf-result').innerText()).trim();
  const className = await modal.locator('.csf-result').getAttribute('class');
  await page.screenshot({ path: path.join(OUTPUT, `${item.name}-desktop-success.png`) });
  if (!SUCCESS.test(message) || /is-error/.test(className)) {
    console.error(JSON.stringify({ name: item.name, message, className, responses }, null, 2));
  }
  assert(SUCCESS.test(message) && !/is-error/.test(className), `${item.name}: ${message}`);
  if (item.forceStaleNonce) {
    assert(responses.some(entry => entry.status === 403), `${item.name}: stale nonce did not fail first`);
    assert(responses.some(entry => /csf_refresh_nonce/.test(entry.body) || /admin-ajax/.test(entry.url) && entry.status === 200), `${item.name}: nonce was not refreshed`);
    assert(responses.filter(entry => entry.status === 200).length >= 2, `${item.name}: nonce retry did not complete`);
  }
  await page.close();
  return { name: item.name, message, responses, consoleErrors };
}

async function submitLegacyInline(browser, item) {
  const responses = [];
  const { page, consoleErrors } = await openPage(browser, item.url, { width: 1360, height: 900 });
  page.on('response', response => collectResponse(response, responses));
  const form = page.locator('input[name="form-action"][value="phone"]').first().locator('xpath=..');
  const panel = form.locator('xpath=..');
  await panel.evaluate(element => {
    element.style.display = 'block';
    element.style.opacity = '1';
    element.style.position = 'relative';
    element.style.inset = 'auto';
    element.style.width = 'min(100%, 560px)';
    element.style.height = 'auto';
    element.style.margin = '20px auto';
    element.style.padding = '18px';
    element.style.background = '#fff';
    element.style.zIndex = '10';
  });
  await panel.scrollIntoViewIfNeeded();
  await form.locator('[name="phone-name"]').fill('Тест переноса 23.07');
  await form.locator('[name="phone-phone"]').fill('+79990000000');
  await panel.screenshot({ path: path.join(OUTPUT, `${item.name}-desktop-before.png`) });
  await form.locator('[type="submit"]').click();
  const result = form.locator('.csf-inline-result.is-visible');
  await result.waitFor({ timeout: 20000 });
  const message = (await result.innerText()).trim();
  const className = await result.getAttribute('class');
  await panel.screenshot({ path: path.join(OUTPUT, `${item.name}-desktop-success.png`) });
  assert(SUCCESS.test(message) && !/is-error/.test(className), `${item.name}: ${message}`);
  assert(responses.some(entry => entry.status === 200 && /success/.test(entry.body)), `${item.name}: no successful handler response`);
  await page.close();
  return { name: item.name, message, responses, consoleErrors };
}

async function submitApreal36(browser) {
  const responses = [];
  const { page, consoleErrors } = await openPage(browser, 'https://apreal36.ru/contacts/', { width: 1360, height: 900 });
  page.on('response', response => collectResponse(response, responses));
  const trigger = page.locator('a[href="#modal-full"], a[href="#license-modal"]').first();
  await trigger.waitFor({ state: 'visible', timeout: 10000 });
  assert((await trigger.innerText()).trim() === 'ЗАДАТЬ ВОПРОС', 'apreal36-question: old button label remains');
  await trigger.click({ force: true });
  const popup = page.locator('#popup-question');
  await popup.waitFor({ state: 'visible', timeout: 10000 });
  assert(await page.locator('#modal-full').count() === 0, 'apreal36-question: broken raw shortcode modal remains');
  await popup.locator('[name="name"]').fill('Тест переноса 23.07');
  await popup.locator('[name="phone"]').fill('+79990000000');
  await popup.locator('[name="coment"]').fill('Тестовая проверка формы после исправления');
  await popup.locator('[name="captcha"]').fill('5');
  await page.screenshot({ path: path.join(OUTPUT, 'apreal36-question-desktop-before.png') });
  await popup.locator('[type="submit"]').click();
  const result = popup.locator('.ajaxConsent.active');
  await result.waitFor({ timeout: 20000 });
  const message = (await result.innerText()).trim();
  await page.screenshot({ path: path.join(OUTPUT, 'apreal36-question-desktop-success.png') });
  assert(SUCCESS.test(message), `apreal36-question: ${message}`);
  assert(responses.some(entry => entry.status === 200), 'apreal36-question: no successful handler response');
  await page.close();
  return { name: 'apreal36-question', message, responses, consoleErrors };
}

async function legacyInlineVisual(browser, item) {
  const { page, consoleErrors } = await openPage(browser, item.url, { width: 1360, height: 900 });
  const infographic = page.locator('.infographic').first();
  const panel = infographic.locator('.text3.info-texts');
  await infographic.locator('.info3').hover();
  await panel.waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForTimeout(1800);
  await infographic.scrollIntoViewIfNeeded();
  await panel.locator('[name="phone-name"]').fill('Тест переноса 23.07');
  await panel.locator('[name="phone-phone"]').fill('+79990000000');
  const fields = await panel.locator('[name="phone-name"], [name="phone-phone"]').evaluateAll(elements => elements.map(element => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return { width: rect.width, height: rect.height, fontSize: style.fontSize };
  }));
  if (item.exactReferenceSize) {
    fields.forEach(field => {
      assert(Math.abs(field.width - 240) < 1, `${item.name}: field width is ${field.width}`);
      assert(Math.abs(field.height - 42) < 1, `${item.name}: field height is ${field.height}`);
      assert(field.fontSize === '16px', `${item.name}: field font is ${field.fontSize}`);
    });
  }
  await page.screenshot({ path: path.join(OUTPUT, `${item.name}-desktop-visual.png`) });
  await page.close();
  return { name: `${item.name}-desktop-visual`, fields, consoleErrors };
}

async function mobileVisual(browser, item) {
  const { page, consoleErrors } = await openPage(browser, item.url, { width: 390, height: 844 });
  const triggers = page.locator(item.trigger);
  const modal = page.locator(item.modal);
  let opened = false;
  for (let index = 0; index < await triggers.count(); index += 1) {
    const trigger = triggers.nth(index);
    if (await trigger.isVisible()) {
      await trigger.click({ force: true });
      opened = true;
      break;
    }
  }
  if (!opened) await triggers.first().evaluate(element => element.click());
  await page.waitForTimeout(400);
  if (!await modal.isVisible()) {
    await triggers.last().evaluate(element => element.click());
  }
  await modal.waitFor({ state: 'visible', timeout: 10000 });
  const metrics = await modal.evaluate(element => {
    const rect = element.getBoundingClientRect();
    return {
      left: rect.left,
      right: rect.right,
      top: rect.top,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height,
      scrollWidth: element.scrollWidth,
      clientWidth: element.clientWidth,
    };
  });
  await page.screenshot({ path: path.join(OUTPUT, `${item.name}-mobile.png`) });
  if (metrics.left < 0 || metrics.right > 390 || metrics.scrollWidth > metrics.clientWidth + 1) {
    console.error(JSON.stringify({ name: item.name, metrics }, null, 2));
  }
  assert(metrics.left >= 0 && metrics.right <= 390, `${item.name}: mobile modal exceeds viewport`);
  assert(metrics.scrollWidth <= metrics.clientWidth + 1, `${item.name}: mobile modal has horizontal overflow`);
  await page.close();
  return { name: `${item.name}-mobile`, metrics, consoleErrors };
}

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: BROWSER_EXECUTABLE, headless: true });
  const results = [];
  try {
    if (PHASE !== 'mobile') results.push(await submitStandard(browser, {
      name: 'apreal-spb-callback', url: 'https://apreal.spb.ru/',
      trigger: '.phones .phones__callback', kind: 'callback', forceStaleNonce: true,
    }));
    if (PHASE !== 'mobile') results.push(await submitStandard(browser, {
      name: 'apreal-spb-question', url: 'https://apreal.spb.ru/',
      trigger: 'button:has-text("ЗАДАТЬ ВОПРОС")', kind: 'question', forceStaleNonce: true,
    }));
    if (PHASE !== 'mobile') results.push(await submitLegacyInline(browser, { name: 'license39-inline-callback', url: 'https://license39.ru/' }));
    if (PHASE !== 'mobile') results.push(await submitLegacyInline(browser, { name: 'apreal-nn-inline-callback', url: 'https://apreal-nn.ru/' }));
    if (PHASE !== 'mobile') results.push(await submitApreal36(browser));
    if (PHASE !== 'mobile') results.push(await submitStandard(browser, {
      name: 'shopap-question', url: 'https://shopap.ru/',
      trigger: '.csf-open-question', kind: 'question', forceStaleNonce: false,
    }));
    if (PHASE === 'all' || PHASE === 'mobile') results.push(await mobileVisual(browser, {
      name: 'apreal-spb-callback', url: 'https://apreal.spb.ru/', trigger: '.phones .phones__callback',
      modal: '.csf-modal[data-modal="callback"]',
    }));
    if (PHASE === 'all' || PHASE === 'mobile') results.push(await mobileVisual(browser, {
      name: 'license39-callback', url: 'https://license39.ru/', trigger: '.phones .phones__callback',
      modal: '.csf-modal[data-modal="callback"]',
    }));
    if (PHASE === 'all' || PHASE === 'mobile') results.push(await mobileVisual(browser, {
      name: 'apreal-nn-callback', url: 'https://apreal-nn.ru/', trigger: 'a[href="#phone-modal"]',
      modal: '.csf-modal[data-modal="callback"]',
    }));
    if (PHASE === 'all' || PHASE === 'mobile') results.push(await mobileVisual(browser, {
      name: 'apreal36-question', url: 'https://apreal36.ru/contacts/',
      trigger: 'a[href="#modal-full"], a[href="#license-modal"]', modal: '#popup-question',
    }));
    if (PHASE === 'all' || PHASE === 'mobile') results.push(await mobileVisual(browser, {
      name: 'shopap-question', url: 'https://shopap.ru/', trigger: '.csf-open-question',
      modal: '.csf-modal[data-modal="question"]',
    }));
    if (PHASE === 'legacy') results.push(await legacyInlineVisual(browser, {
      name: 'license39-inline-callback', url: 'https://license39.ru/', exactReferenceSize: false,
    }));
    if (PHASE === 'legacy') results.push(await legacyInlineVisual(browser, {
      name: 'apreal-nn-inline-callback', url: 'https://apreal-nn.ru/', exactReferenceSize: true,
    }));
  } finally {
    await browser.close();
  }
  const resultFile = path.join(OUTPUT, `results-${PHASE}.json`);
  fs.writeFileSync(resultFile, JSON.stringify(results, null, 2));
  console.log(`LIVE_VISUAL_QA_OK ${resultFile}`);
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
