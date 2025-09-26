from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import secrets
from app import bcrypt
from app.models import User
from app.utils import validate_password, send_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        print("DEBUG: Signup form submitted")  # Debug line
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        print(f"DEBUG: Username: {username}, Email: {email}")  # Debug line
        
        if not all([username, email, password]):
            flash("All fields are required.", "warning")
            return redirect(url_for("auth.signup"))

        if not validate_password(password):
            flash("Password must be at least 8 characters, include uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for("auth.signup"))

        try:
            # Check if username or email already exists
            if current_app.users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
                flash("Username or email already exists.", "danger")
                return redirect(url_for("auth.signup"))

            hashed = bcrypt.generate_password_hash(password).decode("utf-8")
            
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            
            # Insert user with verification data
            user_data = {
                "username": username,
                "email": email,
                "password": hashed,
                "verified": False,
                "verification_token": verification_token,
                "created_at": datetime.utcnow(),
                "reset_token": None,
                "reset_token_expiry": None
            }
            
            result = current_app.users_col.insert_one(user_data)
            print(f"DEBUG: User inserted with ID: {result.inserted_id}")  # Debug line
            
            # Send verification email
            verify_url = url_for('auth.verify_email', token=verification_token, _external=True)
        
            # Render HTML email template
            html_body = render_template(
                'emails/verify_email.html',
                username=username,
                verification_link=verify_url
            )
            
            # Send the email with HTML content
            if send_email(email, "Verify Your Email - Movie App", html_body, html=True):
                flash('Account created! Please check your email to verify your account.', 'success')
            else:
                flash('Account created but error sending verification email.', 'warning')
            
            return redirect(url_for("auth.login"))
            
        except Exception as e:
            print(f"ERROR in signup: {e}")  # Debug line
            flash("An error occurred during signup. Please try again.", "danger")
            return redirect(url_for("auth.signup"))
    
    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user_doc = current_app.users_col.find_one({"username": username})
        
        if user_doc and bcrypt.check_password_hash(user_doc["password"], password):
            if not user_doc.get("verified", False):
                flash('Please verify your email before logging in.', 'warning')
                return redirect(url_for("auth.login"))
            
            # Create User object with the document (using your existing User class)
            user_obj = User(user_doc)
            login_user(user_obj)
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.index"))
        
        flash("Invalid credentials.", "danger")
    
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("main.index"))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].lower()
        print(f"DEBUG: Password reset requested for email: {email}")
        
        # Check if email exists
        user = current_app.users_col.find_one({"email": email})
        
        if user:
            print(f"DEBUG: User found: {user['username']}")
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(hours=1)
            
            # Store token in database
            current_app.users_col.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "reset_token": reset_token,
                    "reset_token_expiry": expiry
                }}
            )
            
            # Get IP and location info (simplified version)
            ip_address = request.remote_addr
            # For now, use a simple location - you can implement IP geolocation later
            location = "Your Location"  # Replace with actual geolocation if needed
            time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # FIXED: Use datetime.now() directly
            
            # Send reset email using HTML template
            reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
            print(f"DEBUG: Reset URL: {reset_url}")
            
            html_body = render_template(
                'emails/password_reset.html',
                username=user['username'],
                reset_link=reset_url,
                ip_address=ip_address,
                location=location,
                time=time
            )
            
            # Create text version
            text_body = f"""
Password Reset Request for Movie App

Hello {user['username']},

We received a request to reset your password from IP address: {ip_address}
Location: {location}
Time: {time}

Click this link to reset your password: {reset_url}

This link will expire in 1 hour.

If you didn't request this password reset, please ignore this email.

Need help? Contact our support team at support@movieapp.com
"""
            
            print("DEBUG: Templates rendered successfully")
            
            if send_email(email, "Password Reset Request - Movie App", html_body, text_body):
                flash('Password reset link sent to your email', 'success')
                print("DEBUG: Email sent successfully")
            else:
                flash('Error sending email. Please try again.', 'danger')
                print("DEBUG: Email sending failed")
        else:
            # For security, don't reveal if email exists or not
            flash('If that email exists in our system, a password reset link has been sent.', 'info')
            print("DEBUG: Email not found in database")
        
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Check if token is valid and not expired
    user = current_app.users_col.find_one({
        "reset_token": token,
        "reset_token_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        flash('Invalid or expired reset token', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html')
        
        if not validate_password(password):
            flash('Password must be at least 8 characters, include uppercase, lowercase, number, and special character.', 'danger')
            return render_template('reset_password.html')
        
        # Update password and clear reset token
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        current_app.users_col.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password": hashed_password,
                "reset_token": None,
                "reset_token_expiry": None,
                "verified": True  # AUTO-VERIFY AFTER PASSWORD RESET
            }}
        )
        
        flash('Password reset successfully. You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html')

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = current_app.users_col.find_one({"verification_token": token})
    
    if user:
        # Check if token is not expired (24 hours)
        if datetime.utcnow() - user.get("created_at", datetime.utcnow()) > timedelta(hours=24):
            flash('Verification link has expired. Please sign up again.', 'danger')
            current_app.users_col.delete_one({"_id": user["_id"]})  # Remove unverified user
            return redirect(url_for("auth.signup"))
        
        current_app.users_col.update_one(
            {"_id": user["_id"]},
            {"$set": {"verified": True, "verification_token": None}}
        )
        flash('Email verified successfully! You can now login.', 'success')
    else:
        flash('Invalid verification token', 'danger')
    
    return redirect(url_for("auth.login"))