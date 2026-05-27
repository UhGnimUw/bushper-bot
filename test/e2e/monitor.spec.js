const { test, expect } = require('@playwright/test');

test.describe('Monitor E2E', () => {
  test('monitor page loads', async ({ page }) => {
    await page.goto('http://localhost:8000/monitor');
    
    await expect(page).toHaveTitle(/系统监控/);
    
    // Check stats cards appear
    await expect(page.locator('.stat')).toHaveCount(4);
    
    // Wait for data to load
    await page.waitForTimeout(2000);
    
    // Check total requests card exists
    await expect(page.locator('#total-requests')).toBeVisible();
  });
  
  test('feishu page loads', async ({ page }) => {
    await page.goto('http://localhost:8000/feishu');
    
    await expect(page).toHaveTitle(/飞书会话/);
    
    // Check sessions panel appears
    await expect(page.locator('.sessions h2')).toContainText('会话列表');
    
    // Check conversations panel appears  
    await expect(page.locator('.conversations h2')).toContainText('对话详情');
  });
});
