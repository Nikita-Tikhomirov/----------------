const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const DOMAIN = 'mchs-spb.ru';
const EXPECTED_MX = ['10 mx1.beget.com.', '20 mx2.beget.com.'];
const EXPECTED_SPF = 'v=spf1 include:beget.com ~all';
const TARGET_MX = 'emx.mail.ru';
const TARGET_SPF = 'v=spf1 include:beget.com include:_spf.mail.ru ~all';
const output = path.resolve('output/mchs-spb-2026-07-24');
const password = process.env.BEGET_PANEL_PASS;

if (!password) throw new Error('BEGET_PANEL_PASS is required');
if (process.env.APPLY_DNS !== '1') throw new Error('Set APPLY_DNS=1 to change DNS');

async function login(page) {
  await page.goto('https://cp.beget.com/', {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.waitForTimeout(2000);
  if (!page.url().includes('/login')) return;
  await page.locator('input[type="text"], input[name*="login" i]').first().fill('nousroc9');
  await page.locator('input[type="password"]').first().fill(password);
  await page.locator('button[type="submit"], input[type="submit"]').first().click();
  await page.waitForURL(/\/main(?:$|\?)/, { timeout: 30000 });
}

async function selectDomain(page) {
  await page.goto('https://cp.beget.com/dns', {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.waitForTimeout(6000);
  const selector = page.locator('[st="dns-select-domain-input"]');
  await selector.click();
  await selector.fill(DOMAIN);
  await page.getByText(DOMAIN, { exact: true }).last().click();
  await page.waitForTimeout(3500);
}

async function openRootEditor(page) {
  const rootTitle = page.locator('[st="dns-list-item-title"]').filter({
    hasText: /^mchs-spb\.ru$/,
  }).first();
  const rootItem = rootTitle.locator('xpath=ancestor::*[@st="dns-item-list"][1]');
  await rootTitle.locator('xpath=..').click();
  await page.waitForTimeout(1200);

  const records = await rootItem.locator('[st="dns-record-data"]').allTextContents();
  const normalized = records.map((value) => value.trim());
  for (const expected of [...EXPECTED_MX, EXPECTED_SPF]) {
    if (!normalized.includes(expected)) {
      throw new Error(`DNS baseline changed; missing ${expected}`);
    }
  }
  await rootItem.locator('[st="button-dns-edit-node"]').click();
  await page.waitForTimeout(1500);
  return rootItem;
}

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    headless: false,
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  });
  const context = await browser.newContext({ viewport: { width: 1360, height: 900 } });
  const page = await context.newPage();
  await login(page);
  await selectDomain(page);
  const rootItem = await openRootEditor(page);

  const mxSelectors = page.locator('[st="dns-edit-modal-selector-mx"]');
  for (let index = 0; index < await mxSelectors.count(); index += 1) {
    await mxSelectors.nth(index).click();
  }
  await page.locator('[st="dns-edit-modal-selector-txt"]').click();
  await page.waitForTimeout(500);

  const preferences = page.locator(
    '[st="input-dns-edit-preference"] input, input[st="input-dns-edit-preference"]',
  );
  const exchanges = page.locator(
    '[st="input-dns-edit-exchange"] input, input[st="input-dns-edit-exchange"]',
  );
  const txtData = page.locator(
    '[st="input-dns-edit-txtdata"] textarea, textarea[st="input-dns-edit-txtdata"]',
  );
  const preferenceCount = await preferences.count();
  const exchangeCount = await exchanges.count();
  if (preferenceCount !== 2 || exchangeCount !== 2) {
    throw new Error(
      `Unexpected MX editor layout: preferences=${preferenceCount}, exchanges=${exchangeCount}`,
    );
  }
  if (await exchanges.nth(0).inputValue() !== 'mx1.beget.com') {
    throw new Error('First MX value changed before update');
  }
  if (await exchanges.nth(1).inputValue() !== 'mx2.beget.com') {
    throw new Error('Second MX value changed before update');
  }
  if (await txtData.inputValue() !== EXPECTED_SPF) {
    throw new Error('SPF value changed before update');
  }

  await preferences.nth(0).fill('10');
  await exchanges.nth(0).fill(TARGET_MX);
  await txtData.fill(TARGET_SPF);
  const removeButtons = page.locator('[st="button-dns-edit-remove-record"]');
  if (await removeButtons.count() !== 4) {
    throw new Error('Unexpected number of root DNS records');
  }
  await removeButtons.nth(2).click();
  await page.screenshot({ path: path.join(output, 'beget-dns-before-save.png'), fullPage: false });
  await page.locator('[st="button-dns-edit-save"]').click();
  await page.waitForTimeout(4500);

  if (await page.locator('[st="button-dns-edit-save"]').isVisible().catch(() => false)) {
    throw new Error('DNS editor remained open after save');
  }
  const updatedRecords = (await rootItem.locator('[st="dns-record-data"]').allTextContents())
    .map((value) => value.trim());
  if (!updatedRecords.includes(`10 ${TARGET_MX}.`)) {
    throw new Error('Target MX is not visible after save');
  }
  if (updatedRecords.some((value) => value.includes('mx1.beget.com') || value.includes('mx2.beget.com'))) {
    throw new Error('Old Beget MX is still present after save');
  }
  if (!updatedRecords.includes(TARGET_SPF)) {
    throw new Error('Target SPF is not visible after save');
  }
  await page.screenshot({ path: path.join(output, 'beget-dns-after-save.png'), fullPage: false });
  fs.writeFileSync(
    path.join(output, 'beget-dns-update-result.json'),
    JSON.stringify({ domain: DOMAIN, records: updatedRecords }, null, 2),
  );
  console.log(JSON.stringify({ domain: DOMAIN, records: updatedRecords }, null, 2));
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
