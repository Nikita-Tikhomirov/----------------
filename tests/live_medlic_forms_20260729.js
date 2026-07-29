const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const URL = 'https://medlic.spb.ru/';
const OUTPUT = path.resolve('output/ap-real-cycle-2026-07-29-medlic');
const SUCCESS = /успешно отправлено/i;
const STAMP = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
const SUBMIT_FORMS = process.env.MEDLIC_QA_SUBMIT !== '0';
const ALLOWED_PAGE_ERRORS = new Set(['n.component.bootComponents is not a function']);

async function openPage(browser, viewport) {
  const context = await browser.newContext({ viewport, ignoreHTTPSErrors: true });
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  const response = await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
  return { context, page, pageErrors, status: response ? response.status() : null };
}

async function openModal(page, label, kind) {
  const trigger = page.getByRole('link', { name: label, exact: true });
  if (await trigger.count() !== 1) throw new Error(`${label}: trigger is not unique`);
  await trigger.click();
  const modal = page.locator(`.csf-modal[data-modal="${kind}"]`);
  await modal.waitFor({ state: 'visible', timeout: 10000 });
  return modal;
}

async function submitForm(modal, values) {
  for (const [name, value] of Object.entries(values)) {
    await modal.locator(`[name="${name}"]`).fill(value);
  }
  await modal.getByRole('button', { name: 'Отправить', exact: true }).click();
  const result = modal.locator('.csf-result.is-visible');
  await result.waitFor({ state: 'visible', timeout: 30000 });
  const message = (await result.innerText()).trim();
  if (!SUCCESS.test(message)) throw new Error(`Unexpected form result: ${message}`);
  return message;
}

async function inspectDesktop(browser) {
  const { context, page, pageErrors, status } = await openPage(
    browser,
    { width: 1360, height: 900 },
  );
  try {
    const fixedActions = await page.locator('.csf-actions').count();
    const callback = await openModal(page, 'ЗАКАЗАТЬ ЗВОНОК', 'callback');
    const callbackFields = await callback
      .locator('input:not([type="hidden"]):not(.csf-honeypot), textarea')
      .evaluateAll((elements) => elements.map((element) => element.name));
    await page.screenshot({ path: path.join(OUTPUT, 'medlic-desktop-callback.png') });
    const callbackResult = SUBMIT_FORMS
      ? await submitForm(callback, {
        name: `QA MEDLIC ${STAMP}`,
        phone: '+7 999 000-29-07',
        captcha: '5',
      })
      : 'submission skipped';
    await callback.locator('.csf-close').click();

    const question = await openModal(page, 'ЗАДАТЬ ВОПРОС', 'question');
    const questionFields = await question
      .locator('input:not([type="hidden"]):not(.csf-honeypot), textarea')
      .evaluateAll((elements) => elements.map((element) => element.name));
    await page.screenshot({ path: path.join(OUTPUT, 'medlic-desktop-question.png') });
    const questionResult = SUBMIT_FORMS
      ? await submitForm(question, {
        name: `QA MEDLIC ${STAMP}`,
        phone: '+7 999 000-29-07',
        question: `Контрольный вопрос ${STAMP}`,
        captcha: '5',
      })
      : 'submission skipped';

    return {
      status,
      fixedActions,
      callbackFields,
      callbackResult,
      questionFields,
      questionResult,
      pageErrors,
    };
  } finally {
    await context.close();
  }
}

async function inspectMobile(browser) {
  const { context, page, pageErrors, status } = await openPage(
    browser,
    { width: 390, height: 844 },
  );
  try {
    const question = await openModal(page, 'ЗАДАТЬ ВОПРОС', 'question');
    const questionFields = await question
      .locator('input:not([type="hidden"]):not(.csf-honeypot), textarea')
      .evaluateAll((elements) => elements.map((element) => element.name));
    const geometry = await question.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return {
        left: rect.left,
        right: rect.right,
        width: rect.width,
        viewport: document.documentElement.clientWidth,
        scrollWidth: element.scrollWidth,
        clientWidth: element.clientWidth,
      };
    });
    await page.screenshot({ path: path.join(OUTPUT, 'medlic-mobile-question.png') });
    return { status, questionFields, geometry, pageErrors };
  } finally {
    await context.close();
  }
}

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  });
  try {
    const results = {
      stamp: STAMP,
      desktop: await inspectDesktop(browser),
      mobile: await inspectMobile(browser),
    };
    const failures = [];
    if (results.desktop.status !== 200 || results.mobile.status !== 200) failures.push('HTTP status');
    if (results.desktop.fixedActions !== 0) failures.push('fixed actions remain');
    if (results.desktop.callbackFields.join(',') !== 'name,phone,captcha') failures.push('callback fields');
    if (results.desktop.questionFields.join(',') !== 'name,phone,question,captcha') failures.push('question fields');
    if (results.mobile.questionFields.join(',') !== 'name,phone,question,captcha') failures.push('mobile fields');
    if (results.mobile.geometry.left < 0
      || results.mobile.geometry.right > results.mobile.geometry.viewport
      || results.mobile.geometry.scrollWidth > results.mobile.geometry.clientWidth + 1) {
      failures.push('mobile overflow');
    }
    const unexpectedPageErrors = [
      ...results.desktop.pageErrors,
      ...results.mobile.pageErrors,
    ].filter((message) => !ALLOWED_PAGE_ERRORS.has(message));
    if (unexpectedPageErrors.length) failures.push(`page errors: ${unexpectedPageErrors.join('; ')}`);
    fs.writeFileSync(path.join(OUTPUT, 'results.json'), JSON.stringify(results, null, 2));
    if (failures.length) throw new Error(failures.join(', '));
    console.log(JSON.stringify(results, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
