# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, now, flt, cint, get_datetime
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional, List

class LeadIntelligenceUsageStats(Document):
	"""Lead Intelligence Usage Statistics DocType for tracking API usage and system metrics."""
	
	def before_save(self):
		"""Calculate total cost before saving."""
		self.calculate_total_cost()
	
	def calculate_total_cost(self):
		"""Calculate total cost from all service costs."""
		self.total_cost = (
			flt(self.google_places_cost) +
			flt(self.openai_cost) +
			flt(self.email_service_cost) +
			flt(self.crm_integration_cost) +
			flt(self.data_enrichment_cost)
		)
	
	def add_api_usage(self, service: str, calls: int = 1, cost: float = 0.0):
		"""Add API usage for a specific service."""
		if service == "google_places":
			self.google_places_calls = cint(self.google_places_calls) + calls
			self.google_places_cost = flt(self.google_places_cost) + cost
		elif service == "openai":
			self.openai_calls = cint(self.openai_calls) + calls
			self.openai_cost = flt(self.openai_cost) + cost
		elif service == "email":
			self.email_api_calls = cint(self.email_api_calls) + calls
			self.email_service_cost = flt(self.email_service_cost) + cost
		elif service == "crm":
			self.crm_api_calls = cint(self.crm_api_calls) + calls
			self.crm_integration_cost = flt(self.crm_integration_cost) + cost
		elif service == "data_enrichment":
			self.data_enrichment_calls = cint(self.data_enrichment_calls) + calls
			self.data_enrichment_cost = flt(self.data_enrichment_cost) + cost
		elif service == "webhook":
			self.webhook_calls = cint(self.webhook_calls) + calls
		
		self.total_requests = cint(self.total_requests) + calls
		self.calculate_total_cost()
	
	def add_usage_metric(self, metric: str, count: int = 1):
		"""Add usage metric."""
		if metric == "leads_generated":
			self.leads_generated = cint(self.leads_generated) + count
		elif metric == "emails_sent":
			self.emails_sent = cint(self.emails_sent) + count
		elif metric == "campaigns_created":
			self.campaigns_created = cint(self.campaigns_created) + count
		elif metric == "ai_conversations":
			self.ai_conversations = cint(self.ai_conversations) + count
		elif metric == "lead_analyses":
			self.lead_analyses = cint(self.lead_analyses) + count
		elif metric == "email_generations":
			self.email_generations = cint(self.email_generations) + count
	
	def update_performance_metrics(self, response_time: float = None, success: bool = True, bandwidth: float = 0.0):
		"""Update performance metrics."""
		if response_time is not None:
			# Calculate running average of response time
			current_avg = flt(self.avg_response_time)
			total_requests = cint(self.total_requests)
			
			if total_requests > 0:
				self.avg_response_time = ((current_avg * (total_requests - 1)) + response_time) / total_requests
			else:
				self.avg_response_time = response_time
		
		if not success:
			self.error_count = cint(self.error_count) + 1
		
		# Calculate success rate
		total_requests = cint(self.total_requests)
		if total_requests > 0:
			self.success_rate = ((total_requests - cint(self.error_count)) / total_requests) * 100
		
		if bandwidth > 0:
			self.bandwidth_used = flt(self.bandwidth_used) + bandwidth
	
	def set_peak_usage_hour(self, hour: str):
		"""Set peak usage hour."""
		self.peak_usage_hour = hour
	
	def add_metadata(self, key: str, value: Any):
		"""Add metadata information."""
		if not self.metadata:
			self.metadata = {}
		elif isinstance(self.metadata, str):
			self.metadata = json.loads(self.metadata)
		
		self.metadata[key] = value
		self.metadata = json.dumps(self.metadata)

# Utility functions for usage tracking
def get_or_create_daily_stats(user: str = None, date: str = None) -> 'LeadIntelligenceUsageStats':
	"""Get or create daily usage statistics for a user."""
	if not user:
		user = frappe.session.user
	if not date:
		date = nowdate()
	
	# Try to find existing stats for the date and user
	existing_stats = frappe.db.get_value(
		"Lead Intelligence Usage Stats",
		{"user": user, "date": date},
		"name"
	)
	
	if existing_stats:
		return frappe.get_doc("Lead Intelligence Usage Stats", existing_stats)
	else:
		# Create new stats document
		stats = frappe.new_doc("Lead Intelligence Usage Stats")
		stats.user = user
		stats.date = date
		stats.session_id = frappe.session.sid
		stats.insert(ignore_permissions=True)
		return stats

def track_api_usage(service: str, calls: int = 1, cost: float = 0.0, user: str = None, response_time: float = None, success: bool = True, bandwidth: float = 0.0):
	"""Track API usage for a service."""
	try:
		stats = get_or_create_daily_stats(user)
		stats.add_api_usage(service, calls, cost)
		stats.update_performance_metrics(response_time, success, bandwidth)
		stats.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Error tracking API usage: {str(e)}", "Lead Intelligence Usage Tracking")

def track_usage_metric(metric: str, count: int = 1, user: str = None):
	"""Track usage metrics."""
	try:
		stats = get_or_create_daily_stats(user)
		stats.add_usage_metric(metric, count)
		stats.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Error tracking usage metric: {str(e)}", "Lead Intelligence Usage Tracking")

def get_usage_summary(user: str = None, from_date: str = None, to_date: str = None) -> Dict[str, Any]:
	"""Get usage summary for a user or date range."""
	filters = {}
	
	if user:
		filters["user"] = user
	if from_date:
		filters["date"] = [">=", from_date]
	if to_date:
		if "date" in filters:
			filters["date"] = ["between", [from_date, to_date]]
		else:
			filters["date"] = ["<=", to_date]
	
	stats = frappe.get_all(
		"Lead Intelligence Usage Stats",
		filters=filters,
		fields=[
			"sum(google_places_calls) as total_google_places_calls",
			"sum(openai_calls) as total_openai_calls",
			"sum(email_api_calls) as total_email_calls",
			"sum(crm_api_calls) as total_crm_calls",
			"sum(data_enrichment_calls) as total_enrichment_calls",
			"sum(webhook_calls) as total_webhook_calls",
			"sum(leads_generated) as total_leads_generated",
			"sum(emails_sent) as total_emails_sent",
			"sum(campaigns_created) as total_campaigns_created",
			"sum(ai_conversations) as total_ai_conversations",
			"sum(lead_analyses) as total_lead_analyses",
			"sum(email_generations) as total_email_generations",
			"sum(total_cost) as total_cost",
			"avg(avg_response_time) as avg_response_time",
			"avg(success_rate) as avg_success_rate",
			"sum(error_count) as total_errors",
			"sum(total_requests) as total_requests",
			"sum(bandwidth_used) as total_bandwidth"
		]
	)
	
	return stats[0] if stats else {}

def get_daily_usage_trend(user: str = None, days: int = 30) -> List[Dict[str, Any]]:
	"""Get daily usage trend for the last N days."""
	from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
	to_date = nowdate()
	
	filters = {"date": ["between", [from_date, to_date]]}
	if user:
		filters["user"] = user
	
	stats = frappe.get_all(
		"Lead Intelligence Usage Stats",
		filters=filters,
		fields=[
			"date",
			"sum(total_requests) as requests",
			"sum(total_cost) as cost",
			"sum(leads_generated) as leads",
			"sum(emails_sent) as emails",
			"avg(success_rate) as success_rate"
		],
		group_by="date",
		order_by="date"
	)
	
	return stats

def get_service_usage_breakdown(user: str = None, from_date: str = None, to_date: str = None) -> Dict[str, Any]:
	"""Get service-wise usage breakdown."""
	filters = {}
	
	if user:
		filters["user"] = user
	if from_date:
		filters["date"] = [">=", from_date]
	if to_date:
		if "date" in filters:
			filters["date"] = ["between", [from_date, to_date]]
		else:
			filters["date"] = ["<=", to_date]
	
	stats = frappe.get_all(
		"Lead Intelligence Usage Stats",
		filters=filters,
		fields=[
			"sum(google_places_calls) as google_places_calls",
			"sum(google_places_cost) as google_places_cost",
			"sum(openai_calls) as openai_calls",
			"sum(openai_cost) as openai_cost",
			"sum(email_api_calls) as email_calls",
			"sum(email_service_cost) as email_cost",
			"sum(crm_api_calls) as crm_calls",
			"sum(crm_integration_cost) as crm_cost",
			"sum(data_enrichment_calls) as enrichment_calls",
			"sum(data_enrichment_cost) as enrichment_cost",
			"sum(webhook_calls) as webhook_calls"
		]
	)
	
	result = stats[0] if stats else {}
	
	# Format the breakdown
	breakdown = {
		"google_places": {
			"calls": result.get("google_places_calls", 0),
			"cost": result.get("google_places_cost", 0)
		},
		"openai": {
			"calls": result.get("openai_calls", 0),
			"cost": result.get("openai_cost", 0)
		},
		"email": {
			"calls": result.get("email_calls", 0),
			"cost": result.get("email_cost", 0)
		},
		"crm": {
			"calls": result.get("crm_calls", 0),
			"cost": result.get("crm_cost", 0)
		},
		"data_enrichment": {
			"calls": result.get("enrichment_calls", 0),
			"cost": result.get("enrichment_cost", 0)
		},
		"webhook": {
			"calls": result.get("webhook_calls", 0),
			"cost": 0
		}
	}
	
	return breakdown

def get_top_users_by_usage(limit: int = 10, from_date: str = None, to_date: str = None) -> List[Dict[str, Any]]:
	"""Get top users by usage."""
	filters = {}
	
	if from_date:
		filters["date"] = [">=", from_date]
	if to_date:
		if "date" in filters:
			filters["date"] = ["between", [from_date, to_date]]
		else:
			filters["date"] = ["<=", to_date]
	
	stats = frappe.get_all(
		"Lead Intelligence Usage Stats",
		filters=filters,
		fields=[
			"user",
			"sum(total_requests) as total_requests",
			"sum(total_cost) as total_cost",
			"sum(leads_generated) as leads_generated",
			"sum(emails_sent) as emails_sent"
		],
		group_by="user",
		order_by="total_requests desc",
		limit=limit
	)
	
	return stats

def cleanup_old_stats(days: int = 90):
	"""Clean up old usage statistics."""
	cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
	
	old_stats = frappe.get_all(
		"Lead Intelligence Usage Stats",
		filters={"date": ["<", cutoff_date]},
		fields=["name"]
	)
	
	for stat in old_stats:
		frappe.delete_doc("Lead Intelligence Usage Stats", stat.name, ignore_permissions=True)
	
	frappe.db.commit()
	frappe.log_error(f"Cleaned up {len(old_stats)} old usage statistics", "Lead Intelligence Cleanup")

def get_cost_analysis(user: str = None, from_date: str = None, to_date: str = None) -> Dict[str, Any]:
	"""Get detailed cost analysis."""
	breakdown = get_service_usage_breakdown(user, from_date, to_date)
	
	total_cost = sum(service["cost"] for service in breakdown.values())
	total_calls = sum(service["calls"] for service in breakdown.values())
	
	# Calculate cost per call for each service
	for service_name, service_data in breakdown.items():
		if service_data["calls"] > 0:
			service_data["cost_per_call"] = service_data["cost"] / service_data["calls"]
		else:
			service_data["cost_per_call"] = 0
		
		if total_cost > 0:
			service_data["cost_percentage"] = (service_data["cost"] / total_cost) * 100
		else:
			service_data["cost_percentage"] = 0
	
	return {
		"total_cost": total_cost,
		"total_calls": total_calls,
		"avg_cost_per_call": total_cost / total_calls if total_calls > 0 else 0,
		"service_breakdown": breakdown
	}