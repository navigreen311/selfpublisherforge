# W27: Frontend Tests for Forgot Password + MFA Settings Pages

## Files to create
- `frontend/src/app/(auth)/forgot-password/__tests__/page.test.tsx` — NEW
- `frontend/src/app/(dashboard)/settings/security/__tests__/page.test.tsx` — NEW

## Task

### 1. Write forgot password page tests

```tsx
describe('ForgotPasswordPage', () => {
  it('renders email input form', () => {
    render(<ForgotPasswordPage />);
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send|reset/i })).toBeInTheDocument();
  });

  it('shows success message after submission', async () => {
    jest.spyOn(api, 'post').mockResolvedValue({});
    render(<ForgotPasswordPage />);
    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /send|reset/i }));
    await waitFor(() => {
      expect(screen.getByText(/check your email/i)).toBeInTheDocument();
    });
  });

  it('shows success even for non-existent email (no enumeration)', async () => { ... });
  it('has link back to login', () => { ... });
});
```

### 2. Write MFA settings page tests

```tsx
describe('SecuritySettingsPage', () => {
  it('shows enable MFA button when MFA is off', () => { ... });
  it('displays QR code after setup initiation', async () => { ... });
  it('shows verification code input during setup', () => { ... });
  it('shows disable button when MFA is enabled', () => { ... });
  it('requires password to disable MFA', () => { ... });
  it('displays backup codes during setup', () => { ... });
});
```

Write at least 8 tests total (4 per page).
