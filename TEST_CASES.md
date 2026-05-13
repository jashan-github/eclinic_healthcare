# E-Clinic — QA Test Cases

Manual regression cases for the five merged bug-fix PRs. Each section maps to one PR. Every case targets a specific bug that was fixed — these are **regression tests**, not exhaustive happy-path coverage.

## Setup

1. **Backend running:**
   ```bash
   cd backend/fastapi-backend
   docker compose up -d
   ```
2. **Frontend running:**
   ```bash
   cd frontend
   npm run dev
   ```
3. Open the browser with **DevTools → Network + Console tabs visible** during every flow. Some bugs (gender casing, console.log leaks, payload shape) are only verifiable from those panels.

Each row has columns:
- **ID** — a unique identifier per case
- **Steps** — what to do in the browser
- **Expected** — what should happen after the fix

Cases marked **🔴 critical** target production-blocking bugs; if any fail, the regression is severe.

---

# PR #1 — `fix/auth-form-validation`

## Login (`/auth/login`)

| ID | Steps | Expected |
|---|---|---|
| AUTH-01 | Click Login with both fields empty + terms unchecked | Three toasts: required field, password min 8, must agree to terms. **No** API call in Network tab. |
| AUTH-02 | Email tab → enter `foo` → password `password123` → check terms → Login | Toast: "Please enter a valid email address". No API call. |
| AUTH-03 | Email tab → valid email → password `1234` (4 chars) → check terms → Login | Toast: "Password must be at least 8 characters". |
| AUTH-04 🔴 | Valid email + valid password, **uncheck** terms, click Login | Toast: "You must agree to the terms". **Page does NOT reload** (was `preventDefault` ordering bug). |
| AUTH-05 | Valid email + valid password + terms checked → Login | Success toast → redirect to dashboard. |
| AUTH-06 | Backend returns 500 with no `errors` field | Toast shows fallback message. **No** `TypeError` in console. |

## Admin Login

| ID | Steps | Expected |
|---|---|---|
| AUTH-07 🔴 | Login with valid admin credentials | Redirect to admin dashboard. Navigate to a different protected route — should NOT bounce back to login (`setIsAuthenticated(true)` fix). |
| AUTH-08 | Submit with `< 8 char` password | Toast, no API call. |

## Signup (`/auth/signup`)

| ID | Steps | Expected |
|---|---|---|
| AUTH-09 | Click Create Account with all fields empty | Multiple toasts (one per missing field). |
| AUTH-10 | Click DOB picker → try to pick tomorrow | Date picker UI **blocks** future dates (`max` attr). |
| AUTH-11 | Bypass via DevTools → inject a future DOB into state → submit | Toast: "Date of birth cannot be in the future". |
| AUTH-12 | Don't pick a country, fill everything else, submit | Toast: "Country is required". |
| AUTH-13 🔴 | **Critical — original bug.** Fill everything correctly, pick "Male" radio, submit. Inspect Network tab → POST `/v1/auth/register` payload | Payload `gender` is **lowercase** `"male"`. Server returns 200 (was 422 before fix — backend rejects TitleCase). |
| AUTH-14 | Repeat for "Female" and "Other" | Payload values: `"female"`, `"other"`. |
| AUTH-15 | Type different password + confirmation | Toast: "Passwords do not match". |

## Forgot Password (`/auth/forgot-password`)

| ID | Steps | Expected |
|---|---|---|
| AUTH-16 | Open the page | Heading reads **"Forgot Password"** (was "Reset Password"). |
| AUTH-17 | Submit with empty email | Toast: "This field is required". |
| AUTH-18 | Submit with `not-an-email` | Toast: invalid email format. |
| AUTH-19 | Submit valid email | Success toast: reset link sent. |

## Reset Password (`/auth/reset-password?token=...&email=...`)

| ID | Steps | Expected |
|---|---|---|
| AUTH-20 | Open URL **without** `token` query param | Redirect to `/auth/reset-password-verification-failed`. |
| AUTH-21 | Open URL with `token` but **without** `email` | Same redirect (was previously letting form submit with empty email). |
| AUTH-22 | Valid URL → enter `1234` (5 chars) for new password + match confirm → submit | Toast: "Password must be at least 8 characters". Stays on form. |
| AUTH-23 | Mismatched password and confirm | Toast: "Passwords do not match". |
| AUTH-24 🔴 | Backend returns 400 (e.g. password rejected by server complexity rule) | Form **stays mounted**, toast shows error. (Was redirecting to verification-failed dead-end.) |
| AUTH-25 | Backend returns 401 or 403 (token expired) | Redirects to verification-failed. |

---

# PR #2 — `fix/patient-form-validation`

## New Patient Form (Doctor — Add Patient flow)

### Schema + casing

| ID | Steps | Expected |
|---|---|---|
| PAT-01 🔴 | Submit with valid data, gender = "Male" radio. Inspect Network tab payload | Payload `gender: "male"` (lowercase). Was TitleCase, breaking every patient creation. |
| PAT-02 | Repeat with Female / Other | Payload `"female"` / `"other"`. |
| PAT-03 | Display labels next to radios still read **Male / Female / Other** | UI labels TitleCase, payload lowercase. |

### Form-level errors actually render

| ID | Steps | Expected |
|---|---|---|
| PAT-04 🔴 | Fill in only first_name, leave required fields blank, submit | Each field shows an inline error from `state.meta.errors` (TanStack Form `{ fields }` shape — was `{ errors }` so all errors were silently swallowed). |

### Validation tightening

| ID | Steps | Expected |
|---|---|---|
| PAT-05 | Submit empty → check email field | If touched, show "Please enter a valid email address" only when typed something invalid. Empty allowed (optional). |
| PAT-06 | Type `foo` in email | Toast: invalid email (was accepted before — backend uses EmailStr). |
| PAT-07 | Address: empty default, submit | No "Address is required" error (old `min(1).optional()` bug — fixed via `or(literal(''))`). |
| PAT-08 | City: same as ADDR-07 | No spurious validation error on empty default. |
| PAT-09 | Pincode: empty default | No error on empty (was `length(6)` failing on `""`). |
| PAT-10 | Pincode: type "12" (2 chars) | Toast: "Pincode is too short" (min 3 international). |
| PAT-11 | Pincode: type "1234567890" (10 chars) | Accepted (max 10). |
| PAT-12 | Pincode: type "12345678901" (11 chars) | Toast: "Pincode is too long". |
| PAT-13 | Age: type "abc" | Toast: "Age must be a number". |
| PAT-14 | Age: type "-5" | Toast: not a positive integer. |
| PAT-15 | Age: type "200" (3 digits) | Accepted (regex allows 1–3 digits). |
| PAT-16 | Age: type "1000" (4 digits) | Toast: not 1–3 digits. |
| PAT-17 | DOB: type a future date in DevTools | Toast: "Date of birth must be a valid date in the past". |
| PAT-18 | DOB: type random non-date string | Same toast. |

### Age ↔ DOB cross-validation

| ID | Steps | Expected |
|---|---|---|
| PAT-19 | Age = 25, DOB = 1965-01-01 (computed age ~60) | Toast: "Age (25) does not match date of birth (computed age 60)". |
| PAT-20 | Age = 25, DOB = 25 years ago today | Accepts (within ±1 year tolerance). |
| PAT-21 | Age = 25, DOB = 26 years ago today (off-by-one for not-yet-had-birthday case) | Accepts (±1 tolerance). |

### UHID hint

| ID | Steps | Expected |
|---|---|---|
| PAT-22 | Click Generate, then clear the UHID field, submit | Toast: "UHID is required — click Generate to create one" (was just "UHID is required"). |

### Country selector + phone

| ID | Steps | Expected |
|---|---|---|
| PAT-23 | Phone country code field is now a **searchable Select**, not a disabled `+91` chip | Confirm. Type "United" → US options appear in dropdown. |
| PAT-24 | Default value still `91` (India) for backward compat | Confirm. |
| PAT-25 | Change country to US (+1), enter phone "5551234", submit | Schema accepts (`4-15` digits). |
| PAT-26 | Phone "12" (2 digits) | Toast: "Phone number must be 4-15 digits". |

---

# PR #3 — `fix/admin-bug-cleanup`

## Locations — Add Dialog

| ID | Steps | Expected |
|---|---|---|
| ADM-01 🔴 | Open Add Location dialog → close → open → repeat 5×. Watch console. | No "Rendered more hooks than during the previous render" error (hooks-after-`return null` was a real React rules-of-hooks violation). |
| ADM-02 | Phone field accepts `+1 (234) 567-8900` | Verbatim accepted (was rejected by old `type="number"`). |
| ADM-03 | Phone: leading zero `01234567890` | Preserved (was stripped by `type="number"`). |
| ADM-04 | Phone: type `1e5` | Just `1` accepted; `e5` ignored (was passed as `1e5` numeric value). |

## Locations — Edit Dialog

| ID | Steps | Expected |
|---|---|---|
| ADM-05 🔴 | Click Edit on any location row | Form opens with prefilled data, no console error. |
| ADM-06 🔴 | Open → close × 5 | No hooks-order crash. |
| ADM-07 | Same phone-input behavior as ADM-02 / ADM-03 | Same. |

## Visits Sidebar (Patient → any patient → Visits tab)

| ID | Steps | Expected |
|---|---|---|
| ADM-08 🔴 | View a patient with **zero visits** | Empty state renders, no "rendered fewer hooks" error in console. |
| ADM-09 | View a patient with visits | Templates load, first clinic auto-selects in dropdown. **No** `Auto-selected clinic ID:` log in console (was leaking the UUID). |

## Notifications Settings (Admin → Settings → Notifications)

| ID | Steps | Expected |
|---|---|---|
| ADM-10 | Open page while API still pending | "Loading…" shows, no destructure crash. |
| ADM-11 | Toggle a notification → click Save | PATCH/POST fires successfully. |

## Waiver Settings (Admin → Settings → Waiver)

| ID | Steps | Expected |
|---|---|---|
| ADM-12 | Open page, watch browser console | **No** `true` / `false` log on every render (`console.log(!!settings?.waiver_enabled)` removed). |
| ADM-13 | Toggle waiver enabled, change percentage, click Save | PATCH/POST fires. |

## Webinar — Create Dialog (Admin → Webinars → Create)

| ID | Steps | Expected |
|---|---|---|
| ADM-14 | Click Publish with all fields empty | Toast: "Please fill in all required fields". |
| ADM-15 🔴 | Fill everything **except description**, observe Publish button | Button stays **disabled** (was clickable → toast → return — but UI hinted submit was possible). |
| ADM-16 | Date input: try to pick yesterday | UI blocks (`min={today}`). |
| ADM-17 | Set start=11:00, end=10:00, click Publish | Toast: "End time must be after start time". |
| ADM-18 | Set start=10:00, end=10:00 | Same toast (equal treated as invalid). |
| ADM-19 🔴 | type=paid, price=`abc`, submit | Toast: "Please enter a valid price greater than 0". **No** webinar created (was creating with `price: 0`). |
| ADM-20 🔴 | type=paid, price=`0`, submit | Same toast. |
| ADM-21 | type=paid, price=`-50`, submit | Same toast. |
| ADM-22 | "Custom" participant limit, leave it empty, submit | Toast: "Please enter a valid participant limit" (was sending `NaN`). |
| ADM-23 | All valid, paid, price=100, submit | Webinar created. Network payload: `price: 100`, `participant_limit: <int>`. |

## Webinar — Edit Dialog

| ID | Steps | Expected |
|---|---|---|
| ADM-24 | Edit a **past** webinar | Form opens, dialog accepts the past date (no `min` guard on edit). |
| ADM-25 | Edit a future webinar, set end_time before start_time, submit | Toast. |
| ADM-26 | Same parsing guards as create | Same toasts. |

## Doctor & Calendar Create-New-Service

| ID | Steps | Expected |
|---|---|---|
| ADM-27 | Open Create New Service dialog, watch console | No `console.log(user, 136)` printing the user object. |
| ADM-28 | (Calendar variant) Submit form, watch console | No `Form Data:` log printing the payload. |

---

# PR #4 — `fix/admin-validation-alignment`

## Users — Add User Dialog

| ID | Steps | Expected |
|---|---|---|
| USR-01 | Submit with name = "A" (1 char) | Toast: "Name must be at least 2 characters" (backend `min_length=2`). |
| USR-02 | Submit with email = "foo" | Toast: "Please enter a valid email address" (was passing `type=email` HTML check but no regex). |
| USR-03 | Submit with name=valid, email=`foo@bar` | Same toast (regex requires TLD). |
| USR-04 | Submit with name=valid, email=valid, phone="0" (invalid E.164 — leading 0 after `+91`) | Toast: "Please enter a valid phone number". |
| USR-05 | Submit with name=valid, email=valid, phone="9876543210" + country=`91` | Combined `+919876543210` matches `^\+?[1-9]\d{1,14}$`. Accepted. |
| USR-06 🔴 | Switch role to "Healthcare Provider" (doctor), leave Education blank, submit | Toast: "Education is required for healthcare providers" (backend requires this). |
| USR-07 🔴 | Doctor role, fill education but no specializations selected, submit | Toast: "At least one specialization is required for healthcare providers". |
| USR-08 | Doctor role, all required fields filled, submit | User created. Network payload: `specializations` is an array of UUIDs (audit was wrong; this was already correct — but verify regression-free). |

## Speciality — Add Medical Service Dialog

| ID | Steps | Expected |
|---|---|---|
| MED-01 | Type 256 chars in Speciality Name | Input `maxLength=255` truncates at 255. |
| MED-02 | Bypass via DevTools, force >255 chars, submit | Toast: "Speciality name must be 255 characters or fewer". |
| MED-03 | Submit empty/whitespace-only name | Toast: "Speciality name is required". |

## Vital Settings — Add Vital Dialog

| ID | Steps | Expected |
|---|---|---|
| VIT-01 | Vital Name max 255 chars (input + toast on bypass) | Same as MED-01/02. |
| VIT-02 | Unit max 50 chars | Input truncates at 50, toast on bypass. |
| VIT-03 | Data Type max 50 chars | Same. |

## Commissions — Edit Modal

| ID | Steps | Expected |
|---|---|---|
| COM-01 | Set rate = 0, click Update | Toast: "Rate must be between 1% and 100%" (backend `min=1`; was previously `min=0`). |
| COM-02 | Set rate = 101 | Same toast (added `max=100` cap). |
| COM-03 | Rate = 50, submit | Accepted. |

## Webinar — Title Length (both create + edit)

| ID | Steps | Expected |
|---|---|---|
| WBN-01 | Type 256 chars in webinar title | `maxLength=255` truncates input. |
| WBN-02 | Bypass via DevTools, force >255 chars, submit | Toast: "Title must be 255 characters or fewer". |

## Doctor Calendar — Create New Service (price)

| ID | Steps | Expected |
|---|---|---|
| SVC-01 | Price empty | No error (still optional). |
| SVC-02 | Price = "abc" | Schema rejects: "Price must be a positive number with up to 2 decimal places". |
| SVC-03 | Price = "0" | Schema rejects (must be > 0). |
| SVC-04 | Price = "-100" | Same. |
| SVC-05 | Price = "10.999" (3 decimals) | Schema rejects (max 2 decimals). |
| SVC-06 | Price = "10.99" | Accepted. |
| SVC-07 | Price = "100" | Accepted. |

---

# PR #5 — `fix/workspaces-routing-validation`

## Workspace layout redirect

| ID | Steps | Expected |
|---|---|---|
| WSP-01 🔴 | Log in to any account, then navigate to `/workspaces/create-workspace` | Auto-redirects to `/app/dashboard` (was redirecting to `/setup/sign-in` which 404'd). |
| WSP-02 | Logged-out user navigates to `/workspaces/create-workspace` | Page loads normally. |

## Workspace Header

| ID | Steps | Expected |
|---|---|---|
| WSP-03 | Open `/workspaces/create-profile` directly | Header back button is a circular `ActionIcon` with the back arrow. |
| WSP-04 | Inspect Mantine `variant` prop | Was `variant="secondary"` (invalid) → now `variant="default"` (valid Mantine API). |
| WSP-05 | On create-profile, click back button | Goes to previously-visited page (uses `router.history.back()`). |
| WSP-06 | Open create-profile via direct URL load (no history), click back button | Falls back to `/workspaces/sign-in`. |

## Multi-step navigation

| ID | Steps | Expected |
|---|---|---|
| WSP-07 🔴 | On `/workspaces/create-workspace`, fill all fields validly, click Next | Navigates to `/workspaces/create-profile` (was only `console.log`). |
| WSP-08 | Notice that step-1 form values do **not** carry over to step-2 | Confirmed by design — TODO in code, no shared store wired up yet. Out of scope for this PR. |

## Form validation tightening (both create-workspace and create-profile)

| ID | Steps | Expected |
|---|---|---|
| WSP-09 | First name = 256 chars | Toast: "First name must be 255 characters or fewer". |
| WSP-10 | Last name = 256 chars | Same. |
| WSP-11 | Mobile = `123456789` (9 digits) | Toast: "Mobile number must be at least 10 digits". |
| WSP-12 | Mobile = `12345678901` (11 digits) | Toast: "Mobile number must be at most 10 digits" (was unbounded above min). |
| WSP-13 | DOB = future date | Toast: "Date of birth must be a valid date in the past". |
| WSP-14 | DOB = `not-a-date` | Same toast (refine catches invalid Date parse). |

## Sign-in placeholder

| ID | Steps | Expected |
|---|---|---|
| WSP-15 | Visit `/workspaces/sign-in` | Renders "Workspace Sign In — This page is not yet implemented." (was `<div>Workspace - Sign In</div>` — visually impossible to tell it was a placeholder). |

---

# PR — `feat/doctor-currency-and-ongoing-experience` (D3-A)

## Edit Service Modal — Currency selector

| ID | Steps | Expected |
|---|---|---|
| CUR-01 | Open Edit Service modal on any existing service | A new "Currency" `Select` appears above "Price". (Was no selector; currency was locked to whatever was in the data.) |
| CUR-02 | Open dropdown | Lists USD, INR, EUR, GBP, AED, CAD, AUD, SGD, JPY. Searchable. |
| CUR-03 | Edit a service whose backend `currency` is `"INR"` | Modal opens with INR pre-selected and the Price leftSection shows `₹` (was showing literal text `"XCG"` — the Caribbean guilder code, a real visible bug). |
| CUR-04 | Edit a service whose backend `currency` is an unknown code like `"XYZ"` | Modal falls back to USD without crashing. |
| CUR-05 | Change currency to EUR, observe Price leftSection | Shows `€`. |
| CUR-06 | Change currency to AED, save | Network payload includes `currency: "AED"`. |
| CUR-07 | Try to clear the Select via X button | `allowDeselect={false}` prevents an empty state; the previous selection stays. |

## Experience Form — "Currently work here"

| ID | Steps | Expected |
|---|---|---|
| EXP-01 | Open Add Experience form | New `Checkbox` labeled **"I currently work here"** between Start Year and End Year. Unchecked by default. |
| EXP-02 | Fill title + hospital + start year, **check** "I currently work here", click Save | End Year is **disabled** with placeholder "Ongoing". Form submits successfully. Network payload has `end_year: ""` (or null). |
| EXP-03 | Same as EXP-02 but uncheck the box after checking | End Year re-enables. Validation kicks back in — Save is blocked until a valid year is picked. |
| EXP-04 | Edit an existing experience whose `end_year` is empty/null | The checkbox is **pre-checked** automatically; End Year is disabled with "Ongoing". |
| EXP-05 | Edit an existing experience with a real `end_year` | Checkbox unchecked; End Year shows the saved value. |
| EXP-06 | Checkbox checked, leave end_year empty, submit | No "End year required" validation error (was previously blocking ongoing roles). |
| EXP-07 | Checkbox unchecked, end_year = `2050` | Validation blocks: "End year cannot be in the future". |
| EXP-08 | Checkbox unchecked, end_year < start_from | Validation blocks: "End year must be on or after start year". |
| EXP-09 | Checkbox checked, start_from = 2010, end_year empty | Saves successfully. The cross-year refine is skipped when `is_current=true`. |

---

# Out of scope / known gaps

These are surfaced for awareness — do **not** treat as test failures:

- New-patient form's `fetch('/api/patients')` hits a non-existent endpoint; submit silently fails. Wiring to `patientsService` is feature work.
- Workspace sign-in form is not implemented; the placeholder is intentional.
- Step-1 → Step-2 state persistence in the workspace flow is not wired.
- Doctor webinar hosting/create remains backend-blocked; doctors can view/join supported webinars but cannot create new webinars until a doctor-scoped create endpoint exists.
- ~50 pre-existing lint errors elsewhere in the codebase (unrelated to these PRs).
- No automated test infrastructure in the repo. These cases are manual.

---

# PR — `fix/calendar-services-create-button` (Doctor service bug pass)

## Doctor Calendar — Create Service

| ID | Steps | Expected |
|---|---|---|
| DOC-SVC-01 | Login as doctor, open `/app/calendar`, switch to Services | **Create New Service** is visible. |
| DOC-SVC-02 | Click Create New Service | Service Name is a dropdown populated from `/v1/doctor/services/available`; it does not call `/v1/admin/service-types`. |
| DOC-SVC-03 | Select an available service, duration 5+ minutes, price with max 2 decimals, submit | Network calls `/v1/doctor/services`; service appears in the doctor Services list after refresh/refetch. |
| DOC-SVC-04 | Open Duration dropdown as doctor | 2-minute and 3-minute options are not shown; minimum option is 5 minutes. |
| DOC-SVC-05 | Enter service name or nickname longer than 255 chars in an admin create flow | Frontend validation blocks the submit with a max-length error. |

## Doctor Calendar — Edit Service

| ID | Steps | Expected |
|---|---|---|
| DOC-SVC-06 | Open Edit Service, change duration, click Update | Network calls `/v1/doctor/services/{assignmentId}` with `slot_duration_minutes`; list refreshes with the updated duration. |
| DOC-SVC-07 | Edit price to `0`, negative value, letters, or more than 2 decimal places | Frontend blocks submit and shows a price validation toast. |
| DOC-SVC-08 | Change currency and save | Network pricing payload includes the selected ISO currency code. |

## Doctor Webinar Chat

| ID | Steps | Expected |
|---|---|---|
| DOC-WEB-01 | In webinar chat, paste/type more than 1000 characters | Input is capped at 1000 characters and cannot send a longer message. |

---

# PR — `fix/staff-module-validation` (Staff module bug pass)

## Messages

| ID | Steps | Expected |
|---|---|---|
| STF-MSG-01 | Open `/app/messages`, select an active conversation, leave message empty and click send | Message is not sent; inline validation shows "Message cannot be empty". |
| STF-MSG-02 | Type or paste more than 5000 characters | Input is capped/validated; send is blocked and the user sees max-length feedback. |
| STF-MSG-03 | Type a valid message and press Enter | Message is encrypted and sent through the existing WebSocket flow. |

## Calendar — Block Calendar

| ID | Steps | Expected |
|---|---|---|
| STF-CAL-01 | Open Block Calendar form | Optional **Reason** textarea is visible. |
| STF-CAL-02 | Enter a reason and submit | Network payload includes `reason` with the entered trimmed text. |
| STF-CAL-03 | Leave reason empty and submit | Calendar block still succeeds; payload sends an empty reason for backward compatibility. |
| STF-CAL-04 | Enter more than 500 characters in reason | Frontend validation blocks submit with a max-length error. |

## Calendar — Create Service

| ID | Steps | Expected |
|---|---|---|
| STF-SVC-01 | In Create Service, enter a service name over 255 chars | Zod validation blocks submit with a max-length error. |
| STF-SVC-02 | In Create Service, enter a nickname over 255 chars | Zod validation blocks submit with a max-length error. |
| STF-SVC-03 | Login as doctor, create service from available services | Uses doctor-scoped `/v1/doctor/services`; no admin endpoint is called. |

---

# Critical regression checklist (5 minutes)

If you only run a subset, run these first — they cover the highest-impact bugs across all 5 PRs:

1. **AUTH-04** — Login terms-unchecked does not reload page
2. **AUTH-13** — Signup gender payload is lowercase `"male"` in Network tab
3. **AUTH-24** — Reset-password 400 stays on form
4. **PAT-01** — Patient gender payload lowercase
5. **PAT-04** — TanStack form errors render inline per field
6. **ADM-01 / ADM-05 / ADM-08** — Hooks-order crash on dialog open/close cycles
7. **ADM-15** — Webinar Publish disabled without description
8. **ADM-19** — Webinar paid price `abc` blocked
9. **USR-06 / USR-07** — Doctor role education + specialization required
10. **WSP-01** — `/workspaces/create-workspace` redirect goes to dashboard, not 404
11. **WSP-07** — Workspace step-1 → step-2 navigates correctly
