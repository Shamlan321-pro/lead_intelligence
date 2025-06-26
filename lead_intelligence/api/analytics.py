# Analytics API

import frappe
from frappe import _
from frappe.utils import nowdate, now, add_days, getdate, flt, cint
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json


@frappe.whitelist()
def get_dashboard_analytics(date_range: str = '30') -> Dict[str, Any]:
    """
    Get comprehensive dashboard analytics
    
    Args:
        date_range: Number of days to analyze (default: 30)
    
    Returns:
        Dictionary containing dashboard analytics
    """
    try:
        days = cint(date_range)
        end_date = getdate(nowdate())
        start_date = add_days(end_date, -days)
        
        # Get overview metrics
        overview = get_overview_metrics(start_date, end_date)
        
        # Get campaign performance
        campaign_performance = get_campaign_performance_summary(start_date, end_date)
        
        # Get lead analytics
        lead_analytics = get_lead_analytics_summary(start_date, end_date)
        
        # Get email performance
        email_performance = get_email_performance_summary(start_date, end_date)
        
        # Get trend data
        trends = get_trend_data(start_date, end_date)
        
        # Get top performers
        top_performers = get_top_performers(start_date, end_date)
        
        return {
            'success': True,
            'data': {
                'overview': overview,
                'campaign_performance': campaign_performance,
                'lead_analytics': lead_analytics,
                'email_performance': email_performance,
                'trends': trends,
                'top_performers': top_performers,
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': days
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Dashboard analytics failed: {str(e)}", "Analytics Error")
        return {
            'success': False,
            'error': _("Failed to retrieve dashboard analytics")
        }


@frappe.whitelist()
def get_campaign_analytics(campaign_id: Optional[str] = None, date_range: str = '30') -> Dict[str, Any]:
    """
    Get detailed campaign analytics
    
    Args:
        campaign_id: Specific campaign ID (optional)
        date_range: Number of days to analyze
    
    Returns:
        Dictionary containing campaign analytics
    """
    try:
        days = cint(date_range)
        end_date = getdate(nowdate())
        start_date = add_days(end_date, -days)
        
        filters = {
            'creation': ['between', [start_date, end_date]]
        }
        
        if campaign_id:
            filters['name'] = campaign_id
        
        # Get campaign data
        campaigns = frappe.get_all('Lead Campaign',
            filters=filters,
            fields=['*']
        )
        
        analytics_data = []
        
        for campaign in campaigns:
            # Get campaign executions
            executions = frappe.get_all('Campaign Execution',
                filters={'lead_campaign': campaign.name},
                fields=['*']
            )
            
            # Calculate metrics
            metrics = calculate_campaign_metrics(campaign, executions)
            
            # Get lead breakdown
            lead_breakdown = get_campaign_lead_breakdown(campaign.name)
            
            # Get performance over time
            performance_timeline = get_campaign_performance_timeline(campaign.name)
            
            analytics_data.append({
                'campaign': campaign,
                'metrics': metrics,
                'lead_breakdown': lead_breakdown,
                'performance_timeline': performance_timeline,
                'executions': executions
            })
        
        return {
            'success': True,
            'data': analytics_data
        }
        
    except Exception as e:
        frappe.log_error(f"Campaign analytics failed: {str(e)}", "Analytics Error")
        return {
            'success': False,
            'error': _("Failed to retrieve campaign analytics")
        }


@frappe.whitelist()
def get_lead_analytics(filters: Optional[Dict[str, Any]] = None, date_range: str = '30') -> Dict[str, Any]:
    """
    Get detailed lead analytics
    
    Args:
        filters: Optional filters for leads
        date_range: Number of days to analyze
    
    Returns:
        Dictionary containing lead analytics
    """
    try:
        days = cint(date_range)
        end_date = getdate(nowdate())
        start_date = add_days(end_date, -days)
        
        # Build filters
        lead_filters = {
            'creation': ['between', [start_date, end_date]]
        }
        
        if filters:
            lead_filters.update(filters)
        
        # Get lead data
        leads = frappe.get_all('Lead',
            filters=lead_filters,
            fields=['*']
        )
        
        # Calculate analytics
        analytics = {
            'total_leads': len(leads),
            'status_distribution': get_lead_status_distribution(leads),
            'source_distribution': get_lead_source_distribution(leads),
            'industry_distribution': get_lead_industry_distribution(leads),
            'location_distribution': get_lead_location_distribution(leads),
            'quality_distribution': get_lead_quality_distribution(leads),
            'conversion_funnel': get_lead_conversion_funnel(leads),
            'daily_trends': get_lead_daily_trends(start_date, end_date),
            'top_sources': get_top_lead_sources(leads),
            'performance_metrics': calculate_lead_performance_metrics(leads)
        }
        
        return {
            'success': True,
            'data': analytics
        }
        
    except Exception as e:
        frappe.log_error(f"Lead analytics failed: {str(e)}", "Analytics Error")
        return {
            'success': False,
            'error': _("Failed to retrieve lead analytics")
        }


@frappe.whitelist()
def get_email_analytics(template_id: Optional[str] = None, date_range: str = '30') -> Dict[str, Any]:
    """
    Get email performance analytics
    
    Args:
        template_id: Specific template ID (optional)
        date_range: Number of days to analyze
    
    Returns:
        Dictionary containing email analytics
    """
    try:
        days = cint(date_range)
        end_date = getdate(nowdate())
        start_date = add_days(end_date, -days)
        
        # Get email data from campaign executions
        filters = {
            'creation': ['between', [start_date, end_date]]
        }
        
        executions = frappe.get_all('Campaign Execution',
            filters=filters,
            fields=['*']
        )
        
        # Calculate email metrics
        email_metrics = calculate_email_metrics(executions, template_id)
        
        # Get template performance
        template_performance = get_template_performance(template_id, start_date, end_date)
        
        # Get email trends
        email_trends = get_email_trends(start_date, end_date)
        
        return {
            'success': True,
            'data': {
                'metrics': email_metrics,
                'template_performance': template_performance,
                'trends': email_trends,
                'best_performing_templates': get_best_performing_templates(start_date, end_date),
                'subject_line_analysis': get_subject_line_analysis(start_date, end_date)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Email analytics failed: {str(e)}", "Analytics Error")
        return {
            'success': False,
            'error': _("Failed to retrieve email analytics")
        }


@frappe.whitelist()
def get_roi_analytics(date_range: str = '30') -> Dict[str, Any]:
    """
    Get ROI and cost analytics
    
    Args:
        date_range: Number of days to analyze
    
    Returns:
        Dictionary containing ROI analytics
    """
    try:
        days = cint(date_range)
        end_date = getdate(nowdate())
        start_date = add_days(end_date, -days)
        
        # Calculate costs
        total_costs = calculate_total_costs(start_date, end_date)
        
        # Calculate revenue (this would need to be integrated with sales data)
        revenue_data = calculate_revenue_data(start_date, end_date)
        
        # Calculate ROI metrics
        roi_metrics = {
            'total_investment': total_costs['total'],
            'total_revenue': revenue_data['total'],
            'roi_percentage': calculate_roi_percentage(revenue_data['total'], total_costs['total']),
            'cost_per_lead': calculate_cost_per_lead(total_costs['total'], start_date, end_date),
            'cost_per_conversion': calculate_cost_per_conversion(total_costs['total'], start_date, end_date),
            'customer_acquisition_cost': calculate_customer_acquisition_cost(start_date, end_date)
        }
        
        # Get cost breakdown
        cost_breakdown = {
            'api_costs': total_costs['api_costs'],
            'ai_costs': total_costs['ai_costs'],
            'email_costs': total_costs['email_costs'],
            'other_costs': total_costs['other_costs']
        }
        
        # Get ROI trends
        roi_trends = get_roi_trends(start_date, end_date)
        
        return {
            'success': True,
            'data': {
                'roi_metrics': roi_metrics,
                'cost_breakdown': cost_breakdown,
                'roi_trends': roi_trends,
                'benchmarks': get_roi_benchmarks()
            }
        }
        
    except Exception as e:
        frappe.log_error(f"ROI analytics failed: {str(e)}", "Analytics Error")
        return {
            'success': False,
            'error': _("Failed to retrieve ROI analytics")
        }


@frappe.whitelist()
def export_analytics_report(report_type: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Export analytics report
    
    Args:
        report_type: Type of report to export
        filters: Optional filters for the report
    
    Returns:
        Dictionary containing export information
    """
    try:
        # Generate report data based on type
        if report_type == 'dashboard':
            data = get_dashboard_analytics(filters.get('date_range', '30'))
        elif report_type == 'campaigns':
            data = get_campaign_analytics(filters.get('campaign_id'), filters.get('date_range', '30'))
        elif report_type == 'leads':
            data = get_lead_analytics(filters.get('lead_filters'), filters.get('date_range', '30'))
        elif report_type == 'emails':
            data = get_email_analytics(filters.get('template_id'), filters.get('date_range', '30'))
        elif report_type == 'roi':
            data = get_roi_analytics(filters.get('date_range', '30'))
        else:
            return {
                'success': False,
                'error': _("Invalid report type")
            }
        
        # Create export file (this would typically generate CSV/Excel)
        export_data = prepare_export_data(data, report_type)
        
        return {
            'success': True,
            'export_data': export_data,
            'filename': f"{report_type}_analytics_{nowdate()}.json"
        }
        
    except Exception as e:
        frappe.log_error(f"Analytics export failed: {str(e)}", "Analytics Error")
        return {
            'success': False,
            'error': _("Failed to export analytics report")
        }


# Helper Functions

def get_overview_metrics(start_date, end_date) -> Dict[str, Any]:
    """
    Get overview metrics for dashboard
    """
    # Total leads
    total_leads = frappe.db.count('Lead', {
        'creation': ['between', [start_date, end_date]]
    })
    
    # Active campaigns
    active_campaigns = frappe.db.count('Lead Campaign', {
        'status': 'Active'
    })
    
    # Total emails sent
    total_emails = frappe.db.sql("""
        SELECT SUM(emails_sent) 
        FROM `tabCampaign Execution` 
        WHERE creation BETWEEN %s AND %s
    """, [start_date, end_date])[0][0] or 0
    
    # Conversion rate
    converted_leads = frappe.db.count('Lead', {
        'creation': ['between', [start_date, end_date]],
        'status': ['in', ['Converted', 'Opportunity']]
    })
    
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    return {
        'total_leads': total_leads,
        'active_campaigns': active_campaigns,
        'total_emails': total_emails,
        'conversion_rate': round(conversion_rate, 2)
    }


def get_campaign_performance_summary(start_date, end_date) -> Dict[str, Any]:
    """
    Get campaign performance summary
    """
    campaigns = frappe.get_all('Lead Campaign',
        filters={'creation': ['between', [start_date, end_date]]},
        fields=['name', 'campaign_name', 'status', 'leads_created', 'target_lead_count']
    )
    
    performance = {
        'total_campaigns': len(campaigns),
        'active_campaigns': len([c for c in campaigns if c.status == 'Active']),
        'completed_campaigns': len([c for c in campaigns if c.status == 'Completed']),
        'total_leads_generated': sum(c.leads_created or 0 for c in campaigns),
        'average_completion_rate': 0
    }
    
    if campaigns:
        completion_rates = [
            (c.leads_created or 0) / (c.target_lead_count or 1) * 100 
            for c in campaigns if c.target_lead_count
        ]
        performance['average_completion_rate'] = round(sum(completion_rates) / len(completion_rates), 2) if completion_rates else 0
    
    return performance


def get_lead_analytics_summary(start_date, end_date) -> Dict[str, Any]:
    """
    Get lead analytics summary
    """
    leads = frappe.get_all('Lead',
        filters={'creation': ['between', [start_date, end_date]]},
        fields=['status', 'source', 'industry']
    )
    
    return {
        'total_leads': len(leads),
        'new_leads': len([l for l in leads if l.status == 'Lead']),
        'qualified_leads': len([l for l in leads if l.status in ['Qualified', 'Opportunity']]),
        'converted_leads': len([l for l in leads if l.status == 'Converted']),
        'top_sources': get_top_values([l.source for l in leads if l.source], 5),
        'top_industries': get_top_values([l.industry for l in leads if l.industry], 5)
    }


def get_email_performance_summary(start_date, end_date) -> Dict[str, Any]:
    """
    Get email performance summary
    """
    executions = frappe.get_all('Campaign Execution',
        filters={'creation': ['between', [start_date, end_date]]},
        fields=['emails_sent', 'emails_delivered', 'emails_opened', 'emails_clicked', 'responses_received']
    )
    
    total_sent = sum(e.emails_sent or 0 for e in executions)
    total_delivered = sum(e.emails_delivered or 0 for e in executions)
    total_opened = sum(e.emails_opened or 0 for e in executions)
    total_clicked = sum(e.emails_clicked or 0 for e in executions)
    total_responses = sum(e.responses_received or 0 for e in executions)
    
    return {
        'total_sent': total_sent,
        'delivery_rate': round((total_delivered / total_sent * 100) if total_sent > 0 else 0, 2),
        'open_rate': round((total_opened / total_delivered * 100) if total_delivered > 0 else 0, 2),
        'click_rate': round((total_clicked / total_delivered * 100) if total_delivered > 0 else 0, 2),
        'response_rate': round((total_responses / total_delivered * 100) if total_delivered > 0 else 0, 2)
    }


def get_trend_data(start_date, end_date) -> Dict[str, List]:
    """
    Get trend data for charts
    """
    # Generate daily data points
    current_date = start_date
    trends = {
        'dates': [],
        'leads': [],
        'emails': [],
        'conversions': []
    }
    
    while current_date <= end_date:
        trends['dates'].append(current_date.strftime('%Y-%m-%d'))
        
        # Daily leads
        daily_leads = frappe.db.count('Lead', {
            'creation': ['between', [current_date, current_date]]
        })
        trends['leads'].append(daily_leads)
        
        # Daily emails
        daily_emails = frappe.db.sql("""
            SELECT SUM(emails_sent) 
            FROM `tabCampaign Execution` 
            WHERE DATE(creation) = %s
        """, [current_date])[0][0] or 0
        trends['emails'].append(daily_emails)
        
        # Daily conversions
        daily_conversions = frappe.db.count('Lead', {
            'creation': ['between', [current_date, current_date]],
            'status': ['in', ['Converted', 'Opportunity']]
        })
        trends['conversions'].append(daily_conversions)
        
        current_date = add_days(current_date, 1)
    
    return trends


def get_top_performers(start_date, end_date) -> Dict[str, List]:
    """
    Get top performing campaigns, templates, etc.
    """
    # Top campaigns by leads generated
    top_campaigns = frappe.get_all('Lead Campaign',
        filters={'creation': ['between', [start_date, end_date]]},
        fields=['campaign_name', 'leads_created'],
        order_by='leads_created desc',
        limit=5
    )
    
    # Top templates by usage
    top_templates = frappe.get_all('Outreach Template',
        fields=['template_name', 'usage_count'],
        order_by='usage_count desc',
        limit=5
    )
    
    return {
        'campaigns': top_campaigns,
        'templates': top_templates
    }


def calculate_campaign_metrics(campaign, executions) -> Dict[str, Any]:
    """
    Calculate metrics for a specific campaign
    """
    total_emails_sent = sum(e.emails_sent or 0 for e in executions)
    total_emails_delivered = sum(e.emails_delivered or 0 for e in executions)
    total_emails_opened = sum(e.emails_opened or 0 for e in executions)
    total_emails_clicked = sum(e.emails_clicked or 0 for e in executions)
    total_responses = sum(e.responses_received or 0 for e in executions)
    
    return {
        'leads_created': campaign.leads_created or 0,
        'target_completion': round((campaign.leads_created or 0) / (campaign.target_lead_count or 1) * 100, 2),
        'emails_sent': total_emails_sent,
        'delivery_rate': round((total_emails_delivered / total_emails_sent * 100) if total_emails_sent > 0 else 0, 2),
        'open_rate': round((total_emails_opened / total_emails_delivered * 100) if total_emails_delivered > 0 else 0, 2),
        'click_rate': round((total_emails_clicked / total_emails_delivered * 100) if total_emails_delivered > 0 else 0, 2),
        'response_rate': round((total_responses / total_emails_delivered * 100) if total_emails_delivered > 0 else 0, 2)
    }


def get_campaign_lead_breakdown(campaign_id) -> Dict[str, int]:
    """
    Get lead status breakdown for a campaign
    """
    leads = frappe.get_all('Lead',
        filters={'custom_lead_campaign': campaign_id},
        fields=['status']
    )
    
    breakdown = {}
    for lead in leads:
        status = lead.status or 'Unknown'
        breakdown[status] = breakdown.get(status, 0) + 1
    
    return breakdown


def get_campaign_performance_timeline(campaign_id) -> List[Dict[str, Any]]:
    """
    Get performance timeline for a campaign
    """
    executions = frappe.get_all('Campaign Execution',
        filters={'lead_campaign': campaign_id},
        fields=['creation', 'emails_sent', 'leads_created'],
        order_by='creation asc'
    )
    
    timeline = []
    cumulative_leads = 0
    cumulative_emails = 0
    
    for execution in executions:
        cumulative_leads += execution.leads_created or 0
        cumulative_emails += execution.emails_sent or 0
        
        timeline.append({
            'date': execution.creation,
            'cumulative_leads': cumulative_leads,
            'cumulative_emails': cumulative_emails,
            'daily_leads': execution.leads_created or 0,
            'daily_emails': execution.emails_sent or 0
        })
    
    return timeline


def get_lead_status_distribution(leads) -> Dict[str, int]:
    """
    Get distribution of lead statuses
    """
    distribution = {}
    for lead in leads:
        status = lead.get('status', 'Unknown')
        distribution[status] = distribution.get(status, 0) + 1
    return distribution


def get_lead_source_distribution(leads) -> Dict[str, int]:
    """
    Get distribution of lead sources
    """
    distribution = {}
    for lead in leads:
        source = lead.get('source', 'Unknown')
        distribution[source] = distribution.get(source, 0) + 1
    return distribution


def get_lead_industry_distribution(leads) -> Dict[str, int]:
    """
    Get distribution of lead industries
    """
    distribution = {}
    for lead in leads:
        industry = lead.get('industry', 'Unknown')
        distribution[industry] = distribution.get(industry, 0) + 1
    return distribution


def get_lead_location_distribution(leads) -> Dict[str, int]:
    """
    Get distribution of lead locations
    """
    distribution = {}
    for lead in leads:
        location = lead.get('address_line1', 'Unknown')
        if location and ',' in location:
            location = location.split(',')[-1].strip()  # Get last part (usually city/state)
        distribution[location] = distribution.get(location, 0) + 1
    return distribution


def get_lead_quality_distribution(leads) -> Dict[str, int]:
    """
    Get distribution of lead quality scores
    """
    distribution = {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0}
    
    for lead in leads:
        # This would be based on a quality scoring system
        # For now, use a simple heuristic
        rating = lead.get('custom_business_rating', 0)
        if rating >= 4.0:
            distribution['High'] += 1
        elif rating >= 3.0:
            distribution['Medium'] += 1
        elif rating > 0:
            distribution['Low'] += 1
        else:
            distribution['Unknown'] += 1
    
    return distribution


def get_lead_conversion_funnel(leads) -> Dict[str, int]:
    """
    Get lead conversion funnel data
    """
    funnel = {
        'Total Leads': len(leads),
        'Qualified': 0,
        'Opportunity': 0,
        'Converted': 0
    }
    
    for lead in leads:
        status = lead.get('status', '')
        if status in ['Qualified', 'Opportunity', 'Converted']:
            funnel['Qualified'] += 1
        if status in ['Opportunity', 'Converted']:
            funnel['Opportunity'] += 1
        if status == 'Converted':
            funnel['Converted'] += 1
    
    return funnel


def get_lead_daily_trends(start_date, end_date) -> List[Dict[str, Any]]:
    """
    Get daily lead creation trends
    """
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_count = frappe.db.count('Lead', {
            'creation': ['between', [current_date, current_date]]
        })
        
        trends.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': daily_count
        })
        
        current_date = add_days(current_date, 1)
    
    return trends


def get_top_lead_sources(leads) -> List[Dict[str, Any]]:
    """
    Get top lead sources with counts
    """
    source_counts = {}
    for lead in leads:
        source = lead.get('source', 'Unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Sort by count and return top 10
    sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return [{'source': source, 'count': count} for source, count in sorted_sources]


def calculate_lead_performance_metrics(leads) -> Dict[str, float]:
    """
    Calculate lead performance metrics
    """
    total_leads = len(leads)
    if total_leads == 0:
        return {'conversion_rate': 0, 'qualification_rate': 0, 'opportunity_rate': 0}
    
    converted = len([l for l in leads if l.get('status') == 'Converted'])
    qualified = len([l for l in leads if l.get('status') in ['Qualified', 'Opportunity', 'Converted']])
    opportunities = len([l for l in leads if l.get('status') in ['Opportunity', 'Converted']])
    
    return {
        'conversion_rate': round(converted / total_leads * 100, 2),
        'qualification_rate': round(qualified / total_leads * 100, 2),
        'opportunity_rate': round(opportunities / total_leads * 100, 2)
    }


def calculate_email_metrics(executions, template_id=None) -> Dict[str, Any]:
    """
    Calculate email performance metrics
    """
    if template_id:
        # Filter executions by template (this would need template tracking)
        pass
    
    total_sent = sum(e.emails_sent or 0 for e in executions)
    total_delivered = sum(e.emails_delivered or 0 for e in executions)
    total_opened = sum(e.emails_opened or 0 for e in executions)
    total_clicked = sum(e.emails_clicked or 0 for e in executions)
    total_responses = sum(e.responses_received or 0 for e in executions)
    
    return {
        'total_sent': total_sent,
        'total_delivered': total_delivered,
        'total_opened': total_opened,
        'total_clicked': total_clicked,
        'total_responses': total_responses,
        'delivery_rate': round((total_delivered / total_sent * 100) if total_sent > 0 else 0, 2),
        'open_rate': round((total_opened / total_delivered * 100) if total_delivered > 0 else 0, 2),
        'click_rate': round((total_clicked / total_delivered * 100) if total_delivered > 0 else 0, 2),
        'response_rate': round((total_responses / total_delivered * 100) if total_delivered > 0 else 0, 2)
    }


def get_template_performance(template_id, start_date, end_date) -> List[Dict[str, Any]]:
    """
    Get performance data for email templates
    """
    templates = frappe.get_all('Outreach Template',
        fields=['name', 'template_name', 'usage_count', 'success_rate']
    )
    
    if template_id:
        templates = [t for t in templates if t.name == template_id]
    
    return templates


def get_email_trends(start_date, end_date) -> List[Dict[str, Any]]:
    """
    Get email performance trends over time
    """
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_executions = frappe.get_all('Campaign Execution',
            filters={'creation': ['between', [current_date, current_date]]},
            fields=['emails_sent', 'emails_delivered', 'emails_opened']
        )
        
        daily_sent = sum(e.emails_sent or 0 for e in daily_executions)
        daily_delivered = sum(e.emails_delivered or 0 for e in daily_executions)
        daily_opened = sum(e.emails_opened or 0 for e in daily_executions)
        
        trends.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'sent': daily_sent,
            'delivered': daily_delivered,
            'opened': daily_opened,
            'open_rate': round((daily_opened / daily_delivered * 100) if daily_delivered > 0 else 0, 2)
        })
        
        current_date = add_days(current_date, 1)
    
    return trends


def get_best_performing_templates(start_date, end_date) -> List[Dict[str, Any]]:
    """
    Get best performing email templates
    """
    templates = frappe.get_all('Outreach Template',
        fields=['name', 'template_name', 'success_rate', 'usage_count'],
        order_by='success_rate desc',
        limit=10
    )
    
    return templates


def get_subject_line_analysis(start_date, end_date) -> Dict[str, Any]:
    """
    Analyze subject line performance
    """
    # This would analyze subject lines from sent emails
    # For now, return placeholder data
    return {
        'avg_length': 45,
        'best_performing_words': ['Free', 'Quick', 'Exclusive', 'Limited'],
        'worst_performing_words': ['Spam', 'Buy', 'Urgent', 'Act Now'],
        'optimal_length_range': [30, 50]
    }


def calculate_total_costs(start_date, end_date) -> Dict[str, float]:
    """
    Calculate total costs for the period
    """
    # Get AI costs from executions
    ai_costs = frappe.db.sql("""
        SELECT SUM(cost_incurred) 
        FROM `tabCampaign Execution` 
        WHERE creation BETWEEN %s AND %s
    """, [start_date, end_date])[0][0] or 0
    
    # Other costs would be calculated based on usage
    api_costs = 0  # Google Places API costs
    email_costs = 0  # Email service costs
    other_costs = 0  # Other operational costs
    
    total = ai_costs + api_costs + email_costs + other_costs
    
    return {
        'total': total,
        'ai_costs': ai_costs,
        'api_costs': api_costs,
        'email_costs': email_costs,
        'other_costs': other_costs
    }


def calculate_revenue_data(start_date, end_date) -> Dict[str, float]:
    """
    Calculate revenue data (would need integration with sales)
    """
    # This would integrate with sales/opportunity data
    # For now, return placeholder
    return {
        'total': 0,
        'from_leads': 0,
        'pipeline_value': 0
    }


def calculate_roi_percentage(revenue, investment) -> float:
    """
    Calculate ROI percentage
    """
    if investment == 0:
        return 0
    return round((revenue - investment) / investment * 100, 2)


def calculate_cost_per_lead(total_cost, start_date, end_date) -> float:
    """
    Calculate cost per lead
    """
    total_leads = frappe.db.count('Lead', {
        'creation': ['between', [start_date, end_date]]
    })
    
    return round(total_cost / total_leads, 2) if total_leads > 0 else 0


def calculate_cost_per_conversion(total_cost, start_date, end_date) -> float:
    """
    Calculate cost per conversion
    """
    conversions = frappe.db.count('Lead', {
        'creation': ['between', [start_date, end_date]],
        'status': 'Converted'
    })
    
    return round(total_cost / conversions, 2) if conversions > 0 else 0


def calculate_customer_acquisition_cost(start_date, end_date) -> float:
    """
    Calculate customer acquisition cost
    """
    # This would be based on actual customer data
    return 0


def get_roi_trends(start_date, end_date) -> List[Dict[str, Any]]:
    """
    Get ROI trends over time
    """
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        # Calculate daily costs and revenue
        daily_costs = calculate_total_costs(current_date, current_date)
        daily_revenue = calculate_revenue_data(current_date, current_date)
        
        trends.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'cost': daily_costs['total'],
            'revenue': daily_revenue['total'],
            'roi': calculate_roi_percentage(daily_revenue['total'], daily_costs['total'])
        })
        
        current_date = add_days(current_date, 1)
    
    return trends


def get_roi_benchmarks() -> Dict[str, float]:
    """
    Get industry ROI benchmarks
    """
    return {
        'industry_average_roi': 400,  # 4:1 ratio
        'good_roi_threshold': 300,
        'excellent_roi_threshold': 500,
        'average_cost_per_lead': 50,
        'average_conversion_rate': 2.5
    }


def get_top_values(values, limit=5) -> List[Dict[str, Any]]:
    """
    Get top values with counts
    """
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    
    sorted_values = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{'value': value, 'count': count} for value, count in sorted_values]


def prepare_export_data(data, report_type) -> Dict[str, Any]:
    """
    Prepare data for export
    """
    # This would format the data for CSV/Excel export
    return {
        'report_type': report_type,
        'generated_at': now(),
        'data': data
    }