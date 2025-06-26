# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import frappe
import unittest
from frappe.test_runner import make_test_records
from lead_intelligence.doctype.lead_intelligence_settings.lead_intelligence_settings import (
	get_lead_intelligence_settings,
	get_google_places_api_key,
	get_openai_api_key,
	get_email_service_config,
	get_crm_config,
	get_data_enrichment_config
)

class TestLeadIntelligenceSettings(unittest.TestCase):
	"""Test cases for Lead Intelligence Settings DocType."""
	
	def setUp(self):
		"""Set up test data."""
		# Create test settings
		self.test_settings = frappe.get_doc({
			"doctype": "Lead Intelligence Settings",
			"settings_name": "Test Settings",
			"is_active": 1,
			"google_places_enabled": 1,
			"google_places_api_key": "test_google_api_key",
			"openai_enabled": 1,
			"openai_api_key": "test_openai_api_key",
			"openai_model": "gpt-3.5-turbo",
			"email_service": "SMTP",
			"smtp_server": "smtp.gmail.com",
			"smtp_port": 587,
			"smtp_username": "test@example.com",
			"smtp_password": "test_password",
			"smtp_use_tls": 1,
			"crm_integration": "HubSpot",
			"hubspot_api_key": "test_hubspot_key",
			"data_enrichment_service": "Clearbit",
			"clearbit_api_key": "test_clearbit_key",
			"default_search_radius": 10000,
			"max_leads_per_campaign": 1000,
			"email_rate_limit": 100,
			"api_rate_limit": 1000,
			"enable_logging": 1,
			"log_level": "INFO"
		})
	
	def tearDown(self):
		"""Clean up test data."""
		frappe.db.rollback()
	
	def test_settings_creation(self):
		"""Test creating Lead Intelligence Settings."""
		self.test_settings.insert()
		self.assertTrue(frappe.db.exists("Lead Intelligence Settings", "Test Settings"))
	
	def test_validation_google_places(self):
		"""Test Google Places API validation."""
		# Test enabled without API key
		self.test_settings.google_places_enabled = 1
		self.test_settings.google_places_api_key = ""
		
		with self.assertRaises(frappe.ValidationError):
			self.test_settings.insert()
	
	def test_validation_openai(self):
		"""Test OpenAI API validation."""
		# Test enabled without API key
		self.test_settings.openai_enabled = 1
		self.test_settings.openai_api_key = ""
		
		with self.assertRaises(frappe.ValidationError):
			self.test_settings.insert()
	
	def test_validation_email_smtp(self):
		"""Test SMTP email validation."""
		# Test SMTP without server
		self.test_settings.email_service = "SMTP"
		self.test_settings.smtp_server = ""
		
		with self.assertRaises(frappe.ValidationError):
			self.test_settings.insert()
	
	def test_validation_email_sendgrid(self):
		"""Test SendGrid email validation."""
		# Test SendGrid without API key
		self.test_settings.email_service = "SendGrid"
		self.test_settings.sendgrid_api_key = ""
		
		with self.assertRaises(frappe.ValidationError):
			self.test_settings.insert()
	
	def test_validation_crm_salesforce(self):
		"""Test Salesforce CRM validation."""
		# Test Salesforce without complete credentials
		self.test_settings.crm_integration = "Salesforce"
		self.test_settings.salesforce_client_id = "test_id"
		self.test_settings.salesforce_client_secret = ""
		
		with self.assertRaises(frappe.ValidationError):
			self.test_settings.insert()
	
	def test_validation_rate_limits(self):
		"""Test rate limit validation."""
		# Test invalid email rate limit
		self.test_settings.email_rate_limit = 0
		
		with self.assertRaises(frappe.ValidationError):
			self.test_settings.insert()
		
		# Test invalid search radius
		self.test_settings.email_rate_limit = 100
		self.test_settings.default_search_radius = 50
		
		with self.assertRaises(frappe.ValidationError):
			self.test_settings.insert()
	
	def test_integration_status(self):
		"""Test integration status method."""
		self.test_settings.insert()
		status = self.test_settings.get_integration_status()
		
		self.assertIn("google_places", status)
		self.assertIn("openai", status)
		self.assertIn("email_service", status)
		self.assertIn("crm_integration", status)
		self.assertIn("data_enrichment", status)
		
		# Check Google Places status
		self.assertTrue(status["google_places"]["enabled"])
		self.assertTrue(status["google_places"]["configured"])
		self.assertEqual(status["google_places"]["status"], "active")
		
		# Check OpenAI status
		self.assertTrue(status["openai"]["enabled"])
		self.assertTrue(status["openai"]["configured"])
		self.assertEqual(status["openai"]["model"], "gpt-3.5-turbo")
		self.assertEqual(status["openai"]["status"], "active")
	
	def test_utility_functions(self):
		"""Test utility functions."""
		self.test_settings.insert()
		
		# Test get_lead_intelligence_settings
		settings = get_lead_intelligence_settings()
		self.assertEqual(settings.settings_name, "Test Settings")
		
		# Test get_google_places_api_key
		api_key = get_google_places_api_key()
		self.assertEqual(api_key, "test_google_api_key")
		
		# Test get_openai_api_key
		openai_key = get_openai_api_key()
		self.assertEqual(openai_key, "test_openai_api_key")
		
		# Test get_email_service_config
		email_config = get_email_service_config()
		self.assertEqual(email_config["service"], "SMTP")
		self.assertEqual(email_config["server"], "smtp.gmail.com")
		self.assertEqual(email_config["port"], 587)
		
		# Test get_crm_config
		crm_config = get_crm_config()
		self.assertEqual(crm_config["service"], "HubSpot")
		self.assertEqual(crm_config["api_key"], "test_hubspot_key")
		
		# Test get_data_enrichment_config
		enrichment_config = get_data_enrichment_config()
		self.assertEqual(enrichment_config["service"], "Clearbit")
		self.assertEqual(enrichment_config["api_key"], "test_clearbit_key")
	
	def test_email_service_configuration_check(self):
		"""Test email service configuration checks."""
		self.test_settings.insert()
		
		# Test SMTP configuration
		self.assertTrue(self.test_settings._is_email_service_configured())
		
		# Test SendGrid configuration
		self.test_settings.email_service = "SendGrid"
		self.test_settings.sendgrid_api_key = "test_key"
		self.assertTrue(self.test_settings._is_email_service_configured())
		
		# Test Mailgun configuration
		self.test_settings.email_service = "Mailgun"
		self.test_settings.mailgun_api_key = "test_key"
		self.test_settings.mailgun_domain = "test.mailgun.org"
		self.assertTrue(self.test_settings._is_email_service_configured())
	
	def test_crm_configuration_check(self):
		"""Test CRM configuration checks."""
		self.test_settings.insert()
		
		# Test HubSpot configuration
		self.assertTrue(self.test_settings._is_crm_configured())
		
		# Test Salesforce configuration
		self.test_settings.crm_integration = "Salesforce"
		self.test_settings.salesforce_client_id = "test_id"
		self.test_settings.salesforce_client_secret = "test_secret"
		self.test_settings.salesforce_username = "test@example.com"
		self.test_settings.salesforce_password = "test_password"
		self.assertTrue(self.test_settings._is_crm_configured())
		
		# Test Pipedrive configuration
		self.test_settings.crm_integration = "Pipedrive"
		self.test_settings.pipedrive_api_token = "test_token"
		self.test_settings.pipedrive_domain = "test.pipedrive.com"
		self.assertTrue(self.test_settings._is_crm_configured())
	
	def test_data_enrichment_configuration_check(self):
		"""Test data enrichment configuration checks."""
		self.test_settings.insert()
		
		# Test Clearbit configuration
		self.assertTrue(self.test_settings._is_data_enrichment_configured())
		
		# Test ZoomInfo configuration
		self.test_settings.data_enrichment_service = "ZoomInfo"
		self.test_settings.zoominfo_api_key = "test_key"
		self.assertTrue(self.test_settings._is_data_enrichment_configured())
		
		# Test Hunter configuration
		self.test_settings.data_enrichment_service = "Hunter"
		self.test_settings.hunter_api_key = "test_key"
		self.assertTrue(self.test_settings._is_data_enrichment_configured())
		
		# Test Apollo configuration
		self.test_settings.data_enrichment_service = "Apollo"
		self.test_settings.apollo_api_key = "test_key"
		self.assertTrue(self.test_settings._is_data_enrichment_configured())
	
	def test_inactive_settings(self):
		"""Test behavior with inactive settings."""
		self.test_settings.is_active = 0
		self.test_settings.insert()
		
		with self.assertRaises(frappe.ValidationError):
			get_lead_intelligence_settings()
	
	def test_disabled_services(self):
		"""Test behavior with disabled services."""
		self.test_settings.google_places_enabled = 0
		self.test_settings.openai_enabled = 0
		self.test_settings.insert()
		
		with self.assertRaises(frappe.ValidationError):
			get_google_places_api_key()
		
		with self.assertRaises(frappe.ValidationError):
			get_openai_api_key()

# Test data for make_test_records
test_records = frappe._dict({
	"Lead Intelligence Settings": [
		{
			"doctype": "Lead Intelligence Settings",
			"settings_name": "Default Settings",
			"is_active": 1,
			"google_places_enabled": 0,
			"openai_enabled": 0,
			"email_service": "SMTP",
			"crm_integration": "None",
			"data_enrichment_service": "None",
			"default_search_radius": 10000,
			"max_leads_per_campaign": 1000,
			"email_rate_limit": 100,
			"api_rate_limit": 1000,
			"enable_logging": 1,
			"log_level": "INFO"
		}
	]
})