"""
Sentoo Payment Gateway Client
Handles API communication with Sentoo payment gateway
"""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from decimal import Decimal
import httpx
from loguru import logger


class SentooClient:
    """Client for Sentoo Payment Gateway API"""
    
    def __init__(
        self,
        merchant_id: str,
        merchant_secret: str,
        api_url: str = "https://api.sentoo.com/v1"
    ):
        """
        Initialize Sentoo client
        
        Args:
            merchant_id: Sentoo Merchant ID
            merchant_secret: Sentoo Merchant Secret
            api_url: Sentoo API base URL
        """
        self.merchant_id = merchant_id
        self.merchant_secret = merchant_secret
        self.api_url = api_url.rstrip('/')
        self.timeout = 30.0  # 30 seconds timeout
    
    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for request authentication
        
        Args:
            data: Request data to sign
            
        Returns:
            HMAC signature string
        """
        # Sort keys for consistent signing
        sorted_data = dict(sorted(data.items()))
        
        # Create string to sign
        message = json.dumps(sorted_data, separators=(',', ':'), sort_keys=True)
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.merchant_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        use_form_data: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Sentoo API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request data
            use_form_data: If True, send as form data instead of JSON
            
        Returns:
            Response data dictionary
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        # Prepare request data
        if data is None:
            data = {}
        
        # Prepare headers - Sentoo uses X-SENTOO-SECRET header
        headers = {
            'X-SENTOO-SECRET': self.merchant_secret
        }
        
        try:
            logger.info(f"Sentoo API Request: {method} {url}")
            
            with httpx.Client(timeout=self.timeout) as client:
                if method.upper() == 'GET':
                    response = client.get(url, headers=headers, params=data)
                elif method.upper() == 'POST':
                    if use_form_data:
                        # Send as form data (application/x-www-form-urlencoded)
                        response = client.post(url, headers=headers, data=data)
                    else:
                        # Send as JSON
                        headers['Content-Type'] = 'application/json'
                        response = client.post(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Log request/response for debugging
                logger.info(f"Sentoo API Response: {response.status_code}")
                logger.info(f"Sentoo API Response Headers: {dict(response.headers)}")
                logger.info(f"Sentoo API Response Body (first 1000 chars): {response.text[:1000]}")
                
                # Raise exception for non-2xx responses
                response.raise_for_status()
                
                # Try to parse as JSON, but handle text responses too
                try:
                    json_response = response.json()
                    logger.info(f"Sentoo API JSON Response: {json_response}")
                    return json_response
                except Exception as json_error:
                    # If response is not JSON, return as text
                    logger.warning(f"Sentoo API response is not JSON: {json_error}. Response: {response.text[:500]}")
                    # Try to parse as text/HTML - might be a redirect URL or HTML page
                    return {"raw_response": response.text, "status_code": response.status_code, "content_type": response.headers.get("content-type", "unknown")}
        
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            error_message = None
            try:
                error_json = e.response.json()
                # Extract error message from nested structure
                if isinstance(error_json, dict):
                    if 'error' in error_json:
                        error_obj = error_json['error']
                        if isinstance(error_obj, dict):
                            error_message = error_obj.get('message', str(error_obj))
                        else:
                            error_message = str(error_obj)
                    else:
                        error_message = str(error_json)
                else:
                    error_message = str(error_json)
            except:
                error_message = error_text
            
            logger.error(f"Sentoo API HTTP error: {e.response.status_code} - {error_message or error_text}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request data: {data}")
            
            if e.response.status_code == 401:
                raise Exception(f"Sentoo API authentication failed (401 Unauthorized). Please verify your merchant secret (X-SENTOO-SECRET). Error: {error_message or error_text}")
            elif e.response.status_code == 402:
                # 402 usually means payment required or business logic validation failed
                raise Exception(f"Sentoo API request failed (402): {error_message or error_text}. Please check: 1) Merchant account is active, 2) Currency is supported, 3) Amount is within limits, 4) All required fields are provided correctly.")
            elif e.response.status_code == 404:
                raise Exception(f"Sentoo API endpoint not found (404). Please verify the API URL and endpoint path. URL: {url}")
            else:
                raise Exception(f"Sentoo API error ({e.response.status_code}): {error_message or error_text}")
        except httpx.RequestError as e:
            logger.error(f"Sentoo API request error: {str(e)}")
            raise Exception(f"Sentoo API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Sentoo API unexpected error: {str(e)}")
            raise
    
    def create_payment(
        self,
        amount: Decimal,
        currency: str,
        reference_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        generate_qr: bool = True,
        description: Optional[str] = None,
        expires: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment transaction using Sentoo API
        
        Based on Sentoo API documentation:
        https://developer.sentoo.io/mdp/create-new-transaction
        
        Args:
            amount: Payment amount (will be converted to cents)
            currency: Currency code (e.g., 'USD', 'EUR', 'ANG')
            reference_id: Your internal reference ID
            metadata: Additional metadata (optional)
            return_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment (optional)
            generate_qr: Whether to generate QR code for payment (optional)
            description: Payment description (optional)
            expires: Expiration date in ISO 8601 format (optional)
            
        Returns:
            Payment response with payment_id, payment_url, qr_code, etc.
        """
        from datetime import datetime, timedelta
        from urllib.parse import urlencode
        
        # Convert amount to cents (Sentoo expects amount in smallest currency unit)
        # For most currencies, this is cents (divide by 0.01)
        amount_cents = int(float(amount) * 100)
        
        # Prepare form data with sentoo_ prefix
        form_data = {
            'sentoo_merchant': self.merchant_id,
            'sentoo_currency': currency.upper(),
            'sentoo_amount': str(amount_cents),
        }
        
        # Add description (use reference_id if not provided)
        if description:
            form_data['sentoo_description'] = description
        else:
            form_data['sentoo_description'] = f"Payment for {reference_id}"
        
        # Add return URL (required)
        if return_url:
            form_data['sentoo_return_url'] = return_url
        else:
            # Default return URL if not provided
            form_data['sentoo_return_url'] = 'https://replace.this.url/?return='
        
        # Add expiration date (optional, default to 30 days from now)
        if expires:
            form_data['sentoo_expires'] = expires
        else:
            # Default: 30 days from now in ISO 8601 format with timezone
            # Format: 2024-01-31T00:00:00+01:00 (will be URL encoded by httpx)
            from datetime import timezone
            expires_date = datetime.now(timezone.utc) + timedelta(days=30)
            # Format with UTC offset (+00:00)
            form_data['sentoo_expires'] = expires_date.strftime('%Y-%m-%dT%H:%M:%S%z')
            # Ensure proper format: replace +0000 with +00:00
            if form_data['sentoo_expires'].endswith('+0000'):
                form_data['sentoo_expires'] = form_data['sentoo_expires'].replace('+0000', '+00:00')
            elif form_data['sentoo_expires'].endswith('-0000'):
                form_data['sentoo_expires'] = form_data['sentoo_expires'].replace('-0000', '+00:00')
        
        # Add cancel URL if provided
        if cancel_url:
            form_data['sentoo_cancel_url'] = cancel_url
        
        # Add metadata as additional fields if needed
        if metadata:
            for key, value in metadata.items():
                form_data[f'sentoo_{key}'] = str(value)
        
        try:
            logger.info(f"Creating Sentoo payment: {reference_id}, Amount: {amount} {currency} ({amount_cents} cents)")
            logger.info(f"Sentoo form data keys: {list(form_data.keys())}")
            logger.info(f"Sentoo form data values: {[(k, v[:50] if isinstance(v, str) and len(v) > 50 else v) for k, v in form_data.items()]}")
            logger.info(f"Sentoo API URL: {self.api_url}")
            response = self._make_request('POST', '/payment/new', form_data, use_form_data=True)
            logger.info(f"Sentoo payment created successfully: {reference_id}")
            logger.debug(f"Sentoo response: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to create Sentoo payment: {str(e)}", exc_info=True)
            raise
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Get payment status
        
        Args:
            payment_id: Sentoo payment ID
            
        Returns:
            Payment status information
        """
        try:
            # Try singular endpoint first (matches /payment/new pattern)
            try:
                response = self._make_request('GET', f'/payment/{payment_id}', {})
                logger.info(f"Successfully retrieved payment using /payment/{payment_id}")
                return response
            except Exception as e1:
                error_msg = str(e1)
                if '404' in error_msg or 'not found' in error_msg.lower():
                    logger.info(f"Endpoint /payment/{payment_id} not found, trying /payments/{payment_id}")
                    response = self._make_request('GET', f'/payments/{payment_id}', {})
                    return response
                else:
                    raise
        except Exception as e:
            logger.error(f"Failed to get Sentoo payment status: {str(e)}")
            raise
    
    def verify_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify transaction status directly from Sentoo API
        
        Uses the correct Sentoo endpoint:
        GET /v1/payment/status/<merchant_id>/<transaction_id>
        
        This should be used to verify payment status instead of relying on
        URL redirect parameters, which can be manipulated.
        
        Args:
            transaction_id: Sentoo transaction ID (payment token received from Sentoo)
            
        Returns:
            Transaction status information with:
            - status: PENDING, ISSUED, SUCCESS, FAILED, CANCELLED, REJECTED
            - is_paid: Boolean indicating if payment is complete
            - transaction_id: Sentoo transaction ID
            - amount: Payment amount details (if available)
            - responses: Processor responses (if available)
        """
        try:
            # Use the correct Sentoo endpoint: /payment/status/<merchant_id>/<transaction_id>
            endpoint = f'/payment/status/{self.merchant_id}/{transaction_id}'
            logger.info(f"Fetching transaction status from Sentoo: {endpoint}")
            
            response = self._make_request('GET', endpoint, {})
            logger.info(f"Sentoo transaction status response: {response}")
            
            # Parse Sentoo response format:
            # {"success": {"code": 200, "message": "pending|success|issued|rejected|cancelled", "data": {...}}}
            status = None
            payment_data = {}
            
            if isinstance(response, dict) and 'success' in response:
                success_obj = response['success']
                if isinstance(success_obj, dict):
                    # Status is in success.message field
                    status = success_obj.get('message', 'UNKNOWN')
                    # Additional data may be in success.data
                    if 'data' in success_obj:
                        payment_data = success_obj['data']
            
            # Normalize status to uppercase
            status = str(status).upper() if status else 'UNKNOWN'
            
            # Map Sentoo status values to our internal status
            # Sentoo statuses: pending, issued, success, rejected, cancelled
            status_mapping = {
                'SUCCESS': 'COMPLETED',
                'PENDING': 'PENDING',
                'ISSUED': 'PENDING',  # Issued means waiting for payment
                'REJECTED': 'FAILED',
                'CANCELLED': 'FAILED',
                'CANCELED': 'FAILED',
                'FAILED': 'FAILED'
            }
            
            normalized_status = status_mapping.get(status, status)
            is_paid = status == 'SUCCESS'
            
            logger.info(f"Sentoo status: {status}, normalized: {normalized_status}, is_paid: {is_paid}")
            
            # Build result
            result = {
                'status': normalized_status,
                'sentoo_status': status,  # Original Sentoo status
                'is_paid': is_paid,
                'transaction_id': transaction_id,
                'raw_response': response
            }
            
            # Add amount details if available
            if isinstance(payment_data, dict):
                amount_data = payment_data.get('amount', {})
                if isinstance(amount_data, dict):
                    result['total_paid'] = amount_data.get('total_paid')
                    result['paid_currency'] = amount_data.get('paid_currency')
                    result['original_amount'] = amount_data.get('original_amount')
                
                result['receiving_account_id'] = payment_data.get('receiving_account_id')
                result['responses'] = payment_data.get('responses', [])
            
            logger.info(f"Parsed payment status: status={normalized_status}, is_paid={is_paid}, sentoo_status={status}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify Sentoo transaction status: {str(e)}", exc_info=True)
            raise
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Webhook payload bytes
            signature: Signature from webhook header
            webhook_secret: Webhook secret key
            
        Returns:
            True if signature is valid
        """
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Cancel a payment
        
        Args:
            payment_id: Sentoo payment ID
            
        Returns:
            Cancellation response
        """
        try:
            response = self._make_request('POST', f'/payments/{payment_id}/cancel', {})
            logger.info(f"Sentoo payment cancelled: {payment_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to cancel Sentoo payment: {str(e)}")
            raise
