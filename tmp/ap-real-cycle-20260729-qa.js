const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const output = path.resolve('output/ap-real-cycle-2026-07-29');
const stamp = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);

async function openQuestion(page, domain, prefix) {
  const url = `https://${domain}/`;
  const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const trigger = prefix === 'desktop'
    ? page.locator('.header-top .calc-button')
    : page.locator('.csf-actions-mobile .csf-open-question');
  await trigger.waitFor({ state: 'visible', timeout: 30000 });
  const triggerBox = await trigger.boundingBox();
  await trigger.hover();
  await trigger.click();
  const modal = page.locator('.csf-modal[data-modal="question"]');
  await modal.waitFor({ state: 'visible', timeout: 10000 });
  const fields = await modal
    .locator('input:not([type="hidden"]):not(.csf-honeypot), textarea')
    .evaluateAll((elements) => elements.map((element) => element.name));
  await page.screenshot({ path: path.join(output, `${domain}-${prefix}-question.png`) });
  return {
    url,
    status: response ? response.status() : null,
    title: await page.title(),
    triggerBox,
    fields,
    pageErrors: errors,
    overflow: await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      html: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
    })),
  };
}

async function inspectMchs(page, prefix, submit) {
  const response = await page.goto('https://mchs-spb.ru/', {
    waitUntil: 'networkidle',
    timeout: 60000,
  });
  const callbackTrigger = prefix === 'desktop'
    ? page.locator('.header-top .backform')
    : page.locator('.csf-actions-mobile .csf-open-callback');
  const questionTrigger = prefix === 'desktop'
    ? page.locator('.header-top .calc-button')
    : page.locator('.csf-actions-mobile .csf-open-question');

  await callbackTrigger.click();
  const callback = page.locator('.csf-modal[data-modal="callback"]');
  await callback.waitFor({ state: 'visible' });
  const callbackFields = await callback
    .locator('input:not([type="hidden"]):not(.csf-honeypot)')
    .evaluateAll((elements) => elements.map((element) => element.name));
  let callbackResult = '';
  if (submit) {
    await callback.locator('[name="name"]').fill(`QA callback ${stamp}`);
    await callback.locator('[name="phone"]').fill('+7 999 111 22 33');
    await callback.locator('[name="captcha"]').fill('5');
    await callback.locator('.csf-submit').click();
    const result = callback.locator('.csf-result.is-visible');
    await result.waitFor({ state: 'visible', timeout: 30000 });
    callbackResult = (await result.innerText()).trim();
  }
  await page.screenshot({ path: path.join(output, `mchs-spb.ru-${prefix}-callback.png`) });
  await callback.locator('.csf-close').click();

  await questionTrigger.click();
  const question = page.locator('.csf-modal[data-modal="question"]');
  await question.waitFor({ state: 'visible' });
  const questionFields = await question
    .locator('input:not([type="hidden"]):not(.csf-honeypot), textarea')
    .evaluateAll((elements) => elements.map((element) => element.name));
  let questionResult = '';
  if (submit) {
    await question.locator('[name="name"]').fill(`QA question ${stamp}`);
    await question.locator('[name="phone"]').fill('+7 999 111 22 33');
    await question.locator('[name="question"]').fill(`Контрольный вопрос ${stamp}`);
    await question.locator('[name="captcha"]').fill('5');
    await question.locator('.csf-submit').click();
    const result = question.locator('.csf-result.is-visible');
    await result.waitFor({ state: 'visible', timeout: 30000 });
    questionResult = (await result.innerText()).trim();
  }
  await page.screenshot({ path: path.join(output, `mchs-spb.ru-${prefix}-question.png`) });
  return {
    status: response ? response.status() : null,
    callbackFields,
    callbackResult,
    questionFields,
    questionResult,
    overflow: await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      html: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
    })),
  };
}

async function withPage(browser, viewport, callback) {
  const context = await browser.newContext({ viewport, ignoreHTTPSErrors: true });
  const page = await context.newPage();
  try {
    return await callback(page);
  } finally {
    await context.close();
  }
}

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  });
  try {
    const results = {
      stamp,
      otxodi: {
        desktop: await withPage(browser, { width: 1360, height: 900 }, (page) =>
          openQuestion(page, 'otxodi.ru', 'desktop')),
        mobile: await withPage(browser, { width: 390, height: 844 }, (page) =>
          openQuestion(page, 'otxodi.ru', 'mobile')),
      },
      mchs: {
        desktop: await withPage(browser, { width: 1360, height: 900 }, (page) =>
          inspectMchs(page, 'desktop', true)),
        mobile: await withPage(browser, { width: 390, height: 844 }, (page) =>
          inspectMchs(page, 'mobile', false)),
      },
    };
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(results, null, 2));
    console.log(JSON.stringify(results, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
