# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now, get_datetime, add_days, cstr, flt, cint
from frappe import _
import json
import re
import requests
from datetime import datetime, timedelta
import hashlib
import base64
from typing import Dict, List, Any, Optional


# API Utilities
def get_api_settings(service_name: str) -> Dict[str, Any]:
	"""Get API settings for a specific service"""
	try:
		settings = frappe.get_single("Lead Intelligence Settings")
		
		if service_name == "google_places":
			return {
				"enabled": settings.google_places_enabled,
				"api_key": settings.get_password("google_places_api_key"),
				"rate_limit": 1000  # per day
			}
		
		elif service_name == "openai":
			return {
				"enabled": settings.openai_enabled,
				"api_key": settings.get_password("openai_api_key"),
				"rate_limit": 3000  # per day
			}
		
		elif service_name == "sendgrid":
			return {
				"enabled": settings.sendgrid_enabled,
				"api_key": settings.get_password("sendgrid_api_key"),
				"rate_limit": 100  # per hour
			}
		
		elif service_name == "salesforce":
			return {
				"enabled": settings.salesforce_enabled,
				"client_id": settings.salesforce_client_id,
				"client_secret": settings.get_password("salesforce_client_secret"),
				"username": settings.salesforce_username,
				"password": settings.get_password("salesforce_password"),
				"security_token": settings.get_password("salesforce_security_token")
			}
		
		else:
			return {"enabled": False}
		
	except Exception as e:
		frappe.log_error(f"Error getting API settings for {service_name}: {str(e)}", "Lead Intelligence Utils")
		return {"enabled": False}


def check_api_rate_limit(service_name: str, user: str = None) -> bool:
	"""Check if API rate limit is exceeded"""
	try:
		if not user:
			user = frappe.session.user
		
		# Get today's usage
		from lead_intelligence.lead_intelligence.doctype.lead_intelligence_usage_stats.lead_intelligence_usage_stats import get_or_create_daily_stats
		stats = get_or_create_daily_stats()
		
		# Get rate limits
		api_settings = get_api_settings(service_name)
		rate_limit = api_settings.get("rate_limit", 1000)
		
		# Check current usage
		current_usage = 0
		if service_name == "google_places":
			current_usage = stats.google_places_calls or 0
		elif service_name == "openai":
			current_usage = stats.openai_calls or 0
		elif service_name == "sendgrid":
			current_usage = stats.email_calls or 0
		
		return current_usage < rate_limit
		
	except Exception as e:
		frappe.log_error(f"Error checking rate limit for {service_name}: {str(e)}", "Lead Intelligence Utils")
		return False


def track_api_usage(service_name: str, cost: float = 0.0, user: str = None):
	"""Track API usage and cost"""
	try:
		if not user:
			user = frappe.session.user
		
		from lead_intelligence.lead_intelligence.doctype.lead_intelligence_usage_stats.lead_intelligence_usage_stats import track_api_usage as track_usage
		track_usage(service_name, cost, user)
		
	except Exception as e:
		frappe.log_error(f"Error tracking API usage for {service_name}: {str(e)}", "Lead Intelligence Utils")


# Data Validation Utilities
def validate_email(email: str) -> bool:
	"""Validate email address format"""
	if not email:
		return False
	
	pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
	return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
	"""Validate phone number format"""
	if not phone:
		return False
	
	# Remove common formatting characters
	clean_phone = re.sub(r'[\s\-\(\)\+]', '', str(phone))
	
	# Check if it's a valid phone number (7-15 digits)
	return len(clean_phone) >= 7 and len(clean_phone) <= 15 and clean_phone.isdigit()


def validate_url(url: str) -> bool:
	"""Validate URL format"""
	if not url:
		return False
	
	pattern = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&=]*)$'
	return re.match(pattern, url) is not None


def clean_phone_number(phone: str) -> str:
	"""Clean and format phone number"""
	if not phone:
		return ""
	
	# Remove all non-digit characters except +
	cleaned = re.sub(r'[^\d\+]', '', str(phone))
	
	# If it starts with +, keep it
	if cleaned.startswith('+'):
		return cleaned
	
	# If it's a US number without country code, add +1
	if len(cleaned) == 10:
		return f"+1{cleaned}"
	
	return cleaned


def normalize_company_name(company_name: str) -> str:
	"""Normalize company name for better matching"""
	if not company_name:
		return ""
	
	# Remove common suffixes
	suffixes = ['Inc', 'LLC', 'Corp', 'Corporation', 'Ltd', 'Limited', 'Co', 'Company']
	normalized = company_name.strip()
	
	for suffix in suffixes:
		pattern = rf'\b{suffix}\.?$'
		normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE).strip()
	
	return normalized


# Lead Scoring Utilities
def calculate_lead_score(lead_data: Dict[str, Any]) -> int:
	"""Calculate lead score based on data quality and completeness"""
	score = 0
	
	# Basic information completeness (40 points max)
	if lead_data.get("lead_name"):
		score += 10
	if lead_data.get("email_id") and validate_email(lead_data.get("email_id")):
		score += 15
	if lead_data.get("phone") and validate_phone(lead_data.get("phone")):
		score += 10
	if lead_data.get("company_name"):
		score += 5
	
	# Email quality (20 points max)
	if lead_data.get("email_id"):
		email = lead_data.get("email_id")
		if validate_email(email):
			score += 10
			# Bonus for business domains
			if not any(domain in email.lower() for domain in ["gmail", "yahoo", "hotmail", "outlook"]):
				score += 10
	
	# Company information (20 points max)
	if lead_data.get("company_name"):
		score += 10
		if lead_data.get("website") and validate_url(lead_data.get("website")):
			score += 10
	
	# Additional data (20 points max)
	if lead_data.get("industry"):
		score += 5
	if lead_data.get("city"):
		score += 5
	if lead_data.get("state"):
		score += 5
	if lead_data.get("country"):
		score += 5
	
	return min(score, 100)  # Cap at 100


def determine_lead_quality(score: int) -> str:
	"""Determine lead quality based on score"""
	if score >= 80:
		return "Hot"
	elif score >= 60:
		return "Warm"
	elif score >= 40:
		return "Cold"
	else:
		return "Unqualified"


# Data Enrichment Utilities
def enrich_lead_data(lead_doc) -> Dict[str, Any]:
	"""Enrich lead data using external services"""
	enrichment_data = {}
	
	try:
		# Get enrichment settings
		settings = frappe.get_single("Lead Intelligence Settings")
		
		# Enrich with Clearbit (if enabled)
		if settings.clearbit_enabled and settings.get_password("clearbit_api_key"):
			clearbit_data = enrich_with_clearbit(lead_doc.email_id, settings.get_password("clearbit_api_key"))
			if clearbit_data:
				enrichment_data["clearbit"] = clearbit_data
		
		# Enrich with Hunter.io (if enabled)
		if settings.hunter_enabled and settings.get_password("hunter_api_key"):
			hunter_data = enrich_with_hunter(lead_doc.email_id, settings.get_password("hunter_api_key"))
			if hunter_data:
				enrichment_data["hunter"] = hunter_data
		
		return enrichment_data
		
	except Exception as e:
		frappe.log_error(f"Error enriching lead data: {str(e)}", "Lead Intelligence Utils")
		return {}


def enrich_with_clearbit(email: str, api_key: str) -> Optional[Dict[str, Any]]:
	"""Enrich lead data using Clearbit API"""
	try:
		url = f"https://person.clearbit.com/v2/people/find?email={email}"
		headers = {"Authorization": f"Bearer {api_key}"}
		
		response = requests.get(url, headers=headers, timeout=10)
		if response.status_code == 200:
			return response.json()
		
	except Exception as e:
		frappe.log_error(f"Clearbit enrichment error: {str(e)}", "Lead Intelligence Utils")
	
	return None


def enrich_with_hunter(email: str, api_key: str) -> Optional[Dict[str, Any]]:
	"""Enrich lead data using Hunter.io API"""
	try:
		url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
		
		response = requests.get(url, timeout=10)
		if response.status_code == 200:
			return response.json()
		
	except Exception as e:
		frappe.log_error(f"Hunter enrichment error: {str(e)}", "Lead Intelligence Utils")
	
	return None


# Email Utilities
def send_notification_email(recipients: List[str], subject: str, message: str, template: str = None):
	"""Send notification email"""
	try:
		if template:
			# Use email template
		from frappe.email.queue import send
			send(
				recipients=recipients,
				subject=subject,
				message=message,
				reference_doctype="Lead Intelligence Settings",
				reference_name="Lead Intelligence Settings"
			)
		else:
			# Send simple email
			from frappe.email.queue import send
			send(
				recipients=recipients,
				subject=subject,
				message=message
			)
		
	except Exception as e:
		frappe.log_error(f"Error sending notification email: {str(e)}", "Lead Intelligence Utils")


def get_email_template_content(template_name: str, context: Dict[str, Any] = None) -> Dict[str, str]:
	"""Get email template content with context"""
	try:
		template = frappe.get_doc("Email Template", template_name)
		
		if context:
			# Replace template variables
			subject = template.subject
			content = template.response
			
			for key, value in context.items():
				subject = subject.replace(f"{{ {key} }}", str(value))
				content = content.replace(f"{{ {key} }}", str(value))
			
			return {"subject": subject, "content": content}
		else:
			return {"subject": template.subject, "content": template.response}
		
	except Exception as e:
		frappe.log_error(f"Error getting email template: {str(e)}", "Lead Intelligence Utils")
		return {"subject": "", "content": ""}


# Security Utilities
def generate_api_key() -> str:
	"""Generate a secure API key"""
	import secrets
	return secrets.token_urlsafe(32)


def hash_sensitive_data(data: str) -> str:
	"""Hash sensitive data for storage"""
	return hashlib.sha256(data.encode()).hexdigest()


def encrypt_data(data: str, key: str) -> str:
	"""Encrypt sensitive data"""
	try:
		from cryptography.fernet import Fernet
		f = Fernet(key.encode())
		return f.encrypt(data.encode()).decode()
	except Exception:
		# Fallback to base64 encoding
		return base64.b64encode(data.encode()).decode()


def decrypt_data(encrypted_data: str, key: str) -> str:
	"""Decrypt sensitive data"""
	try:
		from cryptography.fernet import Fernet
		f = Fernet(key.encode())
		return f.decrypt(encrypted_data.encode()).decode()
	except Exception:
		# Fallback to base64 decoding
		return base64.b64decode(encrypted_data.encode()).decode()


# Date and Time Utilities
def get_local_datetime(utc_datetime: datetime) -> datetime:
	"""Convert UTC datetime to local timezone"""
	try:
		from frappe.utils import get_system_timezone
		import pytz
		
		system_tz = pytz.timezone(get_system_timezone())
		utc_tz = pytz.UTC
		
		if utc_datetime.tzinfo is None:
			utc_datetime = utc_tz.localize(utc_datetime)
		
		return utc_datetime.astimezone(system_tz)
	except Exception:
		return utc_datetime


def format_duration(seconds: int) -> str:
	"""Format duration in human-readable format"""
	if seconds < 60:
		return f"{seconds} seconds"
	elif seconds < 3600:
		minutes = seconds // 60
		return f"{minutes} minutes"
	else:
		hours = seconds // 3600
		minutes = (seconds % 3600) // 60
		if minutes > 0:
			return f"{hours} hours {minutes} minutes"
		else:
			return f"{hours} hours"


# Data Export Utilities
def export_to_csv(data: List[Dict[str, Any]], filename: str) -> str:
	"""Export data to CSV format"""
	try:
		import csv
		import io
		
		if not data:
			return ""
		
		output = io.StringIO()
		writer = csv.DictWriter(output, fieldnames=data[0].keys())
		writer.writeheader()
		writer.writerows(data)
		
		return output.getvalue()
		
	except Exception as e:
		frappe.log_error(f"Error exporting to CSV: {str(e)}", "Lead Intelligence Utils")
		return ""


def export_to_excel(data: List[Dict[str, Any]], filename: str) -> bytes:
	"""Export data to Excel format"""
	try:
		import pandas as pd
		import io
		
		if not data:
			return b""
		
		df = pd.DataFrame(data)
		output = io.BytesIO()
		df.to_excel(output, index=False, engine='openpyxl')
		output.seek(0)
		
		return output.getvalue()
		
	except Exception as e:
		frappe.log_error(f"Error exporting to Excel: {str(e)}", "Lead Intelligence Utils")
		return b""


# Cache Utilities
def get_cached_data(cache_key: str, default=None):
	"""Get data from cache"""
	try:
		return frappe.cache().get_value(cache_key, default)
	except Exception:
		return default


def set_cached_data(cache_key: str, data, expires_in_sec: int = 3600):
	"""Set data in cache"""
	try:
		frappe.cache().set_value(cache_key, data, expires_in_sec)
	except Exception as e:
		frappe.log_error(f"Error setting cache: {str(e)}", "Lead Intelligence Utils")


def clear_cached_data(cache_key: str):
	"""Clear data from cache"""
	try:
		frappe.cache().delete_value(cache_key)
	except Exception as e:
		frappe.log_error(f"Error clearing cache: {str(e)}", "Lead Intelligence Utils")


# Logging Utilities
def log_activity(activity_type: str, details: Dict[str, Any], user: str = None):
	"""Log activity for audit trail"""
	try:
		if not user:
			user = frappe.session.user
		
		activity_log = frappe.get_doc({
			"doctype": "Activity Log",
			"subject": f"Lead Intelligence: {activity_type}",
			"content": json.dumps(details, indent=2),
			"user": user,
			"ip_address": frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None
		})
		activity_log.insert(ignore_permissions=True)
		
	except Exception as e:
		frappe.log_error(f"Error logging activity: {str(e)}", "Lead Intelligence Utils")


def get_system_health() -> Dict[str, Any]:
	"""Get system health status"""
	try:
		# Check database connectivity
		db_status = "healthy"
		try:
			frappe.db.sql("SELECT 1")
		except Exception:
			db_status = "unhealthy"
		
		# Check cache connectivity
		cache_status = "healthy"
		try:
			frappe.cache().ping()
		except Exception:
			cache_status = "unhealthy"
		
		# Check API services
		api_status = {}
		services = ["google_places", "openai", "sendgrid"]
		for service in services:
			settings = get_api_settings(service)
			api_status[service] = "enabled" if settings.get("enabled") else "disabled"
		
		return {
			"database": db_status,
			"cache": cache_status,
			"api_services": api_status,
			"timestamp": now()
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting system health: {str(e)}", "Lead Intelligence Utils")
		return {"status": "error", "timestamp": now()}


# Jinja Methods (for templates)
def jinja_methods():
	"""Custom Jinja methods for Lead Intelligence"""
	return {
		"get_lead_score": calculate_lead_score,
		"determine_lead_quality": determine_lead_quality,
		"validate_email": validate_email,
		"validate_phone": validate_phone,
		"format_duration": format_duration
	}


def jinja_filters():
	"""Custom Jinja filters for Lead Intelligence"""
	return {
		"clean_phone": clean_phone_number,
		"normalize_company": normalize_company_name,
		"lead_quality": determine_lead_quality
	}