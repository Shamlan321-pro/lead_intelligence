// Lead Intelligence - Lead DocType JavaScript

frappe.ui.form.on('Lead', {
    refresh: function(frm) {
        // Add custom buttons for Lead Intelligence features
        if (!frm.doc.__islocal) {
            add_lead_intelligence_buttons(frm);
            setup_lead_score_display(frm);
            setup_quality_indicator(frm);
        }
        
        // Auto-calculate lead score on form load
        if (frm.doc.lead_score === undefined || frm.doc.lead_score === null) {
            calculate_lead_score(frm);
        }
    },
    
    email_id: function(frm) {
        // Validate email and trigger enrichment if auto-enrich is enabled
        if (frm.doc.email_id && validate_email(frm.doc.email_id)) {
            check_auto_enrich_settings(frm);
        }
    },
    
    company_name: function(frm) {
        // Trigger enrichment when company name changes
        if (frm.doc.company_name) {
            check_auto_enrich_settings(frm);
        }
    },
    
    phone: function(frm) {
        // Validate and format phone number
        if (frm.doc.phone) {
            format_phone_number(frm);
        }
    },
    
    before_save: function(frm) {
        // Calculate lead score before saving
        if (should_recalculate_score(frm)) {
            calculate_lead_score(frm);
        }
    }
});

function add_lead_intelligence_buttons(frm) {
    // Enrich Lead Data button
    frm.add_custom_button(__('Enrich Data'), function() {
        enrich_lead_data(frm);
    }, __('Lead Intelligence'));
    
    // Calculate Score button
    frm.add_custom_button(__('Calculate Score'), function() {
        calculate_lead_score(frm);
    }, __('Lead Intelligence'));
    
    // View Insights button
    frm.add_custom_button(__('View Insights'), function() {
        show_lead_insights(frm);
    }, __('Lead Intelligence'));
    
    // Export Lead button
    frm.add_custom_button(__('Export Lead'), function() {
        export_single_lead(frm);
    }, __('Lead Intelligence'));
    
    // Add to Campaign button
    frm.add_custom_button(__('Add to Campaign'), function() {
        add_to_campaign(frm);
    }, __('Lead Intelligence'));
}

function setup_lead_score_display(frm) {
    if (frm.doc.lead_score !== undefined && frm.doc.lead_score !== null) {
        const score = frm.doc.lead_score;
        const quality = frm.doc.lead_quality || 'Unknown';
        
        // Create score display HTML
        const scoreHtml = `
            <div class="lead-score-display">
                <div class="score-circle ${quality.toLowerCase()}">
                    <span class="score-value">${Math.round(score)}</span>
                </div>
                <div class="score-details">
                    <div class="score-label">Lead Score</div>
                    <div class="quality-badge ${quality.toLowerCase()}">${quality}</div>
                </div>
            </div>
        `;
        
        // Add to form sidebar
        frm.sidebar.add_user_action(scoreHtml);
    }
}

function setup_quality_indicator(frm) {
    if (frm.doc.lead_quality) {
        const quality = frm.doc.lead_quality;
        const colors = {
            'Hot': '#ff4757',
            'Warm': '#ffa502',
            'Cold': '#3742fa',
            'Unqualified': '#747d8c'
        };
        
        // Add quality indicator to form
        const indicator = `
            <div class="quality-indicator" style="background-color: ${colors[quality] || '#747d8c'}">
                ${quality}
            </div>
        `;
        
        frm.dashboard.add_indicator(indicator);
    }
}

function enrich_lead_data(frm) {
    frappe.show_alert({
        message: __('Enriching lead data...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'lead_intelligence.api.enrich_lead',
        args: {
            lead_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Lead data enriched successfully'),
                    indicator: 'green'
                });
                
                // Refresh form to show updated data
                frm.reload_doc();
                
                // Show enrichment results
                if (r.message.data) {
                    show_enrichment_results(r.message.data);
                }
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to enrich lead data'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            frappe.show_alert({
                message: __('Error enriching lead data'),
                indicator: 'red'
            });
        }
    });
}

function calculate_lead_score(frm) {
    frappe.call({
        method: 'lead_intelligence.api.calculate_lead_score_api',
        args: {
            lead_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.set_value('lead_score', r.message.score);
                frm.set_value('lead_quality', r.message.quality);
                
                frappe.show_alert({
                    message: r.message.message,
                    indicator: 'green'
                });
                
                // Update score display
                setup_lead_score_display(frm);
                setup_quality_indicator(frm);
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to calculate lead score'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_lead_insights(frm) {
    frappe.call({
        method: 'lead_intelligence.api.get_lead_insights',
        args: {
            lead_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                show_insights_dialog(r.message.insights);
            } else {
                frappe.msgprint(__('Failed to load lead insights'));
            }
        }
    });
}

function show_insights_dialog(insights) {
    const dialog = new frappe.ui.Dialog({
        title: __('Lead Insights'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'insights_html'
            }
        ]
    });
    
    // Build insights HTML
    let html = '<div class="lead-insights">';
    
    // Score breakdown
    if (insights.score_breakdown) {
        html += '<h4>Score Breakdown</h4>';
        html += '<div class="score-breakdown">';
        for (const [key, value] of Object.entries(insights.score_breakdown)) {
            html += `<div class="score-item">
                <span class="score-label">${key.replace('_', ' ').toUpperCase()}</span>
                <span class="score-value">${Math.round(value)}%</span>
            </div>`;
        }
        html += '</div>';
    }
    
    // Recommendations
    if (insights.recommendations && insights.recommendations.length > 0) {
        html += '<h4>Recommendations</h4>';
        html += '<ul class="recommendations-list">';
        insights.recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
        html += '</ul>';
    }
    
    // Next actions
    if (insights.next_actions && insights.next_actions.length > 0) {
        html += '<h4>Suggested Next Actions</h4>';
        html += '<ul class="actions-list">';
        insights.next_actions.forEach(action => {
            html += `<li>${action}</li>`;
        });
        html += '</ul>';
    }
    
    // Similar leads
    if (insights.similar_leads && insights.similar_leads.length > 0) {
        html += '<h4>Similar Leads</h4>';
        html += '<div class="similar-leads">';
        insights.similar_leads.forEach(lead => {
            html += `<div class="similar-lead">
                <a href="/app/lead/${lead.name}">${lead.lead_name || lead.company_name}</a>
                <span class="lead-score">${Math.round(lead.lead_score || 0)}</span>
            </div>`;
        });
        html += '</div>';
    }
    
    html += '</div>';
    
    dialog.fields_dict.insights_html.$wrapper.html(html);
    dialog.show();
}

function export_single_lead(frm) {
    const filters = {
        lead_id: frm.doc.name
    };
    
    frappe.call({
        method: 'lead_intelligence.api.export_leads',
        args: {
            filters: JSON.stringify(filters)
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __('Lead exported successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to export lead'),
                    indicator: 'red'
                });
            }
        }
    });
}

function add_to_campaign(frm) {
    // Get available campaigns
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Lead Intelligence Campaign',
            filters: {
                status: ['in', ['Draft', 'Active']]
            },
            fields: ['name', 'campaign_name', 'status']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                show_campaign_selection_dialog(frm, r.message);
            } else {
                frappe.msgprint(__('No active campaigns found'));
            }
        }
    });
}

function show_campaign_selection_dialog(frm, campaigns) {
    const dialog = new frappe.ui.Dialog({
        title: __('Add to Campaign'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'campaign',
                label: __('Select Campaign'),
                options: campaigns.map(c => c.name),
                reqd: 1
            }
        ],
        primary_action_label: __('Add to Campaign'),
        primary_action: function(values) {
            // Add lead to selected campaign
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'Lead',
                    name: frm.doc.name,
                    fieldname: 'campaign_source',
                    value: values.campaign
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Lead added to campaign successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
            dialog.hide();
        }
    });
    
    dialog.show();
}

function check_auto_enrich_settings(frm) {
    frappe.call({
        method: 'lead_intelligence.api.get_settings',
        callback: function(r) {
            if (r.message && r.message.auto_enrich_leads) {
                // Auto-enrich is enabled, trigger enrichment
                setTimeout(() => {
                    enrich_lead_data(frm);
                }, 1000);
            }
        }
    });
}

function should_recalculate_score(frm) {
    // Check if any scoring-relevant fields have changed
    const scoringFields = ['email_id', 'phone', 'company_name', 'website', 'lead_name'];
    return scoringFields.some(field => frm.doc.__unsaved && frm.doc[field] !== frm.doc.__original[field]);
}

function format_phone_number(frm) {
    const phone = frm.doc.phone;
    if (phone && phone.length > 0) {
        // Basic phone number formatting (can be enhanced)
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10) {
            const formatted = `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
            frm.set_value('phone', formatted);
        }
    }
}

function validate_email(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function show_enrichment_results(data) {
    if (data.company_info || data.social_profiles) {
        let message = 'Enrichment completed:';
        
        if (data.company_info) {
            message += `<br>• Company information updated`;
        }
        
        if (data.social_profiles) {
            message += `<br>• Social profiles found`;
        }
        
        frappe.msgprint({
            title: __('Enrichment Results'),
            message: message,
            indicator: 'green'
        });
    }
}

// Export functions for use in other modules
window.LeadIntelligence = window.LeadIntelligence || {};
window.LeadIntelligence.Lead = {
    enrichData: enrich_lead_data,
    calculateScore: calculate_lead_score,
    showInsights: show_lead_insights,
    exportLead: export_single_lead
};