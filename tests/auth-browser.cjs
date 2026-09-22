// Exercises real Clerk form loading in preview without creating an account.
const { chromium } = require('@playwright/test');
const { execSync } = require('node:child_process');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({
    executablePath: execSync('which chromium').toString().trim(),
    args: ['--no-sandbox']
  });
  try {
    const base = `https://${process.env.REPLIT_DEV_DOMAIN}`;
    for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport, ignoreHTTPSErrors: true });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(base);
      if (viewport.width < 600) await page.locator('.navbar-toggler').click();
      await page.getByRole('link', { name: 'Create account', exact: true }).click();
      await page.locator('#clerk-auth-root input[name=emailAddress]').waitFor();
      assert.equal(await page.locator('#clerk-auth-root input[name=password]').isVisible(), true);
      assert.equal(await page.locator('#clerk-auth-root').getByRole('button', { name: /Continue with Google/ }).isVisible(), true);
      console.log(`${viewport.width}px: Create account link and real Clerk registration form PASS`);

      await page.locator('#clerk-auth-root').getByRole('button', { name: 'Continue', exact: true }).click();
      assert.equal(new URL(page.url()).pathname, '/sign-up');
      assert.equal(await page.locator('#clerk-auth-root input:invalid').count() > 0, true);
      console.log(`${viewport.width}px: Empty registration blocked PASS`);

      await page.locator('#clerk-auth-root').getByRole('link', { name: 'Sign in', exact: true }).click();
      await page.locator('#clerk-auth-root input[name=identifier]').waitFor();
      assert.equal(new URL(page.url()).pathname, '/sign-in');
      console.log(`${viewport.width}px: Sign-in form and registration-to-sign-in navigation PASS`);
      assert.deepEqual(errors, []);
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });