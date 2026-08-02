const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUTPUT = path.resolve(
  process.env.QA_OUTPUT || 'output/ap-real-full-live-acceptance-2026-07-31'
);
const BROWSER_EXECUTABLES = [
  process.env.BROWSER_EXECUTABLE,
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
].filter((value, index, values) => value && values.indexOf(value) === index);
const QA_CONCURRENCY = Math.max(
  1,
  Number.parseInt(process.env.QA_CONCURRENCY || '2', 10) || 1
);
const QA_ATTEMPTS = Math.max(
  1,
  Number.parseInt(process.env.QA_ATTEMPTS || '2', 10) || 1
);
const QA_SCREENSHOT_TIMEOUT_MS = Math.max(
  1000,
  Number.parseInt(process.env.QA_SCREENSHOT_TIMEOUT_MS || '15000', 10) || 15000
);
const QA_VISUAL_STABILITY_TIMEOUT_MS = Math.max(
  1000,
  Number.parseInt(process.env.QA_VISUAL_STABILITY_TIMEOUT_MS || '12000', 10) || 12000
);
const POLICY_URL = 'https://www.apreal.ru/konfedencialnost.html';
const CONSENT_TEXT = 'Нажимая на кнопку "Отправить" я даю согласие на обработку персональных данных на условиях Политики обработки персональных данных';
const SUCCESS_TEXT = 'Спасибо за Ваше сообщение. Оно успешно отправлено';
const EXPECTED_ACTION_LABELS = {
  callback: 'ЗАКАЗАТЬ ЗВОНОК',
  question: 'ЗАДАТЬ ВОПРОС',
};

const STANDARD_SITES = [
  'docp.ru', 'elecktro.ru', 'medlic.spb.ru', 'mchs-spb.ru', 'otxodi.ru',
  'apreal.spb.ru', 'minkult78.ru', 'medtex78.ru', 'mchs78.ru', 'license39.ru',
  '39mchs.ru', 'apreal-nn.ru', 'apreal-volgograd.ru', 'apreal72.ru', 'nousro.ru',
  'dpomuc.ru', 'ed-kgd.ru', 'muc-vrn.ru', 'nousro-nn.ru', 'fste.ru', 'lfsb.ru',
  'medtex39.ru', 'shopap.ru',
];

const CUSTOM_SITES = [
  'apreal.ru', 'mca24.ru', 'fsa-lab.ru', 'med-license.ru', 'mhsl.ru',
  'apreal36.ru', 'nousro-spb.ru',
];

const EXCLUDED_SITES = [
  'rectavr.ru', 'fstek.spb.ru', 'lic-k.ru', 'apreal-samara.ru', 'ed-krd.ru',
];

const KNOWN_EXCLUDED_INFRA_FAILURES = new Set(['apreal-samara.ru']);

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 1000 },
  { name: 'mobile', width: 390, height: 844 },
];

function safeName(value) {
  return value.replace(/[^a-z0-9.-]+/gi, '-');
}

function normalize(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}

function decodeUnicodeEscapes(value) {
  return (value || '').replace(/\\u([0-9a-f]{4})/gi, (_, hex) => (
    String.fromCharCode(Number.parseInt(hex, 16))
  ));
}

async function screenshot(page, domain, viewport, state) {
  const file = path.join(OUTPUT, `${safeName(domain)}-${viewport}-${state}.png`);
  await page.screenshot({
    path: file,
    fullPage: false,
    animations: 'disabled',
    timeout: QA_SCREENSHOT_TIMEOUT_MS,
  });
  return file;
}

async function waitForVisualStability(page, result) {
  await page.waitForTimeout(1200);
  const hasPendingSmartSlider = await page.locator('[data-creator="Smart Slider 3"]').evaluateAll(sliders => (
    sliders.some(slider => {
      const rect = slider.getBoundingClientRect();
      const style = getComputedStyle(slider);
      const visible = style.display !== 'none' && style.visibility !== 'hidden'
        && rect.width > 0 && rect.height > 0;
      return visible && !slider.classList.contains('n2-ss-loaded');
    })
  ));
  if (!hasPendingSmartSlider) return;

  try {
    await page.waitForFunction(() => (
      [...document.querySelectorAll('[data-creator="Smart Slider 3"]')].every(slider => {
        const rect = slider.getBoundingClientRect();
        const style = getComputedStyle(slider);
        const visible = style.display !== 'none' && style.visibility !== 'hidden'
          && rect.width > 0 && rect.height > 0;
        return !visible || slider.classList.contains('n2-ss-loaded');
      })
    ), null, { timeout: QA_VISUAL_STABILITY_TIMEOUT_MS });
    await page.waitForTimeout(250);
  } catch (_) {
    result.failures.push('visual loading state did not settle: Smart Slider 3');
  }
}

function isFirstParty(url, domain) {
  try {
    const hostname = new URL(url).hostname.replace(/^www\./, '').toLowerCase();
    const expected = domain.replace(/^www\./, '').toLowerCase();
    return hostname === expected || hostname.endsWith(`.${expected}`);
  } catch (_) {
    return false;
  }
}

function isBlockingResourceType(resourceType) {
  return ['document', 'script', 'stylesheet', 'xhr', 'fetch', 'image', 'font'].includes(resourceType);
}

function isCriticalConsoleError(message) {
  return /(?:uncaught|referenceerror|typeerror|syntaxerror|rangeerror|failed to load resource)/i.test(message);
}

async function elementSnapshot(locator) {
  return locator.evaluate(element => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return {
      tag: element.tagName.toLowerCase(),
      text: (element.innerText || element.textContent || element.value || '').replace(/\s+/g, ' ').trim(),
      id: element.id || '',
      className: typeof element.className === 'string' ? element.className : '',
      name: element.getAttribute('name') || '',
      type: element.getAttribute('type') || '',
      required: element.required === true,
      ariaRequired: element.getAttribute('aria-required') || '',
      controlClass: typeof element.className === 'string' ? element.className : '',
      href: element.href || '',
      visible: style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) !== 0
        && rect.width > 0 && rect.height > 0,
      rect: {
        left: rect.left,
        top: rect.top,
        right: rect.right,
        bottom: rect.bottom,
        width: rect.width,
        height: rect.height,
      },
    };
  });
}

async function formSnapshot(form) {
  return form.evaluate(element => ({
    selectorHint: `${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ''}${element.className ? `.${String(element.className).trim().replace(/\s+/g, '.')}` : ''}`,
    dataForm: element.getAttribute('data-form') || '',
    text: (element.innerText || element.textContent || '').replace(/\s+/g, ' ').trim(),
    controls: [...element.querySelectorAll('input, textarea, select, button')].map(control => ({
      tag: control.tagName.toLowerCase(),
      type: control.getAttribute('type') || '',
      name: control.getAttribute('name') || '',
      placeholder: control.getAttribute('placeholder') || '',
      required: control.required === true,
      ariaRequired: control.getAttribute('aria-required') || '',
      className: typeof control.className === 'string' ? control.className : '',
      rawValue: control.getAttribute('value') || '',
      value: ['button', 'submit'].includes(control.type)
        ? (control.innerText || control.value || '').trim()
        : '',
    })),
  }));
}

function validateStandardForm(form, kind, failures) {
  const controls = form.controls.filter(control => !['hidden', 'submit', 'button'].includes(control.type));
  const byName = new Map(controls.map(control => [control.name, control]));
  const expected = kind === 'callback'
    ? ['website', 'name', 'phone', 'captcha']
    : ['website', 'name', 'phone', 'question', 'captcha'];
  const actual = controls.map(control => control.name);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    failures.push(`${kind}: unexpected controls ${JSON.stringify(actual)}`);
  }
  if (!byName.has('name') || byName.get('name').required) failures.push(`${kind}: name must be present and optional`);
  if (!byName.has('phone') || !byName.get('phone').required) failures.push(`${kind}: phone must be required`);
  if (!byName.has('captcha') || !byName.get('captcha').required) failures.push(`${kind}: captcha must be required`);
  if (byName.has('email')) failures.push(`${kind}: email must be absent`);
  if (kind === 'question' && (!byName.has('question') || byName.get('question').required)) {
    failures.push('question: question field must be present and optional');
  }
}

function isRequired(control) {
  return Boolean(control && (
    control.required
    || control.ariaRequired === 'true'
    || /validates-as-required/.test(control.className || '')
  ));
}

function validateActionCopy(kind, triggerSnapshot, modalTitle, failures) {
  const expected = EXPECTED_ACTION_LABELS[kind];
  const triggerLabel = normalize(triggerSnapshot.text.replace(/\b[a-z_]+\b/gi, ''));
  if (triggerLabel !== expected) {
    failures.push(`${kind}: trigger label mismatch: ${triggerSnapshot.text}`);
  }
  if (normalize(modalTitle) !== expected) {
    failures.push(`${kind}: modal title mismatch: ${modalTitle}`);
  }
}

async function findStandardTrigger(page, kind) {
  const own = page.locator(`.csf-open-${kind}:visible`).first();
  if (await own.count()) return own;
  const text = kind === 'callback'
    ? /ЗАКАЗАТЬ ЗВОНОК|ОСТАВИТЬ ЗАЯВКУ|ОТПРАВИТЬ ЗАЯВКУ/i
    : /ЗАДАТЬ ВОПРОС/i;
  const candidates = page.locator('a:visible, button:visible, [role="button"]:visible, input[type="button"]:visible');
  const count = Math.min(await candidates.count(), 250);
  for (let index = 0; index < count; index += 1) {
    const candidate = candidates.nth(index);
    const label = normalize(await candidate.evaluate(element => element.innerText || element.textContent || element.value || ''));
    if (text.test(label)) return candidate;
  }
  return null;
}

async function assertModalGeometry(modal, viewport, kind, failures) {
  const snapshot = await elementSnapshot(modal);
  if (!snapshot.visible) failures.push(`${kind}: modal is not visible after ordinary click`);
  const tolerance = 2;
  if (snapshot.rect.left < -tolerance || snapshot.rect.top < -tolerance
      || snapshot.rect.right > viewport.width + tolerance
      || snapshot.rect.bottom > viewport.height + tolerance) {
    failures.push(`${kind}: modal is outside ${viewport.width}x${viewport.height} viewport`);
  }
  return snapshot;
}

async function exerciseStandard(page, domain, viewport, kind, result) {
  const trigger = await findStandardTrigger(page, kind);
  if (!trigger) {
    result.failures.push(`${kind}: no visible ordinary-click trigger`);
    return;
  }
  const triggerSnapshot = await elementSnapshot(trigger);
  try {
    await trigger.scrollIntoViewIfNeeded();
    await trigger.click({ timeout: 8000 });
    await page.waitForTimeout(350);
  } catch (error) {
    result.failures.push(`${kind}: trigger click failed: ${error.message}`);
    return;
  }
  const modal = page.locator(`.csf-modal[data-modal="${kind}"]`);
  const modalSnapshot = await assertModalGeometry(modal, viewport, kind, result.failures);
  const titleLocator = modal.locator(
    `#csf-${kind}-title:visible, .csf-title:visible, h1:visible, h2:visible, h3:visible, h4:visible`
  ).first();
  const modalTitle = await titleLocator.innerText().catch(() => '');
  validateActionCopy(kind, triggerSnapshot, modalTitle, result.failures);
  const file = await screenshot(page, domain, viewport.name, kind);
  const close = modal.locator('.csf-close:visible').first();
  if (!await close.count()) {
    result.failures.push(`${kind}: visible X close control is absent`);
  } else {
    await close.click({ timeout: 8000 }).catch(error => result.failures.push(`${kind}: X click failed: ${error.message}`));
    await page.waitForTimeout(200);
    if (await modal.isVisible().catch(() => false)) result.failures.push(`${kind}: modal stayed visible after X click`);
  }
  result.actions[kind] = { trigger: triggerSnapshot, modal: modalSnapshot, screenshot: file };
}

async function auditStandard(page, domain, viewport, result) {
  await page.waitForSelector('.csf-root', { timeout: 15000 }).catch(() => null);
  const roots = await page.locator('.csf-root').count();
  if (roots !== 1) {
    result.failures.push(`expected one .csf-root, found ${roots}`);
    return;
  }
  const modals = page.locator('.csf-root .csf-modal');
  if (await modals.count() !== 2) result.failures.push(`expected two standard modals, found ${await modals.count()}`);
  for (const kind of ['callback', 'question']) {
    const modal = page.locator(`.csf-root .csf-modal[data-modal="${kind}"]`);
    if (await modal.count() !== 1) {
      result.failures.push(`${kind}: expected exactly one modal`);
      continue;
    }
    const form = await formSnapshot(modal.locator('form'));
    result.forms[kind] = form;
    validateStandardForm(form, kind, result.failures);
    const consent = normalize(await modal.locator('.csf-consent').innerText().catch(() => ''));
    if (consent !== CONSENT_TEXT) result.failures.push(`${kind}: consent text mismatch`);
    const policy = await modal.locator('.csf-consent a').getAttribute('href').catch(() => '');
    if (policy !== POLICY_URL) result.failures.push(`${kind}: policy URL mismatch: ${policy}`);
  }
  const inlineScripts = (await page.locator('script').allTextContents()).join('\n');
  const externalUrls = await page.locator('script[src*="client-standard-forms"]').evaluateAll(
    nodes => nodes.map(node => node.src).filter(Boolean)
  );
  const externalScripts = [];
  for (const url of externalUrls) {
    const response = await page.context().request.get(url, { timeout: 15000 }).catch(() => null);
    if (response && response.ok()) externalScripts.push(await response.text());
  }
  const scripts = decodeUnicodeEscapes(`${inlineScripts}\n${externalScripts.join('\n')}`);
  const endpoint = await page.locator('.csf-root').getAttribute('data-endpoint').catch(() => '');
  if (externalUrls.length && !scripts.includes(SUCCESS_TEXT)) {
    result.failures.push('exact success text is absent from deployed script');
  } else if (!externalUrls.length && /admin-ajax\.php/i.test(endpoint || '')) {
    result.warnings.push('success text is server-side; checked by source tests and deployment hash');
  }
  await exerciseStandard(page, domain, viewport, 'callback', result);
  await exerciseStandard(page, domain, viewport, 'question', result);
}

async function auditCustom(page, domain, viewport, result) {
  let callbackLocators;
  let questionLocators;
  let fieldNames;
  if (domain === 'apreal.ru') {
    callbackLocators = page.locator('form:has(input[name="_wpcf7"][value="6740"])');
    questionLocators = page.locator('form:has(input[name="_wpcf7"][value="4399"])');
    fieldNames = {
      callback: { name: 'f-name', phone: 'f-phone', captcha: 'callback-quiz' },
      question: { name: 'f-name', phone: 'f-phone', question: 'f-text', captcha: 'question-quiz' },
    };
  } else if (domain === 'nousro-spb.ru') {
    callbackLocators = page.locator('form:has(input[name="_wpcf7"][value="2438"])');
    questionLocators = page.locator('form:has(input[name="_wpcf7"][value="2005"])');
    fieldNames = {
      callback: { name: 'callback-name', phone: 'callback-phone', captcha: 'callback-quiz' },
      question: { name: 'question-name', phone: 'question-phone', question: 'question-message', captcha: 'question-quiz' },
    };
  } else {
    callbackLocators = page.locator('.unipop-form[data-form="callback"]');
    questionLocators = page.locator('.unipop-form[data-form="question"]');
    fieldNames = {
      callback: { name: 'name', phone: 'phone', captcha: 'captcha' },
      question: { name: 'name', phone: 'phone', question: 'coment', captcha: 'captcha' },
    };
  }

  const grouped = { callback: callbackLocators, question: questionLocators };
  for (const kind of ['callback', 'question']) {
    const locators = grouped[kind];
    const count = await locators.count();
    if (!count) {
      result.failures.push(`custom ${kind}: target form was not found`);
      continue;
    }
    for (let index = 0; index < count; index += 1) {
      const locator = locators.nth(index);
      const form = await formSnapshot(locator);
      form.kind = kind;
      result.customForms.push(form);
      const names = form.controls.map(control => control.name);
      const expected = fieldNames[kind];
      const name = form.controls.find(control => control.name === expected.name);
      const phone = form.controls.find(control => control.name === expected.phone);
      const captcha = form.controls.find(control => control.name === expected.captcha);
      const question = expected.question
        ? form.controls.find(control => control.name === expected.question)
        : null;
      if (!name || isRequired(name)) result.failures.push(`custom ${kind}: optional name is absent or required`);
      if (!phone || !isRequired(phone)) result.failures.push(`custom ${kind}: required phone is absent`);
      if (!captcha || !isRequired(captcha)) result.failures.push(`custom ${kind}: required captcha is absent`);
      if (kind === 'question' && (!question || isRequired(question))) {
        result.failures.push('custom question: optional question is absent or required');
      }
      if (names.some(nameValue => /email|mail/i.test(nameValue))) {
        result.failures.push(`custom ${kind}: email must be absent`);
      }
      const consent = normalize(await locator.locator('.policity').innerText().catch(() => ''));
      if (consent !== CONSENT_TEXT) result.failures.push(`custom ${kind}: consent text mismatch`);
      const policy = await locator.locator('.policity a').getAttribute('href').catch(() => '');
      if (policy !== POLICY_URL) result.failures.push(`custom ${kind}: policy URL mismatch: ${policy}`);
    }
  }

  const callbackExercise = !['apreal.ru', 'nousro-spb.ru'].includes(domain)
    ? page.locator('#popup-callback .unipop-form[data-form="callback"]')
    : callbackLocators.first();
  const questionExercise = !['apreal.ru', 'nousro-spb.ru'].includes(domain)
    ? page.locator('#popup-question .unipop-form[data-form="question"]')
    : questionLocators.first();
  await exerciseCustom(page, domain, viewport, 'callback', callbackExercise, result);
  await exerciseCustom(page, domain, viewport, 'question', questionExercise, result);
}

async function closeVisibleCustomModal(page) {
  const close = page.locator(
    '.unipop.active .unipop-close:visible, .uk-modal:visible .uk-modal-close:visible, '
    + '.uk-modal:visible [class*="modal-close"]:visible, .modal:visible [class*="modal-close"]:visible, '
    + '.form-modal-close:visible, [role="dialog"]:visible [aria-label*="закры" i]:visible'
  ).first();
  if (await close.count()) await close.click({ timeout: 5000 }).catch(() => null);
  await page.keyboard.press('Escape').catch(() => null);
  await page.waitForTimeout(200);
}

async function findCustomCandidates(page, kind) {
  const pattern = kind === 'callback'
    ? /ЗАКАЗАТЬ ЗВОНОК|ОБРАТНЫЙ ЗВОНОК|ПЕРЕЗВОНИТЬ|^ЗВОНОК$/i
    : /ЗАДАТЬ ВОПРОС|^ВОПРОС$/i;
  const elements = page.locator(
    'a:visible, button:visible, [role="button"]:visible, input[type="button"]:visible, '
    + '.open-callback:visible, .open-question:visible'
  );
  const result = [];
  const count = Math.min(await elements.count(), 300);
  for (let index = 0; index < count; index += 1) {
    const item = elements.nth(index);
    const text = normalize(await item.evaluate(element => element.innerText || element.textContent || element.value || ''));
    if (pattern.test(text)) result.push(item);
  }
  return result;
}

async function exerciseCustom(page, domain, viewport, kind, form, result) {
  if (!await form.count()) return;
  await closeVisibleCustomModal(page);
  let candidates = await findCustomCandidates(page, kind);
  if (!candidates.length && viewport.name === 'mobile') {
    const menu = page.locator(
      '.sidenav-trigger:visible, .button-collapse:visible, [data-target*="mobile"]:visible, '
      + '[aria-label*="меню" i]:visible'
    ).first();
    if (await menu.count()) {
      await menu.click({ timeout: 5000 }).catch(() => null);
      await page.waitForTimeout(400);
      candidates = await findCustomCandidates(page, kind);
    }
  }
  let trigger = null;
  for (const candidate of candidates.slice(0, 12)) {
    try {
      await candidate.scrollIntoViewIfNeeded();
      await candidate.click({ timeout: 5000 });
      await page.waitForTimeout(350);
      if (await form.isVisible().catch(() => false)) {
        trigger = candidate;
        break;
      }
      await closeVisibleCustomModal(page);
    } catch (error) {
      await closeVisibleCustomModal(page);
    }
  }
  if (!trigger) {
    result.failures.push(`custom ${kind}: no ordinary click opened the target form`);
    return;
  }
  const triggerSnapshot = await elementSnapshot(trigger);
  const modal = form.locator(
    'xpath=ancestor::*[contains(concat(" ",normalize-space(@class)," ")," unipop ") '
    + 'or contains(concat(" ",normalize-space(@class)," ")," uk-modal ") '
    + 'or contains(concat(" ",normalize-space(@class)," ")," modal ")][1]'
  );
  const geometryTarget = await modal.count() ? modal : form;
  const modalSnapshot = await assertModalGeometry(geometryTarget, viewport, `custom ${kind}`, result.failures);
  const titleLocator = geometryTarget.locator(
    '.modal-title:visible, .uk-legend:visible, .unipop-title:visible, legend:visible, '
    + 'h1:visible, h2:visible, h3:visible, h4:visible'
  ).first();
  const modalTitle = await titleLocator.innerText().catch(() => '');
  validateActionCopy(kind, triggerSnapshot, modalTitle, result.failures);
  const file = await screenshot(page, domain, viewport.name, kind);
  const close = geometryTarget.locator(
    '.unipop-close:visible, .uk-modal-close:visible, [class*="modal-close"]:visible, '
    + '[aria-label*="закры" i]:visible, button:has-text("×"):visible'
  ).first();
  if (!await close.count()) {
    result.failures.push(`custom ${kind}: visible X close control is absent`);
  } else {
    await close.click({ timeout: 5000 }).catch(error => result.failures.push(`custom ${kind}: X click failed: ${error.message}`));
    await page.waitForTimeout(800);
    if (await form.isVisible().catch(() => false)) result.failures.push(`custom ${kind}: form stayed visible after X click`);
  }
  result.actions[kind] = { trigger: triggerSnapshot, modal: modalSnapshot, screenshot: file };
}

async function auditExcluded(page, domain, result) {
  const roots = await page.locator('.csf-root').count();
  const scripts = await page.locator('script[src*="client-standard"], link[href*="client-standard"]').count();
  if (roots || scripts) result.failures.push(`excluded site has standardized forms: roots=${roots}, assets=${scripts}`);
}

function emptyAuditResult(domain, type, viewport) {
  return {
    domain,
    type,
    viewport: viewport.name,
    canonicalUrl: `https://${domain}/`,
    status: null,
    finalUrl: '',
    title: '',
    failures: [],
    warnings: [],
    consoleErrors: [],
    consoleErrorDetails: [],
    criticalConsoleErrors: [],
    pageErrors: [],
    pageErrorDetails: [],
    requestFailures: [],
    badResponses: [],
    forms: {},
    customForms: [],
    actions: {},
  };
}

async function auditView(browser, domain, type, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
  });
  let page;
  try {
    page = await context.newPage();
  } catch (error) {
    await context.close().catch(() => null);
    throw error;
  }
  const result = emptyAuditResult(domain, type, viewport);
  page.on('pageerror', error => {
    result.pageErrors.push(error.message);
    result.pageErrorDetails.push(error.stack || error.message);
  });
  page.on('console', message => {
    if (message.type() !== 'error') return;
    const value = message.text();
    const location = message.location();
    result.consoleErrors.push(value);
    result.consoleErrorDetails.push({
      message: value,
      url: location.url || '',
      lineNumber: location.lineNumber ?? null,
      columnNumber: location.columnNumber ?? null,
    });
    if (isCriticalConsoleError(value)) {
      const source = location.url
        ? ` (${location.url}:${(location.lineNumber ?? 0) + 1})`
        : '';
      result.criticalConsoleErrors.push(`critical console error: ${value}${source}`);
    }
  });
  page.on('requestfailed', request => {
    if (!isFirstParty(request.url(), domain) || !isBlockingResourceType(request.resourceType())) return;
    result.requestFailures.push(
      `request failed: ${request.resourceType()} ${request.url()} (${request.failure()?.errorText || 'unknown'})`
    );
  });
  page.on('response', response => {
    const request = response.request();
    if (response.status() < 400 || !isFirstParty(response.url(), domain)
        || !isBlockingResourceType(request.resourceType())) return;
    result.badResponses.push(
      `HTTP ${response.status()}: ${request.resourceType()} ${response.url()}`
    );
  });
  try {
    const response = await page.goto(`https://${domain}/`, {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    });
    result.status = response?.status() ?? null;
    result.finalUrl = page.url();
    await waitForVisualStability(page, result);
    result.title = await page.title();
    if (!result.status || result.status >= 400) result.failures.push(`page returned ${result.status}`);
    if (!normalize(await page.locator('body').innerText().catch(() => ''))) result.failures.push('page body is blank');
    result.pageScreenshot = await screenshot(page, domain, viewport.name, 'page');
    if (type === 'standard') await auditStandard(page, domain, viewport, result);
    if (type === 'custom') await auditCustom(page, domain, viewport, result);
    if (type === 'excluded') await auditExcluded(page, domain, result);
    if (result.pageErrors.length) result.failures.push(...result.pageErrors);
    if (result.criticalConsoleErrors.length) result.failures.push(...result.criticalConsoleErrors);
    if (result.requestFailures.length) result.failures.push(...result.requestFailures);
    if (result.badResponses.length) result.failures.push(...result.badResponses);
    const nonCriticalConsole = result.consoleErrors.filter(error => !isCriticalConsoleError(error));
    if (nonCriticalConsole.length) {
      result.warnings.push(...nonCriticalConsole.map(error => `console error: ${error}`));
    }
  } catch (error) {
    if (type === 'excluded' && KNOWN_EXCLUDED_INFRA_FAILURES.has(domain)) {
      result.warnings.push(`known excluded-site infrastructure failure: ${error.message}`);
    } else {
      result.failures.push(error.message);
    }
  } finally {
    await context.close();
  }
  result.failures = [...new Set(result.failures)];
  return result;
}

function isRetryableBrowserFailure(value) {
  return /(?:target crashed|target page, context or browser has been closed|browser has been closed|connection closed)/i
    .test(String(value || ''));
}

async function auditViewWithRetry(browser, domain, type, viewport) {
  let lastError = null;
  for (let attempt = 1; attempt <= QA_ATTEMPTS; attempt += 1) {
    try {
      const result = await auditView(browser, domain, type, viewport);
      result.attempts = attempt;
      const retryable = result.failures.some(isRetryableBrowserFailure);
      if (!retryable || attempt === QA_ATTEMPTS) return result;
      process.stdout.write(`RETRY ${domain} ${viewport.name} after browser target failure\n`);
    } catch (error) {
      lastError = error;
      if (!isRetryableBrowserFailure(error?.message) || attempt === QA_ATTEMPTS) {
        const result = emptyAuditResult(domain, type, viewport);
        result.attempts = attempt;
        result.failures.push(
          `browser infrastructure failure after ${attempt} attempt(s): ${error?.message || error}`
        );
        return result;
      }
      process.stdout.write(`RETRY ${domain} ${viewport.name} after browser infrastructure failure\n`);
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  const result = emptyAuditResult(domain, type, viewport);
  result.attempts = QA_ATTEMPTS;
  result.failures.push(
    `browser infrastructure failure after ${QA_ATTEMPTS} attempt(s): ${lastError?.message || lastError || 'unknown'}`
  );
  return result;
}

async function launchAuditBrowser() {
  const errors = [];
  for (const executablePath of BROWSER_EXECUTABLES) {
    if (!fs.existsSync(executablePath)) {
      errors.push(`${executablePath}: executable is absent`);
      continue;
    }
    for (let attempt = 1; attempt <= QA_ATTEMPTS; attempt += 1) {
      try {
        return await chromium.launch({ executablePath, headless: true });
      } catch (error) {
        errors.push(`${executablePath} attempt ${attempt}: ${error?.message || error}`);
        if (attempt < QA_ATTEMPTS) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    }
  }
  throw new Error(`browser launch failed for all configured executables: ${errors.join(' | ')}`);
}

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const targets = [
    ...STANDARD_SITES.map(domain => ({ domain, type: 'standard' })),
    ...CUSTOM_SITES.map(domain => ({ domain, type: 'custom' })),
    ...EXCLUDED_SITES.map(domain => ({ domain, type: 'excluded' })),
  ];
  const filter = process.env.TARGET_DOMAINS
    ? new Set(process.env.TARGET_DOMAINS.split(',').map(item => item.trim()).filter(Boolean))
    : null;
  const browser = await launchAuditBrowser();
  const results = [];
  try {
    const queue = targets.filter(target => !filter || filter.has(target.domain));
    let nextIndex = 0;
    async function worker() {
      while (nextIndex < queue.length) {
        const target = queue[nextIndex];
        nextIndex += 1;
        for (const viewport of VIEWPORTS) {
          process.stdout.write(`ACCEPT ${target.domain} ${viewport.name}\n`);
          const result = await auditViewWithRetry(browser, target.domain, target.type, viewport);
          results.push(result);
          fs.writeFileSync(path.join(OUTPUT, 'results.partial.json'), JSON.stringify(results, null, 2));
        }
      }
    }
    const workers = Array.from(
      { length: Math.min(QA_CONCURRENCY, queue.length) },
      () => worker()
    );
    await Promise.all(workers);
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(OUTPUT, 'results.json'), JSON.stringify(results, null, 2));
  const summary = results.map(result => ({
    domain: result.domain,
    type: result.type,
    viewport: result.viewport,
    status: result.status,
    failures: result.failures,
  }));
  fs.writeFileSync(path.join(OUTPUT, 'summary.json'), JSON.stringify(summary, null, 2));
  const failed = summary.filter(item => item.failures.length);
  process.stdout.write(`COMPLETE ${summary.length} views; ${failed.length} failed\n`);
  if (failed.length) process.exitCode = 1;
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
