# Test Coverage Documentation

This document provides an overview of all test cases created for the eClinic Backend API endpoints.

## Test Files Overview

### 1. `test_auth.py` (Existing)
**Endpoints Covered:**
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - Patient registration
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/profile` - Get user profile
- `PUT/PATCH /api/v1/auth/profile` - Update profile
- `POST /api/v1/auth/change-password` - Change password
- `GET /api/v1/auth/me` - Get current user

**Test Cases:**
- ✅ Successful login with valid credentials
- ✅ Login with invalid email
- ✅ Login with invalid password
- ✅ Successful registration
- ✅ Registration with duplicate email
- ✅ Registration with password mismatch
- ✅ Successful token refresh
- ✅ Token refresh with invalid token
- ✅ Successful logout
- ✅ Get profile authenticated
- ✅ Get profile unauthenticated
- ✅ Update profile
- ✅ Successful password change
- ✅ Password change with wrong current password

### 2. `test_services.py` (New)
**Endpoints Covered:**
- `POST /api/v1/admin/services` - Create service
- `GET /api/v1/admin/services` - List services
- `GET /api/v1/admin/services/{service_id}` - Get service by ID
- `PATCH /api/v1/admin/services/{service_id}` - Update service
- `DELETE /api/v1/admin/services/{service_id}` - Delete service

**Test Cases:**
- ✅ Create service (IN_CLINIC mode)
- ✅ Create service (TELECONSULTATION mode)
- ✅ Create service without authentication
- ✅ Create service with invalid clinic ID
- ✅ Create service with missing required fields
- ✅ Create service with invalid service mode
- ✅ List services successfully
- ✅ List services with filters (mode, bookable status)
- ✅ Get service by ID
- ✅ Get non-existent service
- ✅ Update service (partial update)
- ✅ Update service (all fields)
- ✅ Update non-existent service
- ✅ Update service without authentication
- ✅ Update service with invalid data
- ✅ Delete service successfully
- ✅ Delete non-existent service
- ✅ Delete service without authentication
- ✅ Create service with zero price
- ✅ Create service with very long name
- ✅ List services with empty result

### 3. `test_appointment_requests.py` (New)
**Endpoints Covered:**
- `POST /api/v1/appointment/requests` - Create appointment request
- `GET /api/v1/appointment/requests` - List appointment requests
- `GET /api/v1/appointment/requests/{request_id}` - Get request details
- `POST /api/v1/appointment/requests/{request_id}/accept` - Accept request
- `POST /api/v1/appointment/requests/{request_id}/reject` - Reject request

**Test Cases:**
- ✅ Create request (IN_CLINIC mode)
- ✅ Create request (TELECONSULTATION mode)
- ✅ Create request without authentication
- ✅ Create request as doctor (should fail)
- ✅ Create request with invalid doctor ID
- ✅ Create request with invalid service ID
- ✅ Create request with past date
- ✅ Create request with missing required fields
- ✅ Create request with invalid time format
- ✅ List requests as doctor
- ✅ List requests with status filter
- ✅ List requests with pagination
- ✅ List requests without authentication
- ✅ Get request details (as patient)
- ✅ Get request details (as doctor)
- ✅ Get non-existent request
- ✅ Get request without authentication
- ✅ Accept request successfully
- ✅ Accept request as patient (should fail)
- ✅ Accept non-existent request
- ✅ Accept already accepted request
- ✅ Accept already rejected request
- ✅ Reject request successfully
- ✅ Reject request without reason
- ✅ Reject request as patient (should fail)
- ✅ Reject non-existent request
- ✅ Reject already rejected request
- ✅ Reject already accepted request

### 4. `test_payments.py` (New)
**Endpoints Covered:**
- `POST /api/v1/payment/payments/initialize` - Initialize payment
- `POST /api/v1/payment/payments/webhook` - Stripe webhook handler

**Test Cases:**
- ✅ Initialize payment successfully (if Stripe configured)
- ✅ Initialize payment without authentication
- ✅ Initialize payment for non-existent request
- ✅ Initialize payment for pending request (should fail)
- ✅ Initialize payment for another patient's request (should fail)
- ✅ Webhook without signature header
- ✅ Webhook with invalid signature
- ✅ Webhook for payment succeeded event
- ✅ Webhook for payment failed event
- ✅ Webhook with unknown event type
- ✅ Webhook without body

### 5. `test_users.py` (New)
**Endpoints Covered:**
- `GET /api/v1/users/` - List users
- `GET /api/v1/users/{user_id}` - Get user details
- `POST /api/v1/users/` - Create user
- `PATCH /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `POST /api/v1/users/{user_id}/activate` - Activate user
- `POST /api/v1/users/{user_id}/deactivate` - Deactivate user
- `POST /api/v1/users/{user_id}/change-role` - Change user role
- `GET /api/v1/users/statistics` - Get user statistics
- `GET /api/v1/users/roles/list` - List available roles

**Test Cases:**
- ✅ List users successfully
- ✅ List users with pagination
- ✅ List users with role filter
- ✅ List users with active status filter
- ✅ List users with search
- ✅ List users without authentication
- ✅ List users as non-admin
- ✅ Get user details successfully
- ✅ Get non-existent user
- ✅ Get user without authentication
- ✅ Create user successfully
- ✅ Create user with doctor role
- ✅ Create user with duplicate email
- ✅ Create user without authentication
- ✅ Create user as non-admin (should fail)
- ✅ Create user with missing required fields
- ✅ Create user with invalid email
- ✅ Create user with short password
- ✅ Update user successfully
- ✅ Update user email
- ✅ Update user role
- ✅ Update non-existent user
- ✅ Update user without authentication
- ✅ Delete user successfully
- ✅ Delete non-existent user
- ✅ Delete user without authentication
- ✅ Delete own account (should fail)
- ✅ Activate user successfully
- ✅ Deactivate user successfully
- ✅ Activate non-existent user
- ✅ Change user role successfully
- ✅ Change role to invalid role
- ✅ Change role for non-existent user
- ✅ Get user statistics successfully
- ✅ Get statistics without authentication
- ✅ List roles successfully
- ✅ List roles without authentication

### 6. `test_patient_doctors.py` (New)
**Endpoints Covered:**
- `GET /api/v1/patient/doctors/search` - Search doctors

**Test Cases:**
- ✅ Search doctors successfully
- ✅ Search doctors with specialty filter
- ✅ Search doctors with availability day filter
- ✅ Search doctors with time filter
- ✅ Search doctors with pagination
- ✅ Search doctors with multiple filters
- ✅ Search doctors with empty result
- ✅ Search doctors with invalid page
- ✅ Search doctors with invalid limit
- ✅ Search doctors with very high limit

### 7. `test_profile.py` (Existing)
**Endpoints Covered:**
- Profile completion and update endpoints
- Patient profile management
- Doctor profile management

### 8. `test_notifications.py` (Existing)
**Endpoints Covered:**
- Notification management endpoints

### 9. `test_doctor_services.py` (New)
**Endpoints Covered:**
- `GET /api/v1/doctor/services/available` - Get available services
- `GET /api/v1/doctor/services` - List doctor services
- `GET /api/v1/doctor/services/{service_id}` - Get doctor service
- `POST /api/v1/doctor/services` - Create doctor service assignment
- `PATCH /api/v1/doctor/services/{service_id}` - Update doctor service
- `DELETE /api/v1/doctor/services/{service_id}` - Delete doctor service

**Test Cases:**
- ✅ Get available services successfully
- ✅ Get available services without authentication
- ✅ Get available services as patient (should fail)
- ✅ List doctor services successfully
- ✅ Get specific doctor service
- ✅ Get non-existent doctor service
- ✅ Create doctor service assignment
- ✅ Create duplicate assignment
- ✅ Create with invalid service ID
- ✅ Update doctor service
- ✅ Delete doctor service

### 10. `test_doctor_service_availability.py` (New)
**Endpoints Covered:**
- `GET /api/v1/doctor/availability-services` - List service availability assignments
- `POST /api/v1/doctor/availability-services` - Assign service to availability
- `PATCH /api/v1/doctor/availability-services/{id}` - Update assignment
- `DELETE /api/v1/doctor/availability-services/{id}` - Delete assignment

**Test Cases:**
- ✅ List availability services
- ✅ List with availability filter
- ✅ Assign service to availability (IN_CLINIC)
- ✅ Assign service to availability (TELECONSULTATION)
- ✅ Assign duplicate service
- ✅ Assign with invalid availability
- ✅ Assign with invalid service
- ✅ Update assignment
- ✅ Delete assignment

### 11. `test_doctor_service_pricing.py` (New)
**Endpoints Covered:**
- `GET /api/v1/doctor/service-pricing` - List pricing
- `POST /api/v1/doctor/service-pricing` - Set price
- `PATCH /api/v1/doctor/service-pricing/{id}` - Update price
- `DELETE /api/v1/doctor/service-pricing/{id}` - Delete price

**Test Cases:**
- ✅ List pricing successfully
- ✅ Set price successfully
- ✅ Set price for invalid service
- ✅ Update price
- ✅ Delete price

### 12. `test_availability.py` (New)
**Endpoints Covered:**
- `GET /api/v1/doctors/{doctor_id}/availability` - Get doctor availability
- `POST /api/v1/availability` - Create availability
- `PUT /api/v1/availability/{id}` - Update availability
- `DELETE /api/v1/availability/{id}` - Delete availability
- `GET /api/v1/doctors/{doctor_id}/time-off` - Get time-off
- `POST /api/v1/time-off` - Create time-off
- `DELETE /api/v1/time-off/{id}` - Delete time-off

**Test Cases:**
- ✅ Get doctor availability
- ✅ Create availability
- ✅ Create with invalid time range
- ✅ Update availability
- ✅ Delete availability
- ✅ Get time-off
- ✅ Create time-off
- ✅ Create time-off with past date
- ✅ Delete time-off

### 13. `test_appointment_booking.py` (New)
**Endpoints Covered:**
- `GET /api/v1/patient/doctors/{doctor_id}/summary` - Get doctor summary
- `GET /api/v1/patient/doctors/{doctor_id}/consultation-types` - Get consultation types
- `GET /api/v1/patient/doctors/{doctor_id}/time-slots` - Get available time slots
- `POST /api/v1/patient/appointments` - Book appointment

**Test Cases:**
- ✅ Get doctor summary
- ✅ Get summary with invalid doctor
- ✅ Get consultation types
- ✅ Get time slots
- ✅ Get time slots for past date
- ✅ Book appointment successfully
- ✅ Book with past date
- ✅ Book with invalid doctor

### 14. `test_locations_languages_medical_services.py` (New)
**Endpoints Covered:**
- `GET /api/v1/locations/countries` - Get countries
- `GET /api/v1/locations/countries/{country_id}/states` - Get states by country
- `GET /api/v1/locations/states/{state_id}/cities` - Get cities by state
- `GET /api/v1/locations/states` - Get all states
- `GET /api/v1/locations/cities` - Get all cities
- `GET /api/v1/languages/languages` - Get languages
- `GET /api/v1/medical-services/` - Get medical services

**Test Cases:**
- ✅ Get countries successfully
- ✅ Get states by country
- ✅ Get states for invalid country
- ✅ Get cities by state
- ✅ Get all states
- ✅ Get all cities
- ✅ Get languages
- ✅ Get medical services
- ✅ Verify no auth required for public endpoints

### 15. `test_profile_comprehensive.py` (New)
**Endpoints Covered:**
- `GET /api/v1/profile` - Get profile
- `POST /api/v1/profile/complete` - Complete profile
- `PUT /api/v1/profile` - Update profile
- `GET /api/v1/profile/patient/personal-info` - Get patient personal info
- `PUT /api/v1/profile/patient/personal-info` - Update patient personal info
- `GET /api/v1/profile/patient/medical-info` - Get patient medical info
- `PUT /api/v1/profile/patient/medical-info` - Update patient medical info
- `GET /api/v1/profile/doctor` - Get doctor profile
- `PUT /api/v1/profile/doctor` - Update doctor profile
- `GET /api/v1/profile/contact-details` - Get contact details
- `PUT /api/v1/profile/contact-details` - Update contact details
- `POST /api/v1/profile/image` - Upload profile image

**Test Cases:**
- ✅ Get profile
- ✅ Complete profile
- ✅ Complete profile with missing fields
- ✅ Update profile
- ✅ Get/update patient personal info
- ✅ Get/update patient medical info
- ✅ Get/update doctor profile
- ✅ Get doctor profile as patient (should fail)
- ✅ Get/update contact details
- ✅ Upload profile image
- ✅ Upload without file

### 16. `test_notifications.py` (New)
**Endpoints Covered:**
- `GET /api/v1/notifications` - List notifications
- `GET /api/v1/notifications/{id}` - Get notification
- `POST /api/v1/notifications` - Create notification
- `PATCH /api/v1/notifications/{id}` - Update notification
- `GET /api/v1/notifications/settings` - Get settings
- `PUT /api/v1/notifications/settings` - Update settings
- `PUT /api/v1/notifications/mark-all-read` - Mark all as read

**Test Cases:**
- ✅ List notifications
- ✅ List with pagination
- ✅ Get specific notification
- ✅ Get non-existent notification
- ✅ Create notification (admin only)
- ✅ Create as non-admin (should fail)
- ✅ Update notification
- ✅ Get/update notification settings
- ✅ Mark all notifications as read

### 17. `test_middleware.py` (Existing)
**Endpoints Covered:**
- Middleware functionality tests

## Test Coverage Summary

### Total Endpoints Tested: ~88 endpoints
### Test Files Created/Enhanced: 17 files
### Total Test Cases: 300+ test cases

## Test Categories

### 1. **Success Cases**
   - All endpoints tested with valid inputs
   - Proper response format validation
   - Data integrity checks

### 2. **Authentication & Authorization**
   - Unauthenticated access attempts
   - Unauthorized role access attempts
   - Token validation
   - Permission checks

### 3. **Validation & Error Handling**
   - Missing required fields
   - Invalid data formats
   - Invalid UUIDs
   - Boundary conditions
   - Edge cases

### 4. **Business Logic**
   - State transitions (pending → accepted → rejected)
   - Duplicate prevention
   - Ownership validation
   - Status-based operations

### 5. **Edge Cases**
   - Empty results
   - Very large inputs
   - Zero/null values
   - Past dates
   - Invalid time formats

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test file:
```bash
pytest tests/test_services.py
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test class:
```bash
pytest tests/test_services.py::TestCreateService
```

### Run specific test:
```bash
pytest tests/test_services.py::TestCreateService::test_create_service_success
```

## Test Database

All tests use SQLite in-memory databases that are:
- Created before each test
- Dropped after each test
- Isolated from each other
- Independent of the main database

## Fixtures

Common fixtures used across tests:
- `test_clinic` - Creates a test clinic
- `admin_user` - Creates an admin user
- `admin_token` - Gets admin authentication token
- `patient_user` - Creates a patient user
- `patient_token` - Gets patient authentication token
- `doctor_user` - Creates a doctor user
- `doctor_token` - Gets doctor authentication token
- `test_service` - Creates a test service
- `appointment_request_data` - Provides appointment request data

## Notes

1. **Stripe Integration**: Payment tests may fail if Stripe is not configured. Tests handle this gracefully.

2. **Database Migrations**: Ensure all migrations are run before executing tests that require specific table structures.

3. **Test Isolation**: Each test is independent and can be run in any order.

4. **Mocking**: Consider adding mocks for external services (Stripe, email, SMS) for faster test execution.

5. **Performance**: Some tests may be slow due to database operations. Consider using fixtures more efficiently.

## Future Enhancements

1. Add integration tests for complete workflows
2. Add performance/load tests
3. Add security penetration tests
4. Add API contract tests
5. Add end-to-end workflow tests
6. Add tests for remaining endpoints:
   - Doctor Services endpoints
   - Doctor Service Availability endpoints
   - Doctor Service Pricing endpoints
   - Availability endpoints
   - Locations endpoints
   - Languages endpoints
   - Medical Services endpoints
   - Appointment Booking endpoints
   - Notifications endpoints
