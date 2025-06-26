// Lead Intelligence - Customer DocType JavaScript

frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        // Add custom buttons for Lead Intelligence features
        if (!frm.doc.__islocal) {
            add_customer_intelligence_buttons(frm);
            setup_customer_score_display(frm);
            show_lead_conversion_info(frm);
        }
    },
    
    email_id: function(frm) {
        // Validate email and check for lead history
        if (frm.doc.email_id && validate_email(frm.doc.email_id)) {
            check_lead_history(frm);
        }
    },
    
    before_save: function(frm) {
        // Update customer intelligence data before saving
        update_customer_intelligence_data(frm);
    }
});

function add_customer_intelligence_buttons(frm) {
    // View Lead History button
    frm.add_custom_button(__('Lead History'), function() {
        show_lead_history(frm);
    }, __('Lead Intelligence'));
    
    // Analyze Customer button
    frm.add_custom_button(__('Analyze Customer'), function() {
        analyze_customer(frm);
    }, __('Lead Intelligence'));
    
    // Export Customer Data button
    frm.add_custom_button(__('Export Data'), function() {
        export_customer_data(frm);
    }, __('Lead Intelligence'));
    
    // Update Score button
    frm.add_custom_button(__('Update Score'), function() {
        update_customer_score(frm);
    }, __('Lead Intelligence'));
    
    // View Analytics button
    frm.add_custom_button(__('View Analytics'), function() {
        show_customer_analytics(frm);
    }, __('Lead Intelligence'));
}

function setup_customer_score_display(frm) {
    if (frm.doc.engagement_score !== undefined && frm.doc.engagement_score !== null) {
        const score = frm.doc.engagement_score;
        const level = get_engagement_level(score);
        
        // Create score display HTML
        const scoreHtml = `
            <div class="customer-score-display">
                <div class="score-circle ${level.toLowerCase()}">
                    <span class="score-value">${Math.round(score)}</span>
                </div>
                <div class="score-details">
                    <div class="score-label">Engagement Score</div>
                    <div class="level-badge ${level.toLowerCase()}">${level}</div>
                </div>
            </div>
        `;
        
        // Add to form sidebar
        frm.sidebar.add_user_action(scoreHtml);
    }
}

function show_lead_conversion_info(frm) {
    // Check if this customer was converted from a lead
    if (frm.doc.conversion_source) {
        const conversionHtml = `
            <div class="conversion-info">
                <div class="conversion-header">
                    <i class="fa fa-exchange"></i>
                    <span>Converted from Lead</span>
                </div>
                <div class="conversion-details">
                    <div class="conversion-source">
                        <strong>Source:</strong> ${frm.doc.conversion_source}
                    </div>
                    ${frm.doc.original_lead_score ? `
                        <div class="original-score">
                            <strong>Original Lead Score:</strong> ${frm.doc.original_lead_score}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        frm.dashboard.add_section(conversionHtml, __('Lead Intelligence'));
    }
}

function check_lead_history(frm) {
    if (frm.doc.email_id) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Lead',
                filters: {
                    email_id: frm.doc.email_id
                },
                fields: ['name', 'lead_name', 'company_name', 'lead_score', 'lead_quality', 'creation'],
                order_by: 'creation desc',
                limit: 5
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    show_lead_history_indicator(frm, r.message);
                }
            }
        });
    }
}

function show_lead_history_indicator(frm, leads) {
    const leadCount = leads.length;
    const latestLead = leads[0];
    
    const historyHtml = `
        <div class="lead-history-indicator">
            <div class="history-header">
                <i class="fa fa-history"></i>
                <span>${leadCount} Previous Lead${leadCount > 1 ? 's' : ''}</span>
            </div>
            <div class="latest-lead">
                <strong>Latest:</strong> 
                <a href="/app/lead/${latestLead.name}">${latestLead.lead_name || latestLead.company_name}</a>
                ${latestLead.lead_score ? `(Score: ${Math.round(latestLead.lead_score)})` : ''}
            </div>
        </div>
    `;
    
    frm.dashboard.add_section(historyHtml, __('Lead History'));
}

function show_lead_history(frm) {
    if (!frm.doc.email_id) {
        frappe.msgprint(__('Email ID is required to view lead history'));
        return;
    }
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Lead',
            filters: {
                email_id: frm.doc.email_id
            },
            fields: [
                'name', 'lead_name', 'company_name', 'email_id', 'phone',
                'lead_score', 'lead_quality', 'campaign_source', 'status',
                'creation', 'modified'
            ],
            order_by: 'creation desc'
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                show_lead_history_dialog(r.message);
            } else {
                frappe.msgprint(__('No lead history found for this email'));
            }
        }
    });
}

function show_lead_history_dialog(leads) {
    const dialog = new frappe.ui.Dialog({
        title: __('Lead History'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'lead_history_html'
            }
        ]
    });
    
    let html = '<div class="lead-history-table">';
    html += '<table class="table table-bordered">';
    html += '<thead><tr>';
    html += '<th>Lead Name</th><th>Company</th><th>Score</th><th>Quality</th><th>Source</th><th>Status</th><th>Created</th>';
    html += '</tr></thead><tbody>';
    
    leads.forEach(lead => {
        html += '<tr>';
        html += `<td><a href="/app/lead/${lead.name}">${lead.lead_name || '-'}</a></td>`;
        html += `<td>${lead.company_name || '-'}</td>`;
        html += `<td>${lead.lead_score ? Math.round(lead.lead_score) : '-'}</td>`;
        html += `<td><span class="quality-badge ${(lead.lead_quality || '').toLowerCase()}">${lead.lead_quality || '-'}</span></td>`;
        html += `<td>${lead.campaign_source || '-'}</td>`;
        html += `<td>${lead.status || '-'}</td>`;
        html += `<td>${frappe.datetime.str_to_user(lead.creation)}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    dialog.fields_dict.lead_history_html.$wrapper.html(html);
    dialog.show();
}

function analyze_customer(frm) {
    frappe.show_alert({
        message: __('Analyzing customer data...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'lead_intelligence.api.analyze_customer',
        args: {
            customer_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                show_customer_analysis(r.message.analysis);
                
                // Update engagement score if provided
                if (r.message.engagement_score) {
                    frm.set_value('engagement_score', r.message.engagement_score);
                    setup_customer_score_display(frm);
                }
                
                frappe.show_alert({
                    message: __('Customer analysis completed'),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to analyze customer'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            frappe.show_alert({
                message: __('Error analyzing customer'),
                indicator: 'red'
            });
        }
    });
}

function show_customer_analysis(analysis) {
    const dialog = new frappe.ui.Dialog({
        title: __('Customer Analysis'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analysis_html'
            }
        ]
    });
    
    let html = '<div class="customer-analysis">';
    
    // Engagement metrics
    if (analysis.engagement_metrics) {
        html += '<h4>Engagement Metrics</h4>';
        html += '<div class="metrics-grid">';
        for (const [key, value] of Object.entries(analysis.engagement_metrics)) {
            html += `<div class="metric-item">
                <span class="metric-label">${key.replace('_', ' ').toUpperCase()}</span>
                <span class="metric-value">${value}</span>
            </div>`;
        }
        html += '</div>';
    }
    
    // Purchase history
    if (analysis.purchase_history) {
        html += '<h4>Purchase History</h4>';
        html += '<div class="purchase-summary">';
        html += `<p>Total Orders: ${analysis.purchase_history.total_orders || 0}</p>`;
        html += `<p>Total Value: ${analysis.purchase_history.total_value || 0}</p>`;
        html += `<p>Average Order Value: ${analysis.purchase_history.avg_order_value || 0}</p>`;
        html += '</div>';
    }
    
    // Recommendations
    if (analysis.recommendations && analysis.recommendations.length > 0) {
        html += '<h4>Recommendations</h4>';
        html += '<ul class="recommendations-list">';
        analysis.recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    
    dialog.fields_dict.analysis_html.$wrapper.html(html);
    dialog.show();
}

function export_customer_data(frm) {
    const filters = {
        customer_id: frm.doc.name
    };
    
    frappe.call({
        method: 'lead_intelligence.api.export_customer_data',
        args: {
            filters: JSON.stringify(filters)
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __('Customer data exported successfully'),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to export customer data'),
                    indicator: 'red'
                });
            }
        }
    });
}

function update_customer_score(frm) {
    frappe.call({
        method: 'lead_intelligence.api.calculate_customer_engagement_score',
        args: {
            customer_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frm.set_value('engagement_score', r.message.score);
                
                frappe.show_alert({
                    message: __('Customer score updated: ') + Math.round(r.message.score),
                    indicator: 'green'
                });
                
                setup_customer_score_display(frm);
            } else {
                frappe.show_alert({
                    message: r.message.error || __('Failed to update customer score'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_customer_analytics(frm) {
    frappe.call({
        method: 'lead_intelligence.api.get_customer_analytics',
        args: {
            customer_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                show_analytics_dialog(r.message.analytics);
            } else {
                frappe.msgprint(__('Failed to load customer analytics'));
            }
        }
    });
}

function show_analytics_dialog(analytics) {
    const dialog = new frappe.ui.Dialog({
        title: __('Customer Analytics'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analytics_html'
            }
        ]
    });
    
    let html = '<div class="customer-analytics">';
    
    // Timeline
    if (analytics.timeline) {
        html += '<h4>Customer Timeline</h4>';
        html += '<div class="timeline">';
        analytics.timeline.forEach(event => {
            html += `<div class="timeline-item">
                <div class="timeline-date">${frappe.datetime.str_to_user(event.date)}</div>
                <div class="timeline-content">${event.description}</div>
            </div>`;
        });
        html += '</div>';
    }
    
    // Performance metrics
    if (analytics.performance) {
        html += '<h4>Performance Metrics</h4>';
        html += '<div class="performance-grid">';
        for (const [key, value] of Object.entries(analytics.performance)) {
            html += `<div class="performance-item">
                <span class="performance-label">${key.replace('_', ' ').toUpperCase()}</span>
                <span class="performance-value">${value}</span>
            </div>`;
        }
        html += '</div>';
    }
    
    html += '</div>';
    
    dialog.fields_dict.analytics_html.$wrapper.html(html);
    dialog.show();
}

function update_customer_intelligence_data(frm) {
    // Update any intelligence-related fields before saving
    if (frm.doc.email_id && !frm.doc.engagement_score) {
        // Calculate initial engagement score
        update_customer_score(frm);
    }
}

function get_engagement_level(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Average';
    if (score >= 20) return 'Poor';
    return 'Very Poor';
}

function validate_email(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Export functions for use in other modules
window.LeadIntelligence = window.LeadIntelligence || {};
window.LeadIntelligence.Customer = {
    showLeadHistory: show_lead_history,
    analyzeCustomer: analyze_customer,
    updateScore: update_customer_score,
    showAnalytics: show_customer_analytics
};