from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_custom_email(user, data, email_type="signup_otp"):
    """
    Send custom email to a user depending on the email_type (signup_otp, login_otp, register_token).
    Renders both HTML and plain text from templates and sends a multipart email.
    """
    templates = {
        'subscription_info': {
            'subject': 'Subscription Confirmation & Payment Instructions',
            'template_name': 'email/subscription_info.html',
            'txt_template_name': 'email/subscription_info.txt',
            'context': {
                'user': user,
                'amount': data.get('payment'),
                'start_date': data.get('start_date'),
                'end_date': data.get('end_date'),
                'duration': data.get('duration')
            }
        },
        'signup_otp': {
            'subject': 'Your Signup OTP Code',
            'template_name': 'email/signup_otp.html',
            'txt_template_name': 'email/signup_otp.txt',
            'context': {'otp': data.get('otp'), 'user': user}
        },
        'login_otp': {
            'subject': 'Your Login OTP Code',
            'template_name': 'email/login_otp.html',
            'txt_template_name': 'email/login_otp.txt',
            'context': {'otp': data.get('otp'), 'user': user}
        },
        'register_token': {
            'subject': 'Complete Your Registration',
            'template_name': 'email/register_token.html',
            'txt_template_name': 'email/register_token.txt',
            'context': {'token': data.get('token'), 'user': user}
        },
        'reset_password': {
            'subject': 'Reset Your Password',
            'template_name': 'email/reset_password.html',
            'txt_template_name': 'email/reset_password.txt',
            'context': {
                'user': user,
                'reset_url': data.get('reset_url')
            }
        },
        'subscription_token': {
            'subject': 'Your Subscription Token',
            'template_name': 'email/subscription_token.html',
            'txt_template_name': 'email/subscription_token.txt',
            'context': {'token': data.get('token'), 'user': user}
        }


    }

    template = templates.get(email_type)
    if not template:
        raise ValueError(f"Unsupported email_type: {email_type}")

    # Render templates
    html_content = render_to_string(
        template['template_name'], template['context'])
    text_content = render_to_string(
        template['txt_template_name'], template['context'])

    # Send email
    msg = EmailMultiAlternatives(
        subject=template['subject'],
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example.com>"}
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
