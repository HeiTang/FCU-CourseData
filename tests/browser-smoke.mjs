// Pass a Playwright Page already opened at the local production preview.
export default async function smoke(page) {
  const check = (condition, message) => {
    if (!condition) throw new Error(message);
  };
  const base = new URL('./', page.url()).href;
  check(['localhost', '127.0.0.1'].includes(new URL(base).hostname), 'Local preview required');
  const latest = await page.locator('#sem option').first().getAttribute('value');
  const storageKey = 'plan:' + latest;
  const savedPlan = await page.evaluate((key) => localStorage.getItem(key), storageKey);
  const errors = [];
  const onError = (error) => errors.push(error.message);
  page.on('pageerror', onError);
  try {
    await page.evaluate((key) => localStorage.setItem(key, 'broken-json'), storageKey);
    await page.goto(base + '#ys=invalid&slot=99-88');
    await page.waitForFunction(() => document.querySelectorAll('#results .row').length === 50);
    check(await page.locator('#sem').inputValue() === latest, 'Invalid semester fallback');
    check(await page.locator('#slotchip').isHidden(), 'Invalid slot ignored');

    const first = page.locator('#results .row').first();
    await first.hover();
    check(/貼得下|撞在一起|還沒排/.test(await page.locator('#verdict').innerText()), 'Hover preview');
    await first.click();
    await page.reload();
    await page.waitForFunction(() => document.querySelector('#st-count').textContent === '1');
    await page.locator('#q').fill('工程');
    check(Number(await page.locator('#count').innerText()) > 0, 'Search results');
    await page.locator('#q').press('Escape');
    await page.locator('#grid td[data-day="3"][data-period="6"]').click();
    await page.reload();
    await page.waitForFunction(() => !document.querySelector('#slotchip').hidden);
    check(/週三 第 6 節/.test(await page.locator('#slotchip').innerText()), 'Shared slot restored');
    await page.locator('#clear').click();

    await page.route('**/data/1001.json', (route) => route.fulfill({ status: 503, body: 'unavailable' }));
    await page.locator('#sem').selectOption('1001');
    await page.getByText('課程資料載入失敗，請重新整理或切換學期再試。').waitFor();
    await page.unroute('**/data/1001.json');
    await page.locator('#sem').selectOption(latest);
    await page.waitForFunction(() => document.querySelectorAll('#results .row').length === 50);

    await page.route('**/data/1001.json', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 350));
      await route.continue();
    });
    await page.locator('#sem').selectOption('1001');
    await page.locator('#sem').selectOption('1131');
    await page.waitForTimeout(650);
    check(await page.locator('#sem').inputValue() === '1131', 'Selected semester');
    check(await page.locator('#count').innerText() === '3613', 'Stale response ignored');
    await page.setViewportSize({ width: 390, height: 844 });
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile overflow');
    check(errors.length === 0, errors.join('\n'));
    return 'browser smoke passed';
  } finally {
    await page.unroute('**/data/1001.json');
    await page.evaluate(({ key, value }) => {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
    }, { key: storageKey, value: savedPlan });
    page.off('pageerror', onError);
  }
}
