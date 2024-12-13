
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from functools import wraps
import os
import hashlib
import dns.resolver
from models import Employer

def verify_domain_records(domain, provider):
    try:
        # Check CNAME record or A record
        try:
            # Try CNAME first
            try:
                cname_answers = dns.resolver.resolve(domain, 'CNAME')
                cname_valid = any(str(rdata.target).rstrip('.') == f"auth.{request.host}" for rdata in cname_answers)
            except:
                cname_valid = False
                
            # Try A record if CNAME fails
            if not cname_valid:
                try:
                    expected_ip = dns.resolver.resolve(f"auth.{request.host}", 'A')[0].address
                    a_answers = dns.resolver.resolve(domain, 'A')
                    cname_valid = any(str(rdata.address) == expected_ip for rdata in a_answers)
                except:
                    pass
        except:
            cname_valid = False
            
        # Check TXT record
        try:
            domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
            expected_txt = f"v=sso provider={provider} verify={domain_hash}"
            txt_answers = dns.resolver.resolve(domain, 'TXT')
            txt_valid = any(str(rdata).strip('"') == expected_txt for rdata in txt_answers)
        except:
            txt_valid = False
            
        return cname_valid or txt_valid
    except:
        return False

@admin_bp.route('/save-domain', methods=['POST'])
@login_required
@admin_required
def save_domain():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    provider = data.get('provider')
    domain = data.get('domain')
    
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
        
    # Check if domain is already in use by another employer
    existing = Employer.query.filter(
        Employer.sso_domain == domain,
        Employer.id != current_user.id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'error': 'Domain already in use'}), 400
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.sso_provider = provider.upper()
    db.session.commit()
    
    # Generate verification records
    domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
    cname_record = f"CNAME {domain} auth.{request.host}"
    txt_record = f"TXT {domain} \"v=sso provider={provider} verify={domain_hash}\""
    
    return jsonify({
        'success': True,
        'cname_record': cname_record,
        'txt_record': txt_record,
        'shadow_url': f"https://{domain}/login"  # Shadow interface URL
    })

@admin_bp.route('/update-domain', methods=['POST'])
@login_required
@admin_required
def update_domain():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    domain = data.get('domain')
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.domain_verified = False  # Reset verification status
    db.session.commit()
    
    return jsonify({'success': True})
