const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BROWSER_EXECUTABLE = process.env.BROWSER_EXECUTABLE
  || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const OUTPUT = path.resolve('output/live-form-qa-2026-07-24');
const SUCCESS = /\u0443\u0441\u043f\u0435\u0448\u043d\u043e \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e|\u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e|\u0441\u043f\u0430\u0441\u0438\u0431\u043e/i;

function intersects(a, b, tolerance = 1) {
  return a.left < b.right - tolerance
    && a.right > b.left + tolerance
    && a.top < b.bottom - tolerance
    && a.bottom > b.top + tolerance;
}

async function openPage(browser, url, viewport = { width: 1360, height: 900 }) {
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1800);
  return { page, consoleErrors };
}

async function openLegacyPanel(page) {
  const marker = page.locator('input[name="form-action"][value="phone"]').first();
  const form = marker.locator('xpath=..');
  const panel = form.locator('xpath=..');
  const infographic = page.locator('.infographic').first();
  const trigger = infographic.locator('.info3');
  await trigger.hover();
  await panel.waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForTimeout(1800);
  await panel.scrollIntoViewIfNeeded();
  return { form, panel };
}

async function formGeometry(form) {
  return form.locator('[name="phone-name"], [name="phone-phone"], [type="submit"]').evaluateAll(elements => elements.map(element => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    const wrapper = element.parentElement;
    const wrapperRect = wrapper.getBoundingClientRect();
    const wrapperStyle = getComputedStyle(wrapper);
    return {
      name: element.getAttribute('name') || element.getAttribute('type'),
      left: rect.left,
      right: rect.right,
      top: rect.top,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height,
      position: style.position,
      transform: style.transform,
      margin: style.margin,
      wrapper: {
        className: wrapper.className,
        left: wrapperRect.left,
        right: wrapperRect.right,
        top: wrapperRect.top,
        bottom: wrapperRect.bottom,
        position: wrapperStyle.position,
      },
    };
  }));
}

async function checkLegacyCallback(browser, domain) {
  const responses = [];
  const { page, consoleErrors } = await openPage(browser, `https://${domain}/`);
  page.on('response', async response => {
    if (!/admin-ajax\.php|client-standard-mail\.php|\/mail\.php/.test(response.url())) return;
    responses.push({
      url: response.url(),
      status: response.status(),
      body: (await response.text().catch(() => '')).slice(0, 500),
    });
  });
  const { form, panel } = await openLegacyPanel(page);
  const settledGeometry = await formGeometry(form);
  const nameField = form.locator('[name="phone-name"]');
  const nameBox = await nameField.boundingBox();
  await page.mouse.move(nameBox.x + nameBox.width / 2, nameBox.y + nameBox.height / 2);
  await page.waitForTimeout(1000);
  const geometry = await formGeometry(form);
  const name = geometry.find(item => item.name === 'phone-name');
  const phone = geometry.find(item => item.name === 'phone-phone');
  const submit = geometry.find(item => item.name === 'submit');
  await page.screenshot({ path: path.join(OUTPUT, `${domain}-legacy-before.png`) });

  const failures = [];
  if (!name || !phone || !submit) failures.push('legacy controls were not found');
  if (name && phone && intersects(name, phone)) failures.push('name and phone fields overlap');
  if (name && submit && intersects(name, submit)) failures.push('name field and submit button overlap');
  if (phone && submit && intersects(phone, submit)) failures.push('phone field and submit button overlap');
  if (submit && submit.position === 'absolute') failures.push('submit button still uses absolute positioning');
  if (name && phone && submit && Math.max(name.bottom, phone.bottom, submit.bottom) - Math.min(name.bottom, phone.bottom, submit.bottom) > 1) {
    failures.push('legacy controls do not share a bottom alignment');
  }
  for (const item of geometry) {
    if (item.wrapper.position === 'absolute') {
      failures.push(`${item.wrapper.className} still uses absolute positioning`);
    }
  }

  await form.locator('[name="phone-name"]').fill('Acceptance 24.07');
  await form.locator('[name="phone-phone"]').fill('+79990000000');
  await form.locator('[type="submit"]').click({ force: true });
  const result = form.locator('.csf-inline-result.is-visible');
  let message = '';
  try {
    await result.waitFor({ timeout: 20000 });
    message = (await result.innerText()).trim();
  } catch (error) {
    failures.push('no visible submission result');
  }
  if (message && !SUCCESS.test(message)) failures.push(`unexpected result: ${message}`);
  if (!responses.some(item => item.status === 200 && /success/.test(item.body))) {
    failures.push('no successful handler response');
  }
  await page.screenshot({ path: path.join(OUTPUT, `${domain}-legacy-after.png`) });
  await page.close();
  return { domain, settledGeometry, geometry, message, responses, consoleErrors, failures };
}

async function checkAprealAlignment(browser) {
  const { page, consoleErrors } = await openPage(browser, 'https://apreal.ru/');
  await page.locator('.info3').first().hover();
  const panel = page.locator('.text3.info-texts');
  await panel.waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForTimeout(1800);
  await panel.scrollIntoViewIfNeeded();
  const form = page.locator('#apreal-inline-callback');
  const settledGeometry = await formGeometry(form);
  const nameBox = await form.locator('[name="phone-name"]').boundingBox();
  await page.mouse.move(nameBox.x + nameBox.width / 2, nameBox.y + nameBox.height / 2);
  await page.waitForTimeout(1000);
  const geometry = await formGeometry(form);
  const name = geometry.find(item => item.name === 'phone-name');
  const phone = geometry.find(item => item.name === 'phone-phone');
  const submit = geometry.find(item => item.name === 'submit');
  const failures = [];
  if (!name || !phone || !submit) failures.push('callback controls were not found');
  if (name && phone && Math.abs(name.top - phone.top) > 1) {
    failures.push(`callback fields are misaligned by ${Math.abs(name.top - phone.top)}px`);
  }
  if (name && phone && Math.abs(name.height - phone.height) > 1) {
    failures.push(`callback field heights differ by ${Math.abs(name.height - phone.height)}px`);
  }
  if (name && submit && intersects(name, submit)) failures.push('name field and submit button overlap');
  if (phone && submit && intersects(phone, submit)) failures.push('phone field and submit button overlap');
  if (submit && submit.position === 'absolute') failures.push('submit button still uses absolute positioning');
  if (name && phone && submit && Math.max(name.bottom, phone.bottom, submit.bottom) - Math.min(name.bottom, phone.bottom, submit.bottom) > 1) {
    failures.push('callback controls do not share a bottom alignment');
  }
  await page.screenshot({ path: path.join(OUTPUT, 'apreal.ru-callback-alignment.png') });
  await page.close();
  return { domain: 'apreal.ru', settledGeometry, geometry, consoleErrors, failures };
}

async function checkShopQuestion(browser, viewport, suffix) {
  const responses = [];
  const { page, consoleErrors } = await openPage(browser, 'https://shopap.ru/', viewport);
  page.on('response', async response => {
    if (!/client-standard-mail\.php/.test(response.url())) return;
    responses.push({
      url: response.url(),
      status: response.status(),
      body: (await response.text().catch(() => '')).slice(0, 500),
    });
  });
  await page.locator('.csf-open-question').first().click({ force: true });
  const modal = page.locator('.csf-modal[data-modal="question"]');
  await modal.waitFor({ state: 'visible', timeout: 10000 });
  const controls = {
    name: await modal.locator('[name="name"]').count(),
    phone: await modal.locator('[name="phone"]').count(),
    question: await modal.locator('[name="question"]').count(),
    captcha: await modal.locator('[name="captcha"]:not([type="hidden"])').count(),
  };
  const failures = Object.entries(controls)
    .filter(([, count]) => count !== 1)
    .map(([key, count]) => `${key} control count is ${count}`);
  const metrics = await modal.evaluate(element => {
    const rect = element.getBoundingClientRect();
    return { left: rect.left, right: rect.right, width: rect.width, scrollWidth: element.scrollWidth, clientWidth: element.clientWidth };
  });
  if (metrics.left < 0 || metrics.right > viewport.width || metrics.scrollWidth > metrics.clientWidth + 1) {
    failures.push('question modal overflows the viewport');
  }
  let message = '';
  if (Object.values(controls).every(count => count === 1)) {
    await modal.locator('[name="name"]').fill('Acceptance 24.07');
    await modal.locator('[name="phone"]').fill('+79990000000');
    await modal.locator('[name="question"]').fill('Acceptance question 24.07');
    await modal.locator('[name="captcha"]').fill('5');
    await modal.locator('[type="submit"]').click();
    const result = modal.locator('.csf-result.is-visible');
    try {
      await result.waitFor({ timeout: 20000 });
      message = (await result.innerText()).trim();
    } catch (error) {
      failures.push('no visible question submission result');
    }
    if (message && !SUCCESS.test(message)) failures.push(`unexpected result: ${message}`);
    if (!responses.some(item => item.status === 200 && /success/.test(item.body))) {
      failures.push('no successful question handler response');
    }
  }
  await page.screenshot({ path: path.join(OUTPUT, `shopap-question-${suffix}.png`) });
  await page.close();
  return { domain: 'shopap.ru', viewport, controls, metrics, message, responses, consoleErrors, failures };
}

async function checkNousroNn(browser, viewport, suffix) {
  const responses = [];
  const { page, consoleErrors } = await openPage(browser, 'https://nousro-nn.ru/', viewport);
  page.on('response', async response => {
    if (!/admin-ajax\.php/.test(response.url())) return;
    responses.push({
      url: response.url(),
      status: response.status(),
      body: (await response.text().catch(() => '')).slice(0, 500),
    });
  });
  const actions = page.locator('.csf-actions');
  const visibleActions = [];
  for (let index = 0; index < await actions.count(); index += 1) {
    if (await actions.nth(index).isVisible()) visibleActions.push(index);
  }
  const failures = [];
  if (visibleActions.length) failures.push(`${visibleActions.length} duplicate fixed action group is visible`);

  const requestTrigger = page.locator('#mail-us');
  if (await requestTrigger.count()) {
    await requestTrigger.click({ force: true });
    await page.waitForTimeout(500);
  } else {
    failures.push('#mail-us request trigger was not found');
  }
  const dialogs = page.locator('.csf-modal:visible, .uk-modal:visible, [role="dialog"]:visible');
  let close = null;
  if (await dialogs.count()) {
    const dialog = dialogs.first();
    const closeLocator = dialog.locator('.csf-close, .modal-close, .uk-modal-close, [aria-label="\u0417\u0430\u043a\u0440\u044b\u0442\u044c"]').first();
    if (await closeLocator.count()) {
      close = await closeLocator.evaluate(element => {
        const rect = element.getBoundingClientRect();
        const dialogRect = element.closest('.csf-modal,.uk-modal,[role="dialog"]').getBoundingClientRect();
        return {
          text: (element.textContent || '').trim(),
          rect: { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom },
          dialog: { left: dialogRect.left, right: dialogRect.right, top: dialogRect.top, bottom: dialogRect.bottom },
        };
      });
      if (close.rect.left < close.dialog.left || close.rect.right > close.dialog.right) {
        failures.push('modal close button is outside the dialog');
      }

      const callback = dialog.locator('form.csf-form');
      if (await callback.count()) {
        await callback.locator('[name="name"]').fill('Acceptance 24.07');
        await callback.locator('[name="phone"]').fill('+79990000000');
        await callback.locator('[name="captcha"]').fill('5');
        await callback.locator('[type="submit"]').click();
        const result = callback.locator('.csf-result.is-visible');
        let message = '';
        try {
          await result.waitFor({ timeout: 20000 });
          message = (await result.innerText()).trim();
        } catch (error) {
          failures.push('no visible request submission result');
        }
        if (message && !SUCCESS.test(message)) failures.push(`unexpected result: ${message}`);
        if (!responses.some(item => item.status === 200 && /success/.test(item.body))) {
          failures.push('no successful request handler response');
        }
      } else {
        failures.push('#mail-us did not open the standard request form');
      }

      await closeLocator.click({ force: true });
      await page.waitForTimeout(250);
      if (await dialog.isVisible()) failures.push('modal did not close');
    } else {
      failures.push('visible dialog has no close button');
    }
  } else {
    failures.push('request dialog did not open');
  }
  await page.screenshot({ path: path.join(OUTPUT, `nousro-nn-${suffix}.png`) });
  await page.close();
  return { domain: 'nousro-nn.ru', viewport, visibleActions, close, responses, consoleErrors, failures };
}

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: BROWSER_EXECUTABLE, headless: true });
  const results = [];
  try {
    for (const domain of ['apreal.spb.ru', 'license39.ru', 'apreal-nn.ru']) {
      results.push(await checkLegacyCallback(browser, domain));
    }
    results.push(await checkAprealAlignment(browser));
    results.push(await checkShopQuestion(browser, { width: 1360, height: 900 }, 'desktop'));
    results.push(await checkShopQuestion(browser, { width: 390, height: 844 }, 'mobile'));
    results.push(await checkNousroNn(browser, { width: 1360, height: 900 }, 'desktop'));
    results.push(await checkNousroNn(browser, { width: 390, height: 844 }, 'mobile'));
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(OUTPUT, 'results.json'), JSON.stringify(results, null, 2));
  const failures = results.flatMap(result => result.failures.map(failure => `${result.domain}: ${failure}`));
  if (failures.length) {
    console.error(failures.join('\n'));
    process.exit(1);
  }
  console.log('LIVE_ACCEPTANCE_20260724_OK');
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
