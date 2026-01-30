import { test, expect } from '@playwright/test';

test('Knowledge Flow: Create Node and Update Mastery Score', async ({ page }) => {
  // 1. Log in to the dashboard
  await page.goto('/login');
  await page.getByRole('button', { name: 'Login' }).click();

  // Verify redirect to dashboard
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByText('Knowledge Dashboard')).toBeVisible();

  // 2. Create a new 'Knowledge Node' for 'Raft Consensus'
  const uniqueLabel = `Raft Consensus ${Date.now()}`;
  await page.getByRole('button', { name: 'Create Node' }).click();
  await expect(page.getByText('Create Knowledge Node')).toBeVisible();

  await page.fill('input[placeholder="Enter node label"]', uniqueLabel);
  await page.getByRole('button', { name: 'Create', exact: true }).click();

  // 3. Verify it appears in the Graph visualization
  // Wait for the node to appear. ReactFlow renders nodes with class react-flow__node-{type}
  const nodeLocator = page.locator('.react-flow__node-custom').filter({ hasText: uniqueLabel });
  await expect(nodeLocator).toBeVisible();
  await expect(nodeLocator).toContainText('Mastery: 0%');

  // 4. Ensure the Mastery Score updates after a simulated quiz
  // Click "Simulate Quiz" button inside the node
  await nodeLocator.getByRole('button', { name: 'Simulate Quiz' }).click();

  // Verify mastery score updates (e.g., to 100%)
  // The backend sets it to 100.0, the frontend displays it.
  // Depending on formatting, it might be "100" or "100.0".
  // In Dashboard component: `Mastery: {data.score}%`
  // Backend returns float 100.0. JS might display as 100.
  await expect(nodeLocator).toContainText('Mastery: 100%');
});
