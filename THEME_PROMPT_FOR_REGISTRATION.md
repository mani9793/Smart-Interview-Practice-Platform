# Prompt for Cursor: Match Smart Interview Practice theme (registration / login)

**Give this entire section below to your friend. She can copy it and paste it into Cursor when working on registration and login. No access to your codebase is required.**

---

## Copy from here (paste into Cursor)

Use this exact design system for the Smart Interview Practice project’s **registration and login** pages so they match the rest of the app.

### 1. Base template (templates/base.html)

If the project doesn’t have this yet, create or update the base template with:

- **In `<head>`:**  
  - Bootstrap 5.3 CSS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css`  
  - Bootstrap Icons: `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css`  
  - Google Font: Plus Jakarta Sans  
    `https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap`

- **In a `<style>` block, add these CSS variables and classes:**

```css
:root {
    --sip-nav: #0f172a;
    --sip-primary: #0d9488;
    --sip-primary-hover: #0f766e;
    --sip-bg: #f8fafc;
    --sip-card: #ffffff;
    --sip-text: #1e293b;
    --sip-muted: #64748b;
    --sip-border: #e2e8f0;
}
body {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    background: var(--sip-bg);
    color: var(--sip-text);
    min-height: 100vh;
}
.navbar-sip {
    background: var(--sip-nav) !important;
    padding: 0.75rem 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}
.navbar-sip .navbar-brand { font-weight: 700; font-size: 1.2rem; color: #fff !important; }
.navbar-sip .nav-link {
    color: rgba(255,255,255,0.9) !important;
    font-weight: 500;
    padding: 0.5rem 0.75rem !important;
    border-radius: 0.375rem;
}
.navbar-sip .nav-link:hover {
    color: #fff !important;
    background: rgba(255,255,255,0.1);
}
.btn-sip-primary {
    background: var(--sip-primary);
    border-color: var(--sip-primary);
    color: #fff;
    font-weight: 500;
}
.btn-sip-primary:hover {
    background: var(--sip-primary-hover);
    border-color: var(--sip-primary-hover);
    color: #fff;
}
.card-sip {
    background: var(--sip-card);
    border: 1px solid var(--sip-border);
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.page-title { font-weight: 700; color: var(--sip-text); margin-bottom: 0.5rem; }
.text-muted-sip { color: var(--sip-muted); }
.form-control, .form-select {
    border-radius: 8px;
    border-color: var(--sip-border);
}
.form-control:focus, .form-select:focus {
    border-color: var(--sip-primary);
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.15);
}
main { padding: 2rem 0 3rem; }
```

- **Before `</body>`:**  
  Bootstrap JS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js`

- **Navbar:** Use `class="navbar navbar-expand-lg navbar-dark navbar-sip"`. Brand: “Smart Interview Practice” with icon `bi bi-journal-check`. Nav links: Practice, Question Sets, History (adjust URLs to match the app’s url names). Use `class="nav-link"` and Bootstrap Icons: `bi bi-play-circle`, `bi bi-collection`, `bi bi-clock-history`.

- **Main content:** Wrap in `<main class="container">`. Show Django `messages` as Bootstrap alerts (`alert alert-{{ message.tags }} alert-dismissible fade show`) with a close button. Include `{% block content %}{% endblock %}`.

### 2. Registration and login templates

- **Both must extend the base template:** `{% extends 'base.html' %}`.

- **Layout for the form page:**  
  One main card:  
  `<div class="card card-sip shadow-sm p-4" style="max-width: 32rem;">`

- **Page title:**  
  `<h1 class="page-title h3 mb-4">`  
  With an icon before the text:  
  - Register: `<i class="bi bi-person-plus-fill text-primary me-2"></i>`  
  - Login: `<i class="bi bi-box-arrow-in-right text-primary me-2"></i>`

- **Form:**
  - Use `method="post"` and `{% csrf_token %}`.
  - Each field in: `<div class="mb-3">`.
  - Label: `<label for="id_..." class="form-label fw-medium">`.
  - Inputs: add `class="form-control"` (or `form-select` for selects). Base template styles them.
  - Errors: `<div class="form-text text-danger">{{ field.errors }}</div>`.

- **Buttons:**
  - Wrapper: `<div class="d-flex gap-2">`.
  - Submit: `class="btn btn-sip-primary"` (e.g. “Register” or “Login”).
  - Cancel or back link: `class="btn btn-outline-secondary"`.

- **Extra line under the form:**  
  e.g. “Already have an account? Log in.” / “Don’t have an account? Register.”  
  Use `class="text-muted-sip mt-3"` and normal `<a>` links.

Apply this so registration and login look and behave like the rest of the Smart Interview Practice app (same colors, fonts, card style, and primary button).

---

## End of prompt
