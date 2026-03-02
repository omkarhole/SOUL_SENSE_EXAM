import { test, expect } from './fixtures';
import { AuthPage } from './pages/AuthPage';

test.describe('Authentication Flow', () => {
  let authPage: AuthPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
  });

  test('should display login page', async ({ page }) => {
    await authPage.goto();
    await expect(page).toHaveTitle(/Soul Sense/);
    await expect(authPage.usernameInput).toBeVisible();
    await expect(authPage.passwordInput).toBeVisible();
    await expect(authPage.submitButton).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await authPage.goto();
    await authPage.login('invalid_user', 'wrong_password');

    const errorMessage = await authPage.getErrorMessage();
    expect(errorMessage).toBeTruthy();
  });

  test('should redirect to dashboard on successful login', async ({ page }) => {
    await authPage.goto();
    await authPage.login('e2e_test_user', 'TestPass123!');

    await page.waitForURL('/dashboard', { timeout: 5000 });
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should navigate to registration page', async ({ page }) => {
    await authPage.goto();
    await authPage.registerLink.click();

    await expect(page).toHaveURL(/.*register/);
  });

  test('should register new user with wizard steps', async ({ page }) => {
    const timestamp = Date.now();
    const username = `test_user_${timestamp}`;
    const password = 'TestPass123!';

    // go through the multi-step wizard and assert headings
    await authPage.gotoRegister();
    await expect(page.locator('h3')).toHaveText('Personal Information');
    await page.fill('input[name="firstName"]', 'Jane');
    await page.fill('input[name="age"]', '30');
    await page.selectOption('select[name="gender"]', 'Female');
    await page.click('button:has-text("Continue")');

    await expect(page.locator('h3')).toHaveText('Account Details');
    await authPage.usernameInput.fill(username);
    await authPage.passwordInput.fill(password);
    await page.fill('input[name="email"]', `test${timestamp}@example.com`);
    await page.click('button:has-text("Continue")');

    await expect(page.locator('h3')).toHaveText('Review & Submit');
    await page.check('input[name="acceptTerms"]');
    await authPage.submitButton.click();

    await page.waitForURL('/dashboard', { timeout: 5000 });
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should validate required fields at each step and preserve state when navigating back', async ({ page }) => {
    await authPage.gotoRegister();
    // try to continue without filling personal info
    await page.click('button:has-text("Continue")');
    await expect(authPage.errorMessage).toBeVisible();

    // fill minimal personal info then continue
    await page.fill('input[name="firstName"]', 'Foo');
    await page.fill('input[name="age"]', '25');
    await page.selectOption('select[name="gender"]', 'Male');
    await page.click('button:has-text("Continue")');

    // now on account step, try Continue with empty credentials
    await page.click('button:has-text("Continue")');
    await expect(authPage.errorMessage).toBeVisible();

    // go back and ensure values persist
    await page.click('button:has-text("Back")');
    await expect(page.locator('input[name="firstName"]')).toHaveValue('Foo');
    await expect(page.locator('input[name="age"]')).toHaveValue('25');
    await expect(page.locator('select[name="gender"]')).toHaveValue('Male');
  });

  test('should logout successfully', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/profile');
    await authenticatedPage.click('button:has-text("Logout")');

    await expect(authenticatedPage).toHaveURL(/.*login/);
  });

  test('should remember me functionality', async ({ page, context }) => {
    await authPage.goto();
    await page.check('input[name="remember"]');
    await authPage.login('e2e_test_user', 'TestPass123!');

    await page.waitForURL('/dashboard');

    const cookies = await context.cookies();
    const rememberCookie = cookies.find(c => c.name === 'remember_token');
    expect(rememberCookie).toBeDefined();
  });
});
