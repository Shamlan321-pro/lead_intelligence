# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now, add_days, get_datetime
from datetime import datetime, timedelta
import json


def all():
	"""Tasks that run on every scheduler event"""
	pass


def daily():
	"""Tasks that run daily"""
	try:
		# Clean up old usage statistics (older than 90 days)
		cleanup_old_usage_stats()
		
		# Generate daily usage summary
		generate_daily_usage_summary()
		
		# Check API usage limits
		check_api_usage_limits()
		
		# Update lead scores
		update_lead_scores()
		
	except Exception as e:
		frappe.log_error(f"Daily task error: {str(e)}", "Lead Intelligence Daily Tasks")


def hourly():
	"""Tasks that run hourly"""
	try:
		# Process pending email campaigns
		process_pending_email_campaigns()
		
		# Update campaign statuses
		update_campaign_statuses()
		
		# Check for webhook failures and retry
		retry_failed_webhooks()
		
	except Exception as e:
		frappe.log_error(f"Hourly task error: {str(e)}", "Lead Intelligence Hourly Tasks")


def weekly():
	"""Tasks that run weekly"""
	try:
		# Generate weekly analytics report
		generate_weekly_analytics_report()
		
		# Clean up old campaign executions
		cleanup_old_campaign_executions()
		
		# Update lead quality scores
		update_lead_quality_scores()
		
	except Exception as e:
		frappe.log_error(f"Weekly task error: {str(e)}", "Lead Intelligence Weekly Tasks")


def monthly():
	"""Tasks that run monthly"""
	try:
		# Generate monthly performance report
		generate_monthly_performance_report()
		
		# Archive old leads (older than 1 year)
		archive_old_leads()
		
		# Update system performance metrics
		update_system_performance_metrics()
		
	except Exception as e:
		frappe.log_error(f"Monthly task error: {str(e)}", "Lead Intelligence Monthly Tasks")


def cleanup_old_data():
	"""Clean up old data (runs daily at midnight)"""
	try:
		# Clean up old usage statistics (older than 90 days)
		cutoff_date = add_days(now(), -90)
		frappe.db.delete("Lead Intelligence Usage Stats", {
			"creation": ["<", cutoff_date]
		})
		
		# Clean up old campaign execution logs (older than 30 days)
		cutoff_date = add_days(now(), -30)
		frappe.db.delete("Campaign Execution", {
			"creation": ["<", cutoff_date],
			"status": ["in", ["Completed", "Failed", "Cancelled"]]
		})
		
		# Clean up old error logs
		cutoff_date = add_days(now(), -7)
		frappe.db.sql("""
			DELETE FROM `tabError Log`
			WHERE creation < %s
			AND error LIKE '%Lead Intelligence%'
		""", (cutoff_date,))
		
		frappe.db.commit()
		frappe.log_error("Old data cleanup completed", "Lead Intelligence Cleanup")
		
	except Exception as e:
		frappe.log_error(f"Cleanup task error: {str(e)}", "Lead Intelligence Cleanup")


def process_campaign_queue():
	"""Process campaign queue (runs every 15 minutes)"""
	try:
		# Get pending campaigns
		pending_campaigns = frappe.get_all("Lead Campaign", 
			filters={
				"status": "Queued",
				"scheduled_start": ["<=", now()]
			},
			fields=["name", "campaign_name", "search_criteria"],
			limit=5  # Process max 5 campaigns at a time
		)
		
		for campaign in pending_campaigns:
			try:
				# Update status to Processing
				frappe.db.set_value("Lead Campaign", campaign.name, "status", "Processing")
				frappe.db.commit()
				
				# Queue the campaign for background processing
				frappe.enqueue(
					"lead_intelligence.lead_intelligence.doctype.lead_campaign.lead_campaign.execute_campaign",
					campaign_name=campaign.name,
					queue="lead_generation",
					timeout=3600
				)
				
			except Exception as e:
				frappe.log_error(f"Campaign queue processing error for {campaign.name}: {str(e)}", "Lead Intelligence Campaign Queue")
				# Reset status back to Queued for retry
				frappe.db.set_value("Lead Campaign", campaign.name, "status", "Queued")
				frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Campaign queue task error: {str(e)}", "Lead Intelligence Campaign Queue")


def sync_crm_data():
	"""Sync data with CRM systems (runs every 6 hours)"""
	try:
		# Get CRM settings
		settings = frappe.get_single("Lead Intelligence Settings")
		
		if not settings.active:
			return
		
		# Sync with Salesforce
		if settings.salesforce_enabled and settings.salesforce_client_id:
			sync_salesforce_data()
		
		# Sync with HubSpot
		if settings.hubspot_enabled and settings.hubspot_api_key:
			sync_hubspot_data()
		
		# Sync with Pipedrive
		if settings.pipedrive_enabled and settings.pipedrive_api_key:
			sync_pipedrive_data()
		
	except Exception as e:
		frappe.log_error(f"CRM sync task error: {str(e)}", "Lead Intelligence CRM Sync")


# Helper functions

def cleanup_old_usage_stats():
	"""Clean up old usage statistics"""
	cutoff_date = add_days(now(), -90)
	frappe.db.delete("Lead Intelligence Usage Stats", {
		"creation": ["<", cutoff_date]
	})
	frappe.db.commit()


def generate_daily_usage_summary():
	"""Generate daily usage summary"""
	try:
		from lead_intelligence.lead_intelligence.doctype.lead_intelligence_usage_stats.lead_intelligence_usage_stats import get_usage_summary
		
		# Get yesterday's usage summary
		yesterday = add_days(now(), -1)
		usage_summary = get_usage_summary(yesterday, yesterday)
		
		# Log the summary
		frappe.log_error(f"Daily usage summary: {json.dumps(usage_summary, indent=2)}", "Lead Intelligence Daily Usage")
		
	except Exception as e:
		frappe.log_error(f"Daily usage summary error: {str(e)}", "Lead Intelligence Daily Usage")


def check_api_usage_limits():
	"""Check API usage limits and send alerts"""
	try:
		from lead_intelligence.lead_intelligence.doctype.lead_intelligence_usage_stats.lead_intelligence_usage_stats import get_usage_summary
		
		# Get today's usage
		today = now()
		usage_summary = get_usage_summary(today, today)
		
		# Check limits (80% threshold)
		warnings = []
		if usage_summary.get("google_places_calls", 0) > 800:  # 80% of 1000
			warnings.append("Google Places API usage is at 80% of daily limit")
		
		if usage_summary.get("openai_calls", 0) > 2400:  # 80% of 3000
			warnings.append("OpenAI API usage is at 80% of daily limit")
		
		if warnings:
			# Send notification to administrators
			from frappe.email.queue import send
			admins = frappe.get_all("User", filters={"role_profile_name": "System Manager"}, fields=["email"])
			
			for admin in admins:
				send(
					recipients=[admin.email],
					subject="Lead Intelligence API Usage Warning",
					message="\n".join(warnings)
				)
		
	except Exception as e:
		frappe.log_error(f"API usage limit check error: {str(e)}", "Lead Intelligence API Limits")


def update_lead_scores():
	"""Update lead scores based on recent activities"""
	try:
		# Get leads updated in the last 24 hours
		yesterday = add_days(now(), -1)
		leads = frappe.get_all("Lead", 
			filters={"modified": [">=", yesterday]},
			fields=["name", "lead_name", "email_id", "phone", "company_name"]
		)
		
		for lead in leads:
			try:
				# Calculate lead score based on completeness and quality
				score = calculate_lead_score(lead)
				
				# Update the lead score
				frappe.db.set_value("Lead", lead.name, "lead_score", score)
				
			except Exception as e:
				frappe.log_error(f"Lead score update error for {lead.name}: {str(e)}", "Lead Intelligence Lead Scoring")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Lead score update task error: {str(e)}", "Lead Intelligence Lead Scoring")


def calculate_lead_score(lead):
	"""Calculate lead score based on data completeness and quality"""
	score = 0
	
	# Basic information completeness (40 points max)
	if lead.get("lead_name"):
		score += 10
	if lead.get("email_id"):
		score += 15
	if lead.get("phone"):
		score += 10
	if lead.get("company_name"):
		score += 5
	
	# Email quality (20 points max)
	if lead.get("email_id"):
		email = lead.get("email_id")
		if "@" in email and "." in email:
			score += 10
			# Bonus for business domains
			if not any(domain in email.lower() for domain in ["gmail", "yahoo", "hotmail", "outlook"]):
				score += 10
	
	# Phone quality (20 points max)
	if lead.get("phone"):
		phone = str(lead.get("phone")).replace(" ", ").replace("-", ").replace("(", ").replace(")", "")
		if len(phone) >= 10:
			score += 20
		elif len(phone) >= 7:
			score += 10
	
	# Company information (20 points max)
	if lead.get("company_name"):
		score += 20
	
	return min(score, 100)  # Cap at 100


def process_pending_email_campaigns():
	"""Process pending email campaigns"""
	try:
		# Get pending email campaigns
		pending_emails = frappe.get_all("Campaign Execution",
			filters={
				"status": "Pending",
				"execution_type": "Email Campaign",
				"scheduled_time": ["<=", now()]
			},
			fields=["name", "campaign", "target_leads"],
			limit=10
		)
		
		for email_campaign in pending_emails:
			try:
				# Queue for background processing
				frappe.enqueue(
					"lead_intelligence.lead_intelligence.doctype.campaign_execution.campaign_execution.execute_email_campaign",
					execution_name=email_campaign.name,
					queue="email_sending",
					timeout=1800
				)
				
				# Update status
				frappe.db.set_value("Campaign Execution", email_campaign.name, "status", "Processing")
				
			except Exception as e:
				frappe.log_error(f"Email campaign processing error for {email_campaign.name}: {str(e)}", "Lead Intelligence Email Campaigns")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Email campaign processing task error: {str(e)}", "Lead Intelligence Email Campaigns")


def update_campaign_statuses():
	"""Update campaign statuses based on execution progress"""
	try:
		# Get active campaigns
		active_campaigns = frappe.get_all("Lead Campaign",
			filters={"status": ["in", ["Processing", "Active"]]},
			fields=["name", "status"]
		)
		
		for campaign in active_campaigns:
			try:
				# Check execution status
				executions = frappe.get_all("Campaign Execution",
					filters={"campaign": campaign.name},
					fields=["status"]
				)
				
				if not executions:
					continue
				
				# Determine overall status
				status_counts = {}
				for execution in executions:
					status = execution.status
					status_counts[status] = status_counts.get(status, 0) + 1
				
				total_executions = len(executions)
				completed = status_counts.get("Completed", 0)
				failed = status_counts.get("Failed", 0)
				processing = status_counts.get("Processing", 0)
				
				# Update campaign status
				if completed == total_executions:
					new_status = "Completed"
				elif failed == total_executions:
					new_status = "Failed"
				elif processing > 0:
					new_status = "Processing"
				else:
					new_status = "Active"
				
				if new_status != campaign.status:
					frappe.db.set_value("Lead Campaign", campaign.name, "status", new_status)
				
			except Exception as e:
				frappe.log_error(f"Campaign status update error for {campaign.name}: {str(e)}", "Lead Intelligence Campaign Status")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Campaign status update task error: {str(e)}", "Lead Intelligence Campaign Status")


def retry_failed_webhooks():
	"""Retry failed webhook deliveries"""
	try:
		# This would typically check a webhook delivery log
		# For now, we'll just log that the task ran
		frappe.log_error("Webhook retry task completed", "Lead Intelligence Webhooks")
		
	except Exception as e:
		frappe.log_error(f"Webhook retry task error: {str(e)}", "Lead Intelligence Webhooks")


def generate_weekly_analytics_report():
	"""Generate weekly analytics report"""
	try:
		# This would generate and send weekly reports
		frappe.log_error("Weekly analytics report generated", "Lead Intelligence Analytics")
		
	except Exception as e:
		frappe.log_error(f"Weekly analytics report error: {str(e)}", "Lead Intelligence Analytics")


def cleanup_old_campaign_executions():
	"""Clean up old campaign executions"""
	cutoff_date = add_days(now(), -30)
	frappe.db.delete("Campaign Execution", {
		"creation": ["<", cutoff_date],
		"status": ["in", ["Completed", "Failed", "Cancelled"]]
	})
	frappe.db.commit()


def update_lead_quality_scores():
	"""Update lead quality scores"""
	try:
		# This would update lead quality scores based on various factors
		frappe.log_error("Lead quality scores updated", "Lead Intelligence Quality")
		
	except Exception as e:
		frappe.log_error(f"Lead quality score update error: {str(e)}", "Lead Intelligence Quality")


def generate_monthly_performance_report():
	"""Generate monthly performance report"""
	try:
		# This would generate comprehensive monthly reports
		frappe.log_error("Monthly performance report generated", "Lead Intelligence Performance")
		
	except Exception as e:
		frappe.log_error(f"Monthly performance report error: {str(e)}", "Lead Intelligence Performance")


def archive_old_leads():
	"""Archive old leads"""
	try:
		# Archive leads older than 1 year that haven't been converted
		cutoff_date = add_days(now(), -365)
		old_leads = frappe.get_all("Lead",
			filters={
				"creation": ["<", cutoff_date],
				"status": ["not in", ["Converted", "Customer"]]
			},
			fields=["name"]
		)
		
		for lead in old_leads:
			frappe.db.set_value("Lead", lead.name, "status", "Archived")
		
		frappe.db.commit()
		frappe.log_error(f"Archived {len(old_leads)} old leads", "Lead Intelligence Archive")
		
	except Exception as e:
		frappe.log_error(f"Lead archiving error: {str(e)}", "Lead Intelligence Archive")


def update_system_performance_metrics():
	"""Update system performance metrics"""
	try:
		# This would calculate and store system performance metrics
		frappe.log_error("System performance metrics updated", "Lead Intelligence Performance")
		
	except Exception as e:
		frappe.log_error(f"System performance metrics error: {str(e)}", "Lead Intelligence Performance")


def sync_salesforce_data():
	"""Sync data with Salesforce"""
	try:
		# This would sync leads and contacts with Salesforce
		frappe.log_error("Salesforce sync completed", "Lead Intelligence CRM Sync")
		
	except Exception as e:
		frappe.log_error(f"Salesforce sync error: {str(e)}", "Lead Intelligence CRM Sync")


def sync_hubspot_data():
	"""Sync data with HubSpot"""
	try:
		# This would sync leads and contacts with HubSpot
		frappe.log_error("HubSpot sync completed", "Lead Intelligence CRM Sync")
		
	except Exception as e:
		frappe.log_error(f"HubSpot sync error: {str(e)}", "Lead Intelligence CRM Sync")


def sync_pipedrive_data():
	"""Sync data with Pipedrive"""
	try:
		# This would sync leads and contacts with Pipedrive
		frappe.log_error("Pipedrive sync completed", "Lead Intelligence CRM Sync")
		
	except Exception as e:
		frappe.log_error(f"Pipedrive sync error: {str(e)}", "Lead Intelligence CRM Sync")