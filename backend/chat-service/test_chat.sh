#!/bin/bash
# Quick Chat Service Test Script

BASE_URL="http://localhost:8001"
BACKEND_URL="http://localhost:8000/backend/api-fast"

echo "=========================================="
echo "Chat Service Testing"
echo "=========================================="
echo ""

# 1. Health Check
echo "1. Health Check"
HEALTH=$(curl -s "$BASE_URL/health")
echo "$HEALTH"
echo ""

# 2. Instructions
echo "2. To test with authentication:"
echo "   export DOCTOR_EMAIL='your-doctor@email.com'"
echo "   export DOCTOR_PASSWORD='password'"
echo "   ./test_chat.sh"
echo ""
echo "3. For detailed testing, see TESTING.md"
