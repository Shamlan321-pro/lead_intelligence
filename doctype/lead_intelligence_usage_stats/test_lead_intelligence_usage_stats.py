# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import frappe
import unittest
from frappe.utils import nowdate, add_days
from lead_intelligence.doctype.lead_intelligence_usage_stats.lead_intelligence_usage_stats import (
	get_or_create_daily_stats,
	track_api_usage,
	track_usage_metric,
	get_usage_summary,
	get_daily_usage_trend,
	get_service_usage_breakdown,
	get_top_users_by_usage,
	get_cost_analysis
)

class TestLeadIntelligenceUsageStats(unittest.TestCase):
	"""Test cases for Lead Intelligence Usage Stats DocType."""
	
	def setUp(self):
		"""Set up test data."""
		self.test_user = "test@example.com"
		self.test_date = nowdate()
		
		# Create test user if not exists
		if not frappe.db.exists("User", self.test_user):
			test_user_doc = frappe.get_doc({
				"doctype": "User",
				"email": self.test_user,
				"first_name": "Test",
				"last_name": "User",
				"enabled": 1
			})
			test_user_doc.insert(ignore_permissions=True)
	
	def tearDown(self):
		"""Clean up test data."""
		frappe.db.rollback()
	
	def test_usage_stats_creation(self):
		"""Test creating usage statistics."""
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user,
			"google_places_calls": 10,
			"google_places_cost": 5.0,
			"openai_calls": 5,
			"openai_cost": 2.5,
			"leads_generated": 20,
			"emails_sent": 15
		})
		stats.insert()
		
		self.assertEqual(stats.total_cost, 7.5)
		self.assertTrue(frappe.db.exists("Lead Intelligence Usage Stats", stats.name))
	
	def test_total_cost_calculation(self):
		"""Test total cost calculation."""
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user,
			"google_places_cost": 10.0,
			"openai_cost": 5.0,
			"email_service_cost": 2.0,
			"crm_integration_cost": 3.0,
			"data_enrichment_cost": 1.5
		})
		stats.insert()
		
		self.assertEqual(stats.total_cost, 21.5)
	
	def test_add_api_usage(self):
		"""Test adding API usage."""
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user
		})
		stats.insert()
		
		# Add Google Places usage
		stats.add_api_usage("google_places", 5, 2.5)
		self.assertEqual(stats.google_places_calls, 5)
		self.assertEqual(stats.google_places_cost, 2.5)
		self.assertEqual(stats.total_requests, 5)
		
		# Add OpenAI usage
		stats.add_api_usage("openai", 3, 1.5)
		self.assertEqual(stats.openai_calls, 3)
		self.assertEqual(stats.openai_cost, 1.5)
		self.assertEqual(stats.total_requests, 8)
		self.assertEqual(stats.total_cost, 4.0)
	
	def test_add_usage_metric(self):
		"""Test adding usage metrics."""
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user
		})
		stats.insert()
		
		stats.add_usage_metric("leads_generated", 10)
		self.assertEqual(stats.leads_generated, 10)
		
		stats.add_usage_metric("emails_sent", 5)
		self.assertEqual(stats.emails_sent, 5)
		
		stats.add_usage_metric("ai_conversations", 3)
		self.assertEqual(stats.ai_conversations, 3)
	
	def test_update_performance_metrics(self):
		"""Test updating performance metrics."""
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user,
			"total_requests": 10
		})
		stats.insert()
		
		# Update with successful request
		stats.update_performance_metrics(response_time=150.5, success=True, bandwidth=1.2)
		self.assertEqual(stats.avg_response_time, 150.5)
		self.assertEqual(stats.error_count, 0)
		self.assertEqual(stats.success_rate, 100.0)
		self.assertEqual(stats.bandwidth_used, 1.2)
		
		# Update with failed request
		stats.update_performance_metrics(response_time=200.0, success=False)
		self.assertEqual(stats.error_count, 1)
		self.assertEqual(stats.success_rate, 90.0)  # 9 out of 10 successful
	
	def test_metadata_handling(self):
		"""Test metadata handling."""
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user
		})
		stats.insert()
		
		stats.add_metadata("campaign_id", "CAMP-001")
		stats.add_metadata("source", "web_app")
		
		import json
		metadata = json.loads(stats.metadata)
		self.assertEqual(metadata["campaign_id"], "CAMP-001")
		self.assertEqual(metadata["source"], "web_app")
	
	def test_get_or_create_daily_stats(self):
		"""Test getting or creating daily stats."""
		# First call should create new stats
		stats1 = get_or_create_daily_stats(self.test_user, self.test_date)
		self.assertTrue(frappe.db.exists("Lead Intelligence Usage Stats", stats1.name))
		
		# Second call should return existing stats
		stats2 = get_or_create_daily_stats(self.test_user, self.test_date)
		self.assertEqual(stats1.name, stats2.name)
	
	def test_track_api_usage_function(self):
		"""Test track_api_usage utility function."""
		track_api_usage("google_places", 5, 2.5, self.test_user, 150.0, True, 1.0)
		
		stats = get_or_create_daily_stats(self.test_user, self.test_date)
		self.assertEqual(stats.google_places_calls, 5)
		self.assertEqual(stats.google_places_cost, 2.5)
		self.assertEqual(stats.avg_response_time, 150.0)
		self.assertEqual(stats.bandwidth_used, 1.0)
	
	def test_track_usage_metric_function(self):
		"""Test track_usage_metric utility function."""
		track_usage_metric("leads_generated", 10, self.test_user)
		track_usage_metric("emails_sent", 5, self.test_user)
		
		stats = get_or_create_daily_stats(self.test_user, self.test_date)
		self.assertEqual(stats.leads_generated, 10)
		self.assertEqual(stats.emails_sent, 5)
	
	def test_get_usage_summary(self):
		"""Test getting usage summary."""
		# Create test data
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user,
			"google_places_calls": 10,
			"openai_calls": 5,
			"leads_generated": 20,
			"total_cost": 15.0,
			"total_requests": 15
		})
		stats.insert()
		
		summary = get_usage_summary(self.test_user, self.test_date, self.test_date)
		self.assertEqual(summary.get("total_google_places_calls"), 10)
		self.assertEqual(summary.get("total_openai_calls"), 5)
		self.assertEqual(summary.get("total_leads_generated"), 20)
		self.assertEqual(summary.get("total_cost"), 15.0)
	
	def test_get_service_usage_breakdown(self):
		"""Test getting service usage breakdown."""
		# Create test data
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user,
			"google_places_calls": 10,
			"google_places_cost": 5.0,
			"openai_calls": 5,
			"openai_cost": 2.5,
			"email_api_calls": 8,
			"email_service_cost": 1.0
		})
		stats.insert()
		
		breakdown = get_service_usage_breakdown(self.test_user, self.test_date, self.test_date)
		
		self.assertEqual(breakdown["google_places"]["calls"], 10)
		self.assertEqual(breakdown["google_places"]["cost"], 5.0)
		self.assertEqual(breakdown["openai"]["calls"], 5)
		self.assertEqual(breakdown["openai"]["cost"], 2.5)
		self.assertEqual(breakdown["email"]["calls"], 8)
		self.assertEqual(breakdown["email"]["cost"], 1.0)
	
	def test_get_cost_analysis(self):
		"""Test getting cost analysis."""
		# Create test data
		stats = frappe.get_doc({
			"doctype": "Lead Intelligence Usage Stats",
			"date": self.test_date,
			"user": self.test_user,
			"google_places_calls": 10,
			"google_places_cost": 10.0,
			"openai_calls": 5,
			"openai_cost": 5.0
		})
		stats.insert()
		
		analysis = get_cost_analysis(self.test_user, self.test_date, self.test_date)
		
		self.assertEqual(analysis["total_cost"], 15.0)
		self.assertEqual(analysis["total_calls"], 15)
		self.assertEqual(analysis["avg_cost_per_call"], 1.0)
		
		# Check service breakdown
		google_service = analysis["service_breakdown"]["google_places"]
		self.assertEqual(google_service["cost_per_call"], 1.0)
		self.assertEqual(google_service["cost_percentage"], 66.67)  # 10/15 * 100
		
		openai_service = analysis["service_breakdown"]["openai"]
		self.assertEqual(openai_service["cost_per_call"], 1.0)
		self.assertEqual(openai_service["cost_percentage"], 33.33)  # 5/15 * 100
	
	def test_daily_usage_trend(self):
		"""Test getting daily usage trend."""
		# Create test data for multiple days
		for i in range(3):
			test_date = add_days(self.test_date, -i)
			stats = frappe.get_doc({
				"doctype": "Lead Intelligence Usage Stats",
				"date": test_date,
				"user": self.test_user,
				"total_requests": 10 + i,
				"total_cost": 5.0 + i,
				"leads_generated": 5 + i,
				"success_rate": 95.0 + i
			})
			stats.insert()
		
		trend = get_daily_usage_trend(self.test_user, 7)
		self.assertEqual(len(trend), 3)
		
		# Check if data is ordered by date
		self.assertTrue(trend[0]["date"] <= trend[1]["date"] <= trend[2]["date"])
	
	def test_top_users_by_usage(self):
		"""Test getting top users by usage."""
		# Create test data for multiple users
		users = ["user1@example.com", "user2@example.com", "user3@example.com"]
		
		for i, user in enumerate(users):
			# Create user if not exists
			if not frappe.db.exists("User", user):
				test_user_doc = frappe.get_doc({
					"doctype": "User",
					"email": user,
					"first_name": f"User{i+1}",
					"enabled": 1
				})
				test_user_doc.insert(ignore_permissions=True)
			
			stats = frappe.get_doc({
				"doctype": "Lead Intelligence Usage Stats",
				"date": self.test_date,
				"user": user,
				"total_requests": 100 - (i * 10),  # Decreasing usage
				"total_cost": 50.0 - (i * 5),
				"leads_generated": 20 - (i * 2)
			})
			stats.insert()
		
		top_users = get_top_users_by_usage(2, self.test_date, self.test_date)
		self.assertEqual(len(top_users), 2)
		
		# Check if users are ordered by total_requests (descending)
		self.assertEqual(top_users[0]["user"], "user1@example.com")
		self.assertEqual(top_users[1]["user"], "user2@example.com")
		self.assertTrue(top_users[0]["total_requests"] > top_users[1]["total_requests"])

# Test data for make_test_records
test_records = frappe._dict({
	"Lead Intelligence Usage Stats": [
		{
			"doctype": "Lead Intelligence Usage Stats",
			"date": "2024-01-01",
			"user": "Administrator",
			"google_places_calls": 5,
			"google_places_cost": 2.5,
			"openai_calls": 3,
			"openai_cost": 1.5,
			"leads_generated": 10,
			"emails_sent": 5,
			"total_requests": 8,
			"success_rate": 100.0
		}
	]
})