const { test, expect } = require('@playwright/test');

test.describe('Chat E2E', () => {
  test('send message and receive response', async ({ page }) => {
    await page.goto('http://localhost:8000');
    
    // Check page title
    await expect(page).toHaveTitle(/Agent Chat/);
    
    // Type message
    await page.fill('#input', '你好');
    await page.click('#send');
    
    // Wait for response
    await page.waitForSelector('.msg.assistant', { timeout: 30000 });
    
    // Check user message appears
    const userMsg = page.locator('.msg.user');
    await expect(userMsg).toContainText('你好');
    
    // Check assistant response appears
    const assistantMsg = page.locator('.msg.assistant').first();
    await expect(assistantMsg).toBeVisible();
  });
  
  test('clear history', async ({ page }) => {
    await page.goto('http://localhost:8000');
    
    // Send a message first
    await page.fill('#input', '测试');
    await page.click('#send');
    await page.waitForSelector('.msg.assistant', { timeout: 30000 });
    
    // Click clear button
    await page.click('#clear-btn');
    
    // Check chat is cleared
    const chatContent = await page.locator('#chat').textContent();
    expect(chatContent).toBe('');
  });
});
