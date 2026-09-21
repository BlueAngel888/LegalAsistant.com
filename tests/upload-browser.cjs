// Run against the isolated browser_harness.py, never the live app.
const { chromium } = require('@playwright/test');
const { execSync } = require('node:child_process');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({
    executablePath: execSync('which chromium').toString().trim(),
    headless: true, args: ['--no-sandbox']
  });
  try {
    for (const flow of ['free', 'paid']) {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      // Real Clerk is deliberately excluded: identity is simulated by the harness.
      await page.route('**/*.clerk.accounts.dev/**', route => route.abort());
      await page.goto('http://127.0.0.1:5001/test-login');
      assert.equal(await page.locator('#submitBtn').isDisabled(), true);
      console.log(`${flow}: STEP 1 empty upload disabled PASS`);
      await page.locator('#file').setInputFiles({
        name: 'synthetic-contract.txt', mimeType: 'text/plain',
        buffer: Buffer.from('Synthetic contract. Example Alpha supplies consulting to Example Beta. Fee EUR 100. Payment due in 30 days. Either party may terminate with 14 days notice.')
      });
      await page.selectOption('#document_country', 'RO');
      await page.selectOption('#analysis_language', 'en');
      assert.equal(await page.locator('#submitBtn').isEnabled(), true);
      console.log(`${flow}: STEP 2 file selection and fields PASS`);
      await page.locator('#submitBtn').click();
      await page.waitForURL('**/checkout');
      assert.match(await page.locator('body').innerText(), /synthetic-contract.txt/);
      console.log(`${flow}: STEP 3 upload -> checkout PASS`);
      if (flow === 'free') {
        await page.fill('#discountCode', 'INVALID-TEST');
        await page.click('#applyDiscountBtn');
        await page.waitForFunction(() => document.querySelector('#discountMessage').textContent.includes('Invalid'));
        await page.fill('#discountCode', 'LETSGO');
        await page.click('#applyDiscountBtn');
        await page.locator('#free-access-form').waitFor({ state: 'visible' });
        console.log('free: STEP 4 invalid then valid discount PASS');
        await page.locator('#free-access-form button[type=submit]').click();
      } else {
        await page.click('#checkout-button');
      }
      await page.waitForURL('**/success*');
      assert.match(await page.locator('body').innerText(), /SIMULATED AI ANALYSIS/);
      assert.match(await page.locator('body').innerText(), /Review the obligations/);
      assert.deepEqual(errors, []);
      console.log(`${flow}: STEP 5 final result render, no JS errors PASS (AI/payment simulated)`);
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });