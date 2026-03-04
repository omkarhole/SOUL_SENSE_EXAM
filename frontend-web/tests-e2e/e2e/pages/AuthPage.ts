import type { Page, Locator } from '@playwright/test';

export class AuthPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly loginLink: Locator;
  readonly registerLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('input[name="username"]');
    this.passwordInput = page.locator('input[name="password"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
    this.loginLink = page.locator('a[href="/login"]');
    this.registerLink = page.locator('a[href="/register"]');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async gotoRegister() {
    await this.page.goto('/register');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  // helper that fills out each step of the wizard
  async completeRegistration({
    username,
    password,
    email,
    firstName,
    lastName,
    age,
    gender,
  }: {
    username: string;
    password: string;
    email?: string;
    firstName?: string;
    lastName?: string;
    age?: string;
    gender?: string;
  }) {
    await this.gotoRegister();
    // step 1 personal
    if (firstName) await this.page.fill('input[name="firstName"]', firstName);
    if (lastName) await this.page.fill('input[name="lastName"]', lastName);
    if (age) await this.page.fill('input[name="age"]', age);
    if (gender) await this.page.selectOption('select[name="gender"]', gender);
    await this.page.click('button:has-text("Continue")');

    // step 2 account
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    if (email) await this.page.fill('input[name="email"]', email);
    await this.page.click('button:has-text("Continue")');

    // step 3 terms
    await this.page.check('input[name="acceptTerms"]');
    await this.submitButton.click();
  }

  async getErrorMessage(): Promise<string> {
    return await this.errorMessage.textContent() || '';
  }
}
