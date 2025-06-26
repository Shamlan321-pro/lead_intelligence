# Lead Generation API

import frappe
from frappe import _
from frappe.utils import nowdate, now, cint, flt, get_datetime
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


@frappe.whitelist()
def search_businesses(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for businesses based on specified criteria using Google Places API
    
    Args:
        filters: Dictionary containing search criteria
            - industry: Target industry
            - location: Geographic location
            - business_type: Type of business
            - min_employees: Minimum number of employees
            - max_employees: Maximum number of employees
            - keywords: Additional search keywords
            - radius: Search radius in kilometers
    
    Returns:
        Dictionary containing search results and metadata
    """
    try:
        # Validate required parameters
        if not filters.get('location'):
            frappe.throw(_("Location is required for business search"))
        
        # Get API configuration
        api_settings = frappe.get_single('Lead Intelligence Settings')
        if not api_settings.google_places_api_key:
            frappe.throw(_("Google Places API key not configured"))
        
        # Build search query
        query_parts = []
        if filters.get('industry'):
            query_parts.append(filters['industry'])
        if filters.get('business_type'):
            query_parts.append(filters['business_type'])
        if filters.get('keywords'):
            query_parts.append(filters['keywords'])
        
        search_query = ' '.join(query_parts) if query_parts else 'business'
        
        # Prepare API request
        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': f"{search_query} in {filters['location']}",
            'key': api_settings.google_places_api_key,
            'type': 'establishment'
        }
        
        if filters.get('radius'):
            params['radius'] = min(int(filters['radius']) * 1000, 50000)  # Convert to meters, max 50km
        
        # Make API request
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK':
            frappe.throw(_(f"Google Places API error: {data.get('error_message', 'Unknown error')}"))
        
        # Process results
        businesses = []
        for place in data.get('results', []):
            business = {
                'place_id': place.get('place_id'),
                'name': place.get('name'),
                'address': place.get('formatted_address'),
                'rating': place.get('rating'),
                'user_ratings_total': place.get('user_ratings_total'),
                'types': place.get('types', []),
                'price_level': place.get('price_level'),
                'geometry': place.get('geometry', {}),
                'photos': place.get('photos', []),
                'business_status': place.get('business_status')
            }
            businesses.append(business)
        
        # Apply additional filters
        filtered_businesses = apply_business_filters(businesses, filters)
        
        return {
            'success': True,
            'businesses': filtered_businesses,
            'total_found': len(filtered_businesses),
            'search_query': search_query,
            'location': filters['location'],
            'next_page_token': data.get('next_page_token')
        }
        
    except requests.RequestException as e:
        frappe.log_error(f"API request failed: {str(e)}", "Lead Generation API Error")
        return {
            'success': False,
            'error': _("Failed to connect to business search service"),
            'businesses': []
        }
    except Exception as e:
        frappe.log_error(f"Business search failed: {str(e)}", "Lead Generation Error")
        return {
            'success': False,
            'error': _("An error occurred while searching for businesses"),
            'businesses': []
        }


def apply_business_filters(businesses: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """
    Apply additional filters to business results
    """
    filtered = businesses
    
    # Filter by business types if specified
    if filters.get('excluded_types'):
        excluded_types = filters['excluded_types']
        filtered = [
            b for b in filtered 
            if not any(excluded_type in b.get('types', []) for excluded_type in excluded_types)
        ]
    
    # Filter by minimum rating
    if filters.get('min_rating'):
        min_rating = flt(filters['min_rating'])
        filtered = [b for b in filtered if flt(b.get('rating', 0)) >= min_rating]
    
    # Filter by minimum reviews
    if filters.get('min_reviews'):
        min_reviews = cint(filters['min_reviews'])
        filtered = [b for b in filtered if cint(b.get('user_ratings_total', 0)) >= min_reviews]
    
    return filtered


@frappe.whitelist()
def get_business_details(place_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific business
    
    Args:
        place_id: Google Places ID for the business
    
    Returns:
        Dictionary containing detailed business information
    """
    try:
        # Get API configuration
        api_settings = frappe.get_single('Lead Intelligence Settings')
        if not api_settings.google_places_api_key:
            frappe.throw(_("Google Places API key not configured"))
        
        # Prepare API request
        base_url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'key': api_settings.google_places_api_key,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,reviews,opening_hours,types,geometry,photos,business_status,price_level'
        }
        
        # Make API request
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK':
            frappe.throw(_(f"Google Places API error: {data.get('error_message', 'Unknown error')}"))
        
        result = data.get('result', {})
        
        # Extract contact information
        business_details = {
            'place_id': place_id,
            'name': result.get('name'),
            'address': result.get('formatted_address'),
            'phone': result.get('formatted_phone_number'),
            'website': result.get('website'),
            'rating': result.get('rating'),
            'user_ratings_total': result.get('user_ratings_total'),
            'types': result.get('types', []),
            'business_status': result.get('business_status'),
            'price_level': result.get('price_level'),
            'opening_hours': result.get('opening_hours', {}),
            'geometry': result.get('geometry', {}),
            'photos': result.get('photos', []),
            'reviews': result.get('reviews', [])
        }
        
        return {
            'success': True,
            'business': business_details
        }
        
    except Exception as e:
        frappe.log_error(f"Business details fetch failed: {str(e)}", "Lead Generation Error")
        return {
            'success': False,
            'error': _("Failed to fetch business details")
        }


@frappe.whitelist()
def create_leads_from_businesses(businesses: List[Dict], campaign_id: str) -> Dict[str, Any]:
    """
    Create Lead records from business search results
    
    Args:
        businesses: List of business dictionaries
        campaign_id: ID of the campaign creating these leads
    
    Returns:
        Dictionary containing creation results
    """
    try:
        created_leads = []
        failed_leads = []
        
        for business in businesses:
            try:
                # Check if lead already exists
                existing_lead = frappe.db.exists('Lead', {
                    'company_name': business.get('name'),
                    'address_line1': business.get('address')
                })
                
                if existing_lead:
                    failed_leads.append({
                        'business': business.get('name'),
                        'reason': 'Lead already exists'
                    })
                    continue
                
                # Create new lead
                lead_doc = frappe.new_doc('Lead')
                lead_doc.update({
                    'lead_name': business.get('name'),
                    'company_name': business.get('name'),
                    'address_line1': business.get('address'),
                    'phone': business.get('phone'),
                    'website': business.get('website'),
                    'source': 'Lead Intelligence',
                    'campaign_name': campaign_id,
                    'status': 'Lead',
                    'lead_type': 'Business',
                    'custom_place_id': business.get('place_id'),
                    'custom_business_rating': business.get('rating'),
                    'custom_business_types': json.dumps(business.get('types', [])),
                    'custom_lead_generation_date': nowdate()
                })
                
                # Extract potential contact person from reviews or use business name
                if business.get('reviews'):
                    # Try to extract owner/manager name from reviews
                    for review in business.get('reviews', [])[:3]:
                        author_name = review.get('author_name', '')
                        if author_name and 'owner' in review.get('text', '').lower():
                            lead_doc.first_name = author_name.split()[0] if author_name else ''
                            lead_doc.last_name = ' '.join(author_name.split()[1:]) if len(author_name.split()) > 1 else ''
                            break
                
                if not lead_doc.first_name:
                    lead_doc.first_name = 'Business'
                    lead_doc.last_name = 'Owner'
                
                lead_doc.insert(ignore_permissions=True)
                
                created_leads.append({
                    'lead_id': lead_doc.name,
                    'lead_name': lead_doc.lead_name,
                    'company_name': lead_doc.company_name
                })
                
            except Exception as e:
                failed_leads.append({
                    'business': business.get('name', 'Unknown'),
                    'reason': str(e)
                })
                frappe.log_error(f"Failed to create lead for {business.get('name')}: {str(e)}", "Lead Creation Error")
        
        # Update campaign statistics
        if campaign_id and created_leads:
            update_campaign_lead_count(campaign_id, len(created_leads))
        
        return {
            'success': True,
            'created_leads': created_leads,
            'failed_leads': failed_leads,
            'total_created': len(created_leads),
            'total_failed': len(failed_leads)
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk lead creation failed: {str(e)}", "Lead Generation Error")
        return {
            'success': False,
            'error': _("Failed to create leads from businesses"),
            'created_leads': [],
            'failed_leads': []
        }


def update_campaign_lead_count(campaign_id: str, new_leads_count: int):
    """
    Update the lead count for a campaign
    """
    try:
        campaign = frappe.get_doc('Lead Campaign', campaign_id)
        campaign.leads_created = (campaign.leads_created or 0) + new_leads_count
        campaign.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to update campaign lead count: {str(e)}", "Campaign Update Error")


@frappe.whitelist()
def enrich_lead_data(lead_id: str) -> Dict[str, Any]:
    """
    Enrich existing lead data with additional business information
    
    Args:
        lead_id: ID of the lead to enrich
    
    Returns:
        Dictionary containing enrichment results
    """
    try:
        lead = frappe.get_doc('Lead', lead_id)
        
        enrichment_data = {}
        
        # If we have a place_id, get detailed business information
        if lead.get('custom_place_id'):
            business_details = get_business_details(lead.custom_place_id)
            if business_details.get('success'):
                business = business_details['business']
                
                # Update lead with additional information
                if business.get('phone') and not lead.phone:
                    lead.phone = business['phone']
                    enrichment_data['phone'] = business['phone']
                
                if business.get('website') and not lead.website:
                    lead.website = business['website']
                    enrichment_data['website'] = business['website']
                
                # Add business insights
                lead.custom_business_rating = business.get('rating')
                lead.custom_total_reviews = business.get('user_ratings_total')
                lead.custom_business_types = json.dumps(business.get('types', []))
                
                enrichment_data.update({
                    'rating': business.get('rating'),
                    'total_reviews': business.get('user_ratings_total'),
                    'business_types': business.get('types', [])
                })
        
        # Try to find email addresses using company website
        if lead.website and not lead.email_id:
            email_candidates = extract_emails_from_website(lead.website)
            if email_candidates:
                lead.email_id = email_candidates[0]
                enrichment_data['email'] = email_candidates[0]
                enrichment_data['email_candidates'] = email_candidates
        
        # Save enriched lead data
        lead.save(ignore_permissions=True)
        
        return {
            'success': True,
            'lead_id': lead_id,
            'enrichment_data': enrichment_data
        }
        
    except Exception as e:
        frappe.log_error(f"Lead enrichment failed for {lead_id}: {str(e)}", "Lead Enrichment Error")
        return {
            'success': False,
            'error': _("Failed to enrich lead data")
        }


def extract_emails_from_website(website_url: str) -> List[str]:
    """
    Extract potential email addresses from a website
    
    Args:
        website_url: URL of the website to scan
    
    Returns:
        List of potential email addresses
    """
    try:
        import re
        
        # Make request to website
        response = requests.get(website_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Extract email addresses using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, response.text)
        
        # Filter out common non-contact emails
        filtered_emails = []
        exclude_patterns = ['noreply', 'no-reply', 'donotreply', 'support', 'info@example']
        
        for email in emails:
            if not any(pattern in email.lower() for pattern in exclude_patterns):
                filtered_emails.append(email)
        
        # Remove duplicates and return
        return list(set(filtered_emails))
        
    except Exception as e:
        frappe.log_error(f"Email extraction failed for {website_url}: {str(e)}", "Email Extraction Error")
        return []


@frappe.whitelist()
def get_lead_generation_stats() -> Dict[str, Any]:
    """
    Get statistics about lead generation activities
    
    Returns:
        Dictionary containing lead generation statistics
    """
    try:
        # Get date ranges
        today = nowdate()
        week_ago = frappe.utils.add_days(today, -7)
        month_ago = frappe.utils.add_days(today, -30)
        
        # Total leads generated
        total_leads = frappe.db.count('Lead', {
            'source': 'Lead Intelligence'
        })
        
        # Leads this week
        leads_this_week = frappe.db.count('Lead', {
            'source': 'Lead Intelligence',
            'creation': ['>=', week_ago]
        })
        
        # Leads this month
        leads_this_month = frappe.db.count('Lead', {
            'source': 'Lead Intelligence',
            'creation': ['>=', month_ago]
        })
        
        # Lead status distribution
        status_distribution = frappe.db.sql("""
            SELECT status, COUNT(*) as count
            FROM `tabLead`
            WHERE source = 'Lead Intelligence'
            GROUP BY status
        """, as_dict=True)
        
        # Top sources/campaigns
        campaign_stats = frappe.db.sql("""
            SELECT campaign_name, COUNT(*) as lead_count
            FROM `tabLead`
            WHERE source = 'Lead Intelligence' AND campaign_name IS NOT NULL
            GROUP BY campaign_name
            ORDER BY lead_count DESC
            LIMIT 10
        """, as_dict=True)
        
        # Conversion rates
        qualified_leads = frappe.db.count('Lead', {
            'source': 'Lead Intelligence',
            'status': ['in', ['Qualified', 'Converted']]
        })
        
        conversion_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            'success': True,
            'stats': {
                'total_leads': total_leads,
                'leads_this_week': leads_this_week,
                'leads_this_month': leads_this_month,
                'conversion_rate': round(conversion_rate, 2),
                'status_distribution': status_distribution,
                'campaign_stats': campaign_stats
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to get lead generation stats: {str(e)}", "Lead Generation Stats Error")
        return {
            'success': False,
            'error': _("Failed to retrieve lead generation statistics")
        }


@frappe.whitelist()
def validate_search_criteria(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate search criteria before executing business search
    
    Args:
        criteria: Search criteria to validate
    
    Returns:
        Dictionary containing validation results
    """
    try:
        errors = []
        warnings = []
        
        # Required fields
        if not criteria.get('location'):
            errors.append("Location is required")
        
        # Validate radius
        if criteria.get('radius'):
            radius = cint(criteria['radius'])
            if radius <= 0:
                errors.append("Radius must be greater than 0")
            elif radius > 50:
                warnings.append("Radius greater than 50km may return limited results")
        
        # Validate employee count range
        min_employees = cint(criteria.get('min_employees', 0))
        max_employees = cint(criteria.get('max_employees', 0))
        
        if min_employees > 0 and max_employees > 0 and min_employees > max_employees:
            errors.append("Minimum employees cannot be greater than maximum employees")
        
        # Check API configuration
        api_settings = frappe.get_single('Lead Intelligence Settings')
        if not api_settings.google_places_api_key:
            errors.append("Google Places API key not configured")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
        
    except Exception as e:
        frappe.log_error(f"Search criteria validation failed: {str(e)}", "Validation Error")
        return {
            'valid': False,
            'errors': ["Failed to validate search criteria"],
            'warnings': []
        }