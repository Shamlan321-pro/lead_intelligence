# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt
import json
import requests
from typing import Dict, Any, Optional

class LeadIntelligenceSettings(Document):
	"""Lead Intelligence Settings DocType for managing all configuration settings."""
	
	def validate(self):
		"""Validate settings before saving."""
		self.validate_api_keys()
		self.validate_email_settings()
		self.validate_crm_settings()
		self.validate_rate_limits()
	
	def validate_api_keys(self):
		"""Validate API keys and test connections."""
		# Validate Google Places API
		if self.google_places_enabled and not self.google_places_api_key:
			frappe.throw(_("Google Places API Key is required when Google Places is enabled"))
		
		# Validate OpenAI API
		if self.openai_enabled and not self.openai_api_key:
			frappe.throw(_("OpenAI API Key is required when OpenAI is enabled"))
	
	def validate_email_settings(self):
		"""Validate email service configuration."""
		if self.email_service == "SendGrid" and not self.sendgrid_api_key:
			frappe.throw(_("SendGrid API Key is required for SendGrid email service"))
		
		if self.email_service == "Mailgun":
			if not self.mailgun_api_key:
				frappe.throw(_("Mailgun API Key is required for Mailgun email service"))
			if not self.mailgun_domain:
				frappe.throw(_("Mailgun Domain is required for Mailgun email service"))
		
		if self.email_service == "SMTP":
			if not self.smtp_server:
				frappe.throw(_("SMTP Server is required for SMTP email service"))
			if not self.smtp_username:
				frappe.throw(_("SMTP Username is required for SMTP email service"))
			if not self.smtp_password:
				frappe.throw(_("SMTP Password is required for SMTP email service"))
	
	def validate_crm_settings(self):
		"""Validate CRM integration settings."""
		if self.crm_integration == "Salesforce":
			if not all([self.salesforce_client_id, self.salesforce_client_secret, 
					   self.salesforce_username, self.salesforce_password]):
				frappe.throw(_("All Salesforce credentials are required for Salesforce integration"))
		
		if self.crm_integration == "HubSpot" and not self.hubspot_api_key:
			frappe.throw(_("HubSpot API Key is required for HubSpot integration"))
		
		if self.crm_integration == "Pipedrive":
			if not self.pipedrive_api_token:
				frappe.throw(_("Pipedrive API Token is required for Pipedrive integration"))
			if not self.pipedrive_domain:
				frappe.throw(_("Pipedrive Domain is required for Pipedrive integration"))
	
	def validate_rate_limits(self):
		"""Validate rate limit settings."""
		if self.email_rate_limit < 1 or self.email_rate_limit > 10000:
			frappe.throw(_("Email rate limit must be between 1 and 10000 per hour"))
		
		if self.api_rate_limit < 1 or self.api_rate_limit > 100000:
			frappe.throw(_("API rate limit must be between 1 and 100000 per hour"))
		
		if self.default_search_radius < 100 or self.default_search_radius > 50000:
			frappe.throw(_("Default search radius must be between 100 and 50000 meters"))
		
		if self.max_leads_per_campaign < 1 or self.max_leads_per_campaign > 10000:
			frappe.throw(_("Max leads per campaign must be between 1 and 10000"))
	
	def test_google_places_connection(self):
		"""Test Google Places API connection."""
		if not self.google_places_api_key:
			return {"success": False, "message": "API key not configured"}
		
		try:
			url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
			params = {
				"input": "test",
				"inputtype": "textquery",
				"key": self.google_places_api_key
			}
			response = requests.get(url, params=params, timeout=10)
			data = response.json()
			
			if response.status_code == 200 and data.get("status") != "REQUEST_DENIED":
				return {"success": True, "message": "Connection successful"}
			else:
				return {"success": False, "message": data.get("error_message", "Invalid API key")}
				
		except Exception as e:
			return {"success": False, "message": str(e)}
	
	def test_openai_connection(self):
		"""Test OpenAI API connection."""
		if not self.openai_api_key:
			return {"success": False, "message": "API key not configured"}
		
		try:
			headers = {
				"Authorization": f"Bearer {self.openai_api_key}",
				"Content-Type": "application/json"
			}
			url = "https://api.openai.com/v1/models"
			response = requests.get(url, headers=headers, timeout=10)
			
			if response.status_code == 200:
				return {"success": True, "message": "Connection successful"}
			else:
				return {"success": False, "message": "Invalid API key"}
				
		except Exception as e:
			return {"success": False, "message": str(e)}
	
	def test_email_service_connection(self):
		"""Test email service connection."""
		if self.email_service == "SendGrid":
			return self._test_sendgrid_connection()
		elif self.email_service == "Mailgun":
			return self._test_mailgun_connection()
		elif self.email_service == "SMTP":
			return self._test_smtp_connection()
		else:
			return {"success": False, "message": "Email service not configured"}
	
	def _test_sendgrid_connection(self):
		"""Test SendGrid API connection."""
		if not self.sendgrid_api_key:
			return {"success": False, "message": "SendGrid API key not configured"}
		
		try:
			headers = {
				"Authorization": f"Bearer {self.sendgrid_api_key}",
				"Content-Type": "application/json"
			}
			url = "https://api.sendgrid.com/v3/user/account"
			response = requests.get(url, headers=headers, timeout=10)
			
			if response.status_code == 200:
				return {"success": True, "message": "SendGrid connection successful"}
			else:
				return {"success": False, "message": "Invalid SendGrid API key"}
				
		except Exception as e:
			return {"success": False, "message": str(e)}
	
	def _test_mailgun_connection(self):
		"""Test Mailgun API connection."""
		if not self.mailgun_api_key or not self.mailgun_domain:
			return {"success": False, "message": "Mailgun credentials not configured"}
		
		try:
			url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/stats/total"
			response = requests.get(url, auth=("api", self.mailgun_api_key), timeout=10)
			
			if response.status_code == 200:
				return {"success": True, "message": "Mailgun connection successful"}
			else:
				return {"success": False, "message": "Invalid Mailgun credentials"}
				
		except Exception as e:
			return {"success": False, "message": str(e)}
	
	def _test_smtp_connection(self):
		"""Test SMTP connection."""
		if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
			return {"success": False, "message": "SMTP credentials not configured"}
		
		try:
			import smtplib
			from email.mime.text import MIMEText
			
			server = smtplib.SMTP(self.smtp_server, self.smtp_port)
			if self.smtp_use_tls:
				server.starttls()
			server.login(self.smtp_username, self.smtp_password)
			server.quit()
			
			return {"success": True, "message": "SMTP connection successful"}
			
		except Exception as e:
			return {"success": False, "message": str(e)}
	
	def get_integration_status(self):
		"""Get status of all integrations."""
		status = {
			"google_places": {
				"enabled": self.google_places_enabled,
				"configured": bool(self.google_places_api_key),
				"status": "active" if self.google_places_enabled and self.google_places_api_key else "inactive"
			},
			"openai": {
				"enabled": self.openai_enabled,
				"configured": bool(self.openai_api_key),
				"model": self.openai_model,
				"status": "active" if self.openai_enabled and self.openai_api_key else "inactive"
			},
			"email_service": {
				"service": self.email_service,
				"configured": self._is_email_service_configured(),
				"status": "active" if self._is_email_service_configured() else "inactive"
			},
			"crm_integration": {
				"service": self.crm_integration,
				"configured": self._is_crm_configured(),
				"status": "active" if self.crm_integration != "None" and self._is_crm_configured() else "inactive"
			},
			"data_enrichment": {
				"service": self.data_enrichment_service,
				"configured": self._is_data_enrichment_configured(),
				"status": "active" if self.data_enrichment_service != "None" and self._is_data_enrichment_configured() else "inactive"
			}
		}
		return status
	
	def _is_email_service_configured(self):
		"""Check if email service is properly configured."""
		if self.email_service == "SendGrid":
			return bool(self.sendgrid_api_key)
		elif self.email_service == "Mailgun":
			return bool(self.mailgun_api_key and self.mailgun_domain)
		elif self.email_service == "SMTP":
			return bool(self.smtp_server and self.smtp_username and self.smtp_password)
		return False
	
	def _is_crm_configured(self):
		"""Check if CRM integration is properly configured."""
		if self.crm_integration == "Salesforce":
			return bool(self.salesforce_client_id and self.salesforce_client_secret and 
					   self.salesforce_username and self.salesforce_password)
		elif self.crm_integration == "HubSpot":
			return bool(self.hubspot_api_key)
		elif self.crm_integration == "Pipedrive":
			return bool(self.pipedrive_api_token and self.pipedrive_domain)
		return False
	
	def _is_data_enrichment_configured(self):
		"""Check if data enrichment service is properly configured."""
		if self.data_enrichment_service == "Clearbit":
			return bool(self.clearbit_api_key)
		elif self.data_enrichment_service == "ZoomInfo":
			return bool(self.zoominfo_api_key)
		elif self.data_enrichment_service == "Hunter":
			return bool(self.hunter_api_key)
		elif self.data_enrichment_service == "Apollo":
			return bool(self.apollo_api_key)
		return False

# Utility functions for getting settings
def get_lead_intelligence_settings():
	"""Get the active Lead Intelligence Settings."""
	settings = frappe.get_single("Lead Intelligence Settings")
	if not settings.is_active:
		frappe.throw(_("Lead Intelligence Settings is not active"))
	return settings

def get_google_places_api_key():
	"""Get Google Places API key from settings."""
	settings = get_lead_intelligence_settings()
	if not settings.google_places_enabled or not settings.google_places_api_key:
		frappe.throw(_("Google Places API is not configured or enabled"))
	return settings.google_places_api_key

def get_openai_api_key():
	"""Get OpenAI API key from settings."""
	settings = get_lead_intelligence_settings()
	if not settings.openai_enabled or not settings.openai_api_key:
		frappe.throw(_("OpenAI API is not configured or enabled"))
	return settings.openai_api_key

def get_openai_model():
	"""Get OpenAI model from settings."""
	settings = get_lead_intelligence_settings()
	return settings.openai_model or "gpt-3.5-turbo"

def get_email_service_config():
	"""Get email service configuration."""
	settings = get_lead_intelligence_settings()
	config = {
		"service": settings.email_service,
		"rate_limit": settings.email_rate_limit
	}
	
	if settings.email_service == "SendGrid":
		config["api_key"] = settings.sendgrid_api_key
	elif settings.email_service == "Mailgun":
		config["api_key"] = settings.mailgun_api_key
		config["domain"] = settings.mailgun_domain
	elif settings.email_service == "SMTP":
		config.update({
			"server": settings.smtp_server,
			"port": settings.smtp_port,
			"username": settings.smtp_username,
			"password": settings.smtp_password,
			"use_tls": settings.smtp_use_tls
		})
	
	return config

def get_crm_config():
	"""Get CRM integration configuration."""
	settings = get_lead_intelligence_settings()
	config = {"service": settings.crm_integration}
	
	if settings.crm_integration == "Salesforce":
		config.update({
			"client_id": settings.salesforce_client_id,
			"client_secret": settings.salesforce_client_secret,
			"username": settings.salesforce_username,
			"password": settings.salesforce_password
		})
	elif settings.crm_integration == "HubSpot":
		config["api_key"] = settings.hubspot_api_key
	elif settings.crm_integration == "Pipedrive":
		config.update({
			"api_token": settings.pipedrive_api_token,
			"domain": settings.pipedrive_domain
		})
	
	return config

def get_data_enrichment_config():
	"""Get data enrichment service configuration."""
	settings = get_lead_intelligence_settings()
	config = {"service": settings.data_enrichment_service}
	
	if settings.data_enrichment_service == "Clearbit":
		config["api_key"] = settings.clearbit_api_key
	elif settings.data_enrichment_service == "ZoomInfo":
		config["api_key"] = settings.zoominfo_api_key
	elif settings.data_enrichment_service == "Hunter":
		config["api_key"] = settings.hunter_api_key
	elif settings.data_enrichment_service == "Apollo":
		config["api_key"] = settings.apollo_api_key
	
	return config

def get_default_settings():
	"""Get default application settings."""
	settings = get_lead_intelligence_settings()
	return {
		"default_search_radius": settings.default_search_radius,
		"max_leads_per_campaign": settings.max_leads_per_campaign,
		"email_rate_limit": settings.email_rate_limit,
		"api_rate_limit": settings.api_rate_limit,
		"enable_logging": settings.enable_logging,
		"log_level": settings.log_level
	}

def get_webhook_config():
	"""Get webhook configuration."""
	settings = get_lead_intelligence_settings()
	return {
		"secret": settings.webhook_secret,
		"url": settings.webhook_url
	}