import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Dict, List
import logging
from datetime import datetime, timezone
from btc_analyzer import BTCAnalyzer
import base64
import requests
from PIL import Image
import io

# Import the Imgur uploader
try:
    from imgur_uploader import ImgurUploader
except ImportError:
    ImgurUploader = None


class EnhancedNotificationHandler:
    """
    Enhanced notification handler with complete MSTR options strategy integration + Pi Cycle + NEW MSTR METRICS
    """

    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')

        # Support multiple recipients
        self.recipients = self._parse_recipients()
        # test mode for test email to admin
        test_mode = os.getenv('TEST_MODE', '').lower() in ['true', '1', 'yes']
        if test_mode:
            self.recipients = [self.email_user] if self.email_user else []
            logging.info(f"🧪 TEST MODE: All emails will be sent to {self.email_user} only")
        else:
            logging.info(f"📧 PRODUCTION MODE: Emails will be sent to {len(self.recipients)} recipients")

        self.btc_analyzer = BTCAnalyzer()

        # Imgur uploader for Gmail compatibility
        self.imgur_uploader = ImgurUploader() if ImgurUploader else None

        logging.info(f"Email configured for {len(self.recipients)} recipients")
        if self.imgur_uploader and self.imgur_uploader.client_id:
            logging.info("✅ Imgur uploader configured - will use external image hosting")
        else:
            logging.warning("⚠️ Imgur not configured - will use embedded images")

    def _parse_recipients(self) -> List[str]:
        """Parse email recipients from environment variables"""
        recipients = []

        # Multiple emails in RECIPIENT_EMAILS (comma-separated)
        recipient_emails = os.getenv('RECIPIENT_EMAILS', '').strip()
        if recipient_emails:
            emails = [email.strip() for email in recipient_emails.split(',') if email.strip()]
            recipients.extend(emails)
            logging.info(f"Found {len(emails)} emails in RECIPIENT_EMAILS")

        # Fallback to single RECIPIENT_EMAIL
        if not recipients:
            single_email = os.getenv('RECIPIENT_EMAIL', '').strip()
            if single_email:
                recipients.append(single_email)
                logging.info(f"Using single email from RECIPIENT_EMAIL")

        # Validate email addresses
        valid_recipients = []
        for email in recipients:
            if '@' in email and '.' in email:
                valid_recipients.append(email)
            else:
                logging.warning(f"Invalid email format: {email}")

        return valid_recipients

    def send_daily_report(self, data: Dict, alerts: List[Dict], bitcoin_laws_screenshot: str = "") -> None:
        """Send enhanced daily Bitcoin + MSTR report with complete options strategy and Pi Cycle + NEW METRICS"""
        try:
            # Get current date for report
            report_date = datetime.now(timezone.utc).strftime('%B %d, %Y')
            subject = f"📊 Dan's Bitcoin Report - {report_date}"

            # Try Imgur hosting first (most reliable for Gmail)
            imgur_url = None
            if bitcoin_laws_screenshot and self.imgur_uploader and self.imgur_uploader.client_id:
                try:
                    resized_screenshot = self._resize_screenshot_for_email(bitcoin_laws_screenshot, max_width=800,
                                                                           max_height=600)
                    imgur_url = self.imgur_uploader.upload_base64_image(
                        resized_screenshot,
                        f"Bitcoin Laws Screenshot - {report_date}"
                    )
                    if imgur_url:
                        logging.info(f"✅ Image uploaded to Imgur: {imgur_url}")
                    else:
                        logging.warning("⚠️ Imgur upload failed, falling back to embedded image")
                except Exception as e:
                    logging.error(f"Error uploading to Imgur: {str(e)}")

            # Generate HTML with appropriate image method
            if imgur_url:
                body = self._generate_enhanced_report_html_with_url(data, alerts, report_date, imgur_url)
                self._send_email_to_multiple(subject, body, is_html=True)
                logging.info(f"✅ Email sent with Imgur-hosted image")
            else:
                # Fallback methods (embedded images)
                logging.info("📎 Using embedded image method...")
                resized_screenshot = self._resize_screenshot_for_email(bitcoin_laws_screenshot)
                body = self._generate_enhanced_report_html(data, alerts, report_date, resized_screenshot)
                self._send_email_to_multiple(subject, body, is_html=True)
                logging.info(f"✅ Email sent with embedded image")

            logging.info(
                f'Enhanced Bitcoin + MSTR + Pi Cycle + Laws + NEW METRICS report sent to {len(self.recipients)} recipients')

        except Exception as e:
            logging.error(f'Error sending enhanced report: {str(e)}')
            # Final fallback: send without image
            try:
                logging.info("🚨 Sending text-only report as final fallback...")
                body = self._generate_enhanced_report_html(data, alerts, report_date, "")
                self._send_email_to_multiple(subject, body, is_html=True)
                logging.info('✅ Text-only fallback email sent successfully')
            except Exception as final_error:
                logging.error(f'All email methods failed: {str(final_error)}')

    def _resize_screenshot_for_email(self, screenshot_base64: str, max_width: int = 800, max_height: int = 600) -> str:
        """Resize screenshot for email with high quality"""
        if not screenshot_base64:
            return ""

        try:
            image_bytes = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_bytes))

            original_width, original_height = image.size
            logging.info(f"Original image size: {original_width}x{original_height}")

            # Calculate scaling
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = min(width_ratio, height_ratio)

            # Only resize if image is larger than max dimensions
            if scale_ratio < 1:
                new_width = int(original_width * scale_ratio)
                new_height = int(original_height * scale_ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logging.info(f"Resized image to: {new_width}x{new_height}")

            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    rgb_image.paste(image, mask=image.split()[-1])
                else:
                    rgb_image.paste(image)
                image = rgb_image

            # High quality save
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            resized_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')

            original_size = len(screenshot_base64)
            new_size = len(resized_base64)
            logging.info(f"Image optimization: {original_size:,} → {new_size:,} chars")

            return resized_base64

        except Exception as e:
            logging.error(f"Error resizing screenshot: {str(e)}")
            return ""

    def _generate_enhanced_report_html_with_url(self, data: Dict, alerts: List[Dict], report_date: str,
                                                image_url: str) -> str:
        """Generate HTML report using external image URL (Imgur-friendly) with Pi Cycle + NEW METRICS"""
        btc_data = data['assets'].get('BTC', {})
        mstr_data = data['assets'].get('MSTR', {})

        if 'error' in btc_data and 'error' in mstr_data:
            return self._generate_error_report_html(report_date, "Both BTC and MSTR collection failed")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                {self._get_email_css()}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Dan's Market Report</h1>
                    <h2>📅 {report_date}</h2>
                </div>

                <div class="assets-grid">
                    {self._generate_enhanced_btc_section_html(btc_data)}
                    {self._generate_enhanced_mstr_section_html(mstr_data)}
                </div>

                <div class="pi-cycle-section-container">
                    {self._generate_pi_cycle_section_html(btc_data)}
                </div>

                <div class="monetary-section-container">
                    {self._generate_monetary_section_html(data.get('monetary', {}))}
                </div>

                <div class="laws-section-container">
                    {self._generate_bitcoin_laws_section_html_url(image_url)}
                </div>

                {self._generate_project_footer_html()}
            </div>
        </body>
        </html>
        """
        return html

    def _generate_enhanced_report_html(self, data: Dict, alerts: List[Dict], report_date: str,
                                       bitcoin_laws_screenshot: str = "") -> str:
        """Generate enhanced HTML report with embedded images and Pi Cycle + NEW METRICS"""
        btc_data = data['assets'].get('BTC', {})
        mstr_data = data['assets'].get('MSTR', {})

        if 'error' in btc_data and 'error' in mstr_data:
            return self._generate_error_report_html(report_date, "Both BTC and MSTR collection failed")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                {self._get_email_css()}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Dan's Market Report</h1>
                    <h2>📅 {report_date}</h2>
                </div>

                <div class="assets-grid">
                    {self._generate_enhanced_btc_section_html(btc_data)}
                    {self._generate_enhanced_mstr_section_html(mstr_data)}
                </div>

                <div class="pi-cycle-section-container">
                    {self._generate_pi_cycle_section_html(btc_data)}
                </div>

                <div class="monetary-section-container">
                    {self._generate_monetary_section_html(data.get('monetary', {}))}
                </div>

                <div class="laws-section-container">
                    {self._generate_bitcoin_laws_section_html(bitcoin_laws_screenshot)}
                </div>

                {self._generate_project_footer_html()}
            </div>
        </body>
        </html>
        """
        return html

    def _generate_pi_cycle_section_html(self, btc_data: Dict) -> str:
        """
        🎯 FIXED: Pi Cycle section with CORRECT data access and NO CSS conflicts
        """
        try:
            # 🎯 CRITICAL FIX: Check if Pi Cycle data exists at the right path
            pi_cycle_data = btc_data.get('pi_cycle', {})

            # Debug logging to see what's happening
            logging.info(f"🔍 Pi Cycle Debug - btc_data keys: {list(btc_data.keys())}")
            logging.info(f"🔍 Pi Cycle Debug - pi_cycle_data exists: {bool(pi_cycle_data)}")
            if pi_cycle_data:
                logging.info(f"🔍 Pi Cycle Debug - pi_cycle success: {pi_cycle_data.get('success', False)}")

            # Handle missing or failed Pi Cycle data
            if not pi_cycle_data or not pi_cycle_data.get('success'):
                error_msg = pi_cycle_data.get('error', 'Unknown error') if pi_cycle_data else 'No data available'
                logging.warning(f"⚠️ Pi Cycle data unavailable: {error_msg}")

                return f"""
                <div class="pi-cycle-section">
                    <div class="pi-cycle-header">
                        <span class="pi-cycle-symbol">🥧 Pi Cycle Top Indicator</span>
                        <span style="color: #dc3545;">Data Unavailable</span>
                    </div>
                    <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #ddd;">
                        <div style="color: #555; font-size: 14px; margin-bottom: 12px; line-height: 1.4;">
                            ⚠️ Pi Cycle data collection failed: {error_msg}
                        </div>
                        <p style="margin: 5px 0; font-size: 12px; color: #666;">
                            💡 <strong>What is Pi Cycle Top?</strong> The most accurate Bitcoin cycle top predictor (95%+ accuracy within 3 days).
                            Signals when 111-day moving average crosses above 2× the 350-day moving average.
                        </p>
                    </div>
                </div>
                """

            # Extract Pi Cycle data safely
            current_values = pi_cycle_data.get('current_values', {})
            signal_status = pi_cycle_data.get('signal_status', {})
            interpretation = pi_cycle_data.get('interpretation', {})
            trend_analysis = pi_cycle_data.get('trend_analysis', {})

            # Safe extraction with defaults
            btc_price = current_values.get('btc_price', 0)
            ma_111 = current_values.get('ma_111', 0)
            ma_350_x2 = current_values.get('ma_350_x2', 0)
            gap_absolute = current_values.get('gap_absolute', 0)
            gap_percentage = current_values.get('gap_percentage', 0)

            proximity_level = signal_status.get('proximity_level', 'UNKNOWN')
            message = signal_status.get('message', 'Unknown status')
            description = signal_status.get('description', 'No description available')
            color = signal_status.get('color', '#6c757d')

            is_converging = trend_analysis.get('is_converging', False)
            trend_description = trend_analysis.get('trend_description', 'Unknown trend')
            trend_emoji = "📈" if is_converging else "📉"

            summary = interpretation.get('summary', 'No summary available')
            action = interpretation.get('action', 'No action specified')
            timeframe = interpretation.get('timeframe', 'No timeframe specified')

            logging.info(f"✅ Pi Cycle rendering: {proximity_level} ({gap_percentage:.1f}% gap)")

            # 🎯 SIMPLE HTML that uses INLINE STYLES to avoid CSS conflicts
            return f"""
            <div class="pi-cycle-section">
                <div class="pi-cycle-header">
                    <span class="pi-cycle-symbol">🥧 Pi Cycle Top Indicator</span>
                    <span style="color: {color}; font-size: 14px; font-weight: 600; background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 12px; margin-left: 15px;">{proximity_level.replace('_', ' ').title()}</span>
                </div>

                <div class="pi-cycle-content">
                    <!-- Signal Status -->
                    <div style="border-left: 4px solid {color}; background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="color: {color}; font-weight: 600; font-size: 16px; margin-bottom: 8px;">
                            {message}
                        </div>
                        <div style="color: #555; font-size: 14px;">
                            {description}
                        </div>
                    </div>

                    <!-- Simple 2x2 Grid with inline styles -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 15px;">
                        <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="font-size: 11px; color: #666; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">BTC PRICE</div>
                            <div style="font-size: 16px; font-weight: 700; color: #333;">${btc_price:,.0f}</div>
                        </div>
                        <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="font-size: 11px; color: #666; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">111-DAY MA</div>
                            <div style="font-size: 16px; font-weight: 700; color: #333;">${ma_111:,.0f}</div>
                        </div>
                        <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="font-size: 11px; color: #666; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">350-DAY MA × 2</div>
                            <div style="font-size: 16px; font-weight: 700; color: #333;">${ma_350_x2:,.0f}</div>
                        </div>
                        <div style="background: white; border: 1px solid #ddd; border-left: 3px solid {color}; border-radius: 6px; padding: 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="font-size: 11px; color: #666; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">GAP REMAINING</div>
                            <div style="font-size: 16px; font-weight: 700; color: #333;">${gap_absolute:,.0f}</div>
                            <div style="color: {color}; font-weight: 600; font-size: 12px;">({gap_percentage:.1f}%)</div>
                        </div>
                    </div>

                    <!-- Trend -->
                    <div style="background: white; padding: 12px; margin-bottom: 15px; border-radius: 6px; border: 1px solid #ddd;">
                        <div style="color: #333; font-size: 14px; font-weight: 600;">
                            {trend_emoji} <strong>Trend:</strong> {trend_description}
                        </div>
                    </div>

                    <!-- Interpretation -->
                    <div style="background: white; padding: 15px; border-radius: 6px; border: 1px solid #ddd;">
                        <div style="color: #333; font-size: 14px; font-weight: 600; margin-bottom: 8px;">
                            📋 <strong>Interpretation:</strong>
                        </div>
                        <div style="color: #555; font-size: 13px; line-height: 1.4;">
                            • <strong>Summary:</strong> {summary}<br>
                            • <strong>Action:</strong> {action}<br>
                            • <strong>Timeframe:</strong> {timeframe}
                        </div>
                    </div>

                    <!-- Explanation -->
                    <div style="background: linear-gradient(135deg, #e7f3ff, #cce7ff); border: 1px solid #6f42c1; border-radius: 6px; padding: 12px; margin-top: 15px;">
                        <div style="color: #495057; font-size: 13px; font-weight: 600; margin-bottom: 6px;">
                            💡 <strong>How to Read Pi Cycle Top:</strong>
                        </div>
                        <div style="color: #666; font-size: 12px; line-height: 1.4;">
                            The Pi Cycle Top indicator signals Bitcoin cycle tops when the 111-day moving average crosses above 
                            2× the 350-day moving average. Historically accurate within 3 days of major peaks (2013, 2017, 2021). 
                            The smaller the gap percentage, the closer to a potential cycle top.
                        </div>
                    </div>
                </div>
            </div>
            """

        except Exception as e:
            logging.error(f"❌ Error generating Pi Cycle HTML: {str(e)}")
            return f"""
            <div class="pi-cycle-section">
                <div class="pi-cycle-header">
                    <span class="pi-cycle-symbol">🥧 Pi Cycle Top Indicator</span>
                    <span style="color: #dc3545;">HTML Generation Error</span>
                </div>
                <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #ddd;">
                    <div style="color: #dc3545; font-size: 14px;">
                        ⚠️ Error generating Pi Cycle display: {str(e)}
                    </div>
                </div>
            </div>
            """

    def _generate_monetary_section_html(self, monetary_data: Dict) -> str:
        """Generate monetary policy section HTML"""
        if not monetary_data or not monetary_data.get('success'):
            return f"""
            <div class="monetary-section">
                <div class="monetary-header">
                    <span class="monetary-symbol">🏦 Monetary Policy Analysis</span>
                    <span style="color: #dc3545;">Data Unavailable</span>
                </div>
                <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #ddd;">
                    <div style="color: #555; font-size: 14px; margin-bottom: 12px; line-height: 1.4;">
                        ⚠️ Monetary data collection failed: {monetary_data.get('error', 'Unknown error') if monetary_data else 'No data provided'}
                    </div>
                    <p>🔗 <a href="https://fred.stlouisfed.org" target="_blank" style="color: #28a745; text-decoration: none; font-weight: 600;">
                        Visit FRED directly for latest data →
                    </a></p>
                </div>
            </div>
            """

        # Extract data
        data_date = monetary_data.get('data_date', 'Unknown')
        days_old = monetary_data.get('days_old', 0)
        fixed_rates = monetary_data.get('fixed_rates', {})
        table_data = monetary_data.get('table_data', [])
        true_inflation_rate = monetary_data.get('true_inflation_rate')
        m2_20y_growth = monetary_data.get('m2_20y_growth')

        # Format data freshness
        if days_old == 0:
            freshness = "Today"
        elif days_old == 1:
            freshness = "1 day ago"
        else:
            freshness = f"{days_old} days ago"

        # Generate fixed rates cards (updated 4-box layout)
        fixed_rates_html = ""

        if 'fed_funds' in fixed_rates:
            fixed_rates_html += f"""
            <div class="rate-card">
                <div class="rate-label">Fed Funds Rate</div>
                <div class="rate-value">{fixed_rates['fed_funds']:.2f}%</div>
            </div>
            """

        if 'real_rate' in fixed_rates:
            fixed_rates_html += f"""
            <div class="rate-card">
                <div class="rate-label">Real Interest Rate</div>
                <div class="rate-value">{fixed_rates['real_rate']:.1f}%</div>
                <div class="rate-description">Fed Funds - Core CPI</div>
            </div>
            """

        # True Inflation box
        if true_inflation_rate is not None:
            fixed_rates_html += f"""
            <div class="rate-card">
                <div class="rate-label">True Inflation</div>
                <div class="rate-value">{true_inflation_rate:.1f}%</div>
                <div class="rate-description">20Y M2 CAGR</div>
            </div>
            """
        else:
            fixed_rates_html += f"""
            <div class="rate-card">
                <div class="rate-label">True Inflation</div>
                <div class="rate-value">N/A</div>
                <div class="rate-description">20Y M2 CAGR</div>
            </div>
            """

        # Breakeven ROI box
        if true_inflation_rate is not None:
            breakeven_rate = true_inflation_rate / (1 - 0.25)  # Assume 25% tax rate
            fixed_rates_html += f"""
            <div class="rate-card">
                <div class="rate-label">Breakeven ROI</div>
                <div class="rate-value">{breakeven_rate:.1f}%</div>
                <div class="rate-description">After-tax (25%)</div>
            </div>
            """
        else:
            fixed_rates_html += f"""
            <div class="rate-card">
                <div class="rate-label">Breakeven ROI</div>
                <div class="rate-value">N/A</div>
                <div class="rate-description">After-tax (25%)</div>
            </div>
            """

        # Generate table rows
        table_rows_html = ""
        for row in table_data:
            table_rows_html += f"""
            <tr>
                <td>{row.get('metric', 'Unknown')}</td>
                <td class="neutral-change">{row.get('monthly', 'N/A')}</td>
                <td class="neutral-change">{row.get('ytd', 'N/A')}</td>
                <td class="neutral-change">{row.get('1y', 'N/A')}</td>
                <td class="neutral-change">{row.get('3y', 'N/A')}</td>
                <td class="neutral-change">{row.get('5y', 'N/A')}</td>
                <td class="neutral-change">{row.get('10y', 'N/A')}</td>
                <td class="neutral-change">{row.get('20y', 'N/A')}</td>
            </tr>
            """

        # Generate investment tools comparison table
        investment_tools_html = ""
        if true_inflation_rate is not None:
            investment_tools = [
                ("Savings Account", 0.5),
                ("Money Market", 2.0),
                ("1-Year CD", 4.5),
                ("10-Year Treasury", 4.3),
                ("S&P 500 (Historical)", 10.0)
            ]

            for tool_name, tool_return in investment_tools:
                real_return = tool_return - true_inflation_rate
                real_return_class = "positive-change" if real_return > 0 else "negative-change"

                investment_tools_html += f"""
                <tr>
                    <td>{tool_name}</td>
                    <td class="neutral-change">{tool_return:.1f}%</td>
                    <td class="{real_return_class}">{real_return:+.1f}%</td>
                </tr>
                """

        investment_tools_section = ""
        if investment_tools_html:
            investment_tools_section = f"""
            <div class="monetary-table-container" style="margin-top: 20px;">
                <h4 style="margin: 0 0 15px 0; color: #333; font-size: 16px; font-weight: 600;">💼 Traditional Investment Tools vs True Inflation</h4>
                <table class="monetary-table">
                    <thead>
                        <tr>
                            <th>Investment Tool</th>
                            <th>Return</th>
                            <th>Real Return*</th>
                        </tr>
                    </thead>
                    <tbody>
                        {investment_tools_html}
                    </tbody>
                </table>
                <div style="font-size: 12px; color: #666; margin-top: 8px;">
                    *vs True Inflation ({true_inflation_rate:.1f}%)
                </div>
            </div>
            """

        # Key Insight
        original_key_insight_html = f"""
        <div style="margin-top: 15px; padding: 15px; background: white; border-radius: 8px; border: 1px solid #dee2e6;">
            <div style="color: #555; font-size: 14px; margin-bottom: 12px; line-height: 1.4;">
                📈 <strong>Key Insight:</strong> Tracking monetary expansion vs reported inflation to assess true purchasing power impact and Bitcoin investment thesis.
            </div>
            <p>🔗 <a href="https://fred.stlouisfed.org" target="_blank" style="color: #28a745; text-decoration: none; font-weight: 600;">
                Source: Federal Reserve Economic Data (FRED) →
            </a></p>
        </div>
        """

        # Monetary Reality Insight
        additional_insight_html = ""
        if true_inflation_rate is not None:
            additional_insight_html = f"""
            <div style="margin-top: 15px; padding: 18px; background: linear-gradient(135deg, #fff8e1, #fff3cd); border-radius: 10px; border: 2px solid #ffcc02; box-shadow: 0 2px 8px rgba(255, 204, 2, 0.2);">
                <div style="color: #856404; font-size: 15px; line-height: 1.6; margin-bottom: 12px;">
                    💡 <strong style="font-size: 16px;">Monetary Reality:</strong> The M2 money supply and Fed balance sheet expansion represent the true rate of monetary debasement. While official CPI reports may show 2-3% annual inflation, the 20-year M2 expansion reveals a compound annual monetary inflation rate of <strong style="color: #b8860b; font-size: 16px;">{true_inflation_rate:.1f}%</strong> - more than double the reported rate.
                </div>
                <div style="color: #6c5214; font-size: 14px; line-height: 1.5; padding-top: 10px; border-top: 1px solid rgba(255, 204, 2, 0.3);">
                    This monetary expansion effectively transfers wealth from savers to asset holders, undermining the credibility of fiat currency and strengthening the case for <strong>Bitcoin as a store of value</strong> against monetary debasement.
                </div>
            </div>
            """
        else:
            additional_insight_html = f"""
            <div style="margin-top: 15px; padding: 18px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 10px; border: 2px solid #6c757d; box-shadow: 0 2px 8px rgba(108, 117, 125, 0.2);">
                <div style="color: #495057; font-size: 15px; line-height: 1.6; margin-bottom: 12px;">
                    💡 <strong style="font-size: 16px;">Monetary Reality:</strong> The M2 money supply and Fed balance sheet expansion represent the true rate of monetary debasement. While official CPI reports may show 2-3% annual inflation, historical M2 expansion typically reveals monetary inflation rates significantly higher than reported CPI.
                </div>
                <div style="color: #6c757d; font-size: 14px; line-height: 1.5; padding-top: 10px; border-top: 1px solid rgba(108, 117, 125, 0.3);">
                    This monetary expansion effectively transfers wealth from savers to asset holders, undermining the credibility of fiat currency and strengthening the case for <strong>Bitcoin as a store of value</strong> against monetary debasement.
                </div>
            </div>
            """

        return f"""
        <div class="monetary-section">
            <div class="monetary-header">
                <span class="monetary-symbol">🏦 Monetary Policy Analysis</span>
                <span class="monetary-date">Latest: {data_date} ({freshness})</span>
            </div>

            <!-- Fixed Rates Section -->
            <div class="fixed-rates-grid">
                {fixed_rates_html}
            </div>

            <!-- Main Table -->
            <div class="monetary-table-container">
                <table class="monetary-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Monthly</th>
                            <th>YTD</th>
                            <th>1Y</th>
                            <th>3Y</th>
                            <th>5Y</th>
                            <th>10Y</th>
                            <th>20Y</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>

            {investment_tools_section}

            {original_key_insight_html}

            {additional_insight_html}
        </div>
        """

    def _get_email_css(self) -> str:
        """Get complete CSS for email styling including Pi Cycle styles"""
        return """
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background-color: #f5f5f5; 
                font-size: 14px;
                line-height: 1.4;
            }

            .container { 
                max-width: 1000px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 12px; 
                overflow: hidden; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
            }

            .header { 
                background: linear-gradient(135deg, #1a1a1a, #333); 
                color: white; 
                padding: 30px; 
                text-align: center; 
            }
            .header h1 { 
                margin: 0; 
                font-size: 28px; 
                font-weight: 700;
                letter-spacing: -0.5px;
            }
            .header h2 { 
                margin: 8px 0 0 0; 
                font-size: 18px; 
                font-weight: 400;
                opacity: 0.9; 
            }

            .assets-grid { 
                display: grid; 
                grid-template-columns: 1fr 1fr; 
                gap: 0; 
            }

            .asset-section { 
                padding: 25px; 
            }
            .btc-section { 
                border-right: 2px solid #f0f0f0; 
            }

            .asset-header { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 20px; 
                padding-bottom: 12px; 
            }
            .btc-header { 
                border-bottom: 3px solid #f7931a; 
            }
            .mstr-header { 
                border-bottom: 3px solid #ff6b35; 
            }

            .asset-symbol { 
                font-size: 24px; 
                font-weight: 700;
            }
            .asset-price { 
                font-size: 24px; 
                font-weight: 700; 
            }
            .btc-price { 
                color: #f7931a; 
            }
            .mstr-price { 
                color: #ff6b35; 
            }

            .market-status { 
                font-size: 16px; 
                font-weight: 600;
                margin: 15px 0; 
                text-align: center; 
                padding: 12px; 
                border-radius: 8px; 
            }
            .bull-market { 
                background: linear-gradient(135deg, #d4edda, #c3e6cb); 
                color: #155724; 
            }
            .bear-market { 
                background: linear-gradient(135deg, #f8d7da, #f5c6cb); 
                color: #721c24; 
            }
            .overvalued { 
                background: linear-gradient(135deg, #f8d7da, #f5c6cb); 
                color: #721c24; 
            }
            .undervalued { 
                background: linear-gradient(135deg, #d4edda, #c3e6cb); 
                color: #155724; 
            }
            .neutral { 
                background: linear-gradient(135deg, #e2e3e5, #d6d8db); 
                color: #495057; 
            }

            .indicators { 
                margin: 20px 0; 
            }
            .indicators h3 {
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 12px 0;
                color: #333;
            }
            .indicator { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                padding: 8px 0; 
                border-bottom: 1px solid #eee; 
                font-size: 14px; 
            }
            .indicator:last-child { 
                border-bottom: none; 
            }
            .indicator-value { 
                font-weight: 600; 
                font-size: 14px;
            }

            .signal-box { 
                margin: 15px 0; 
                padding: 14px; 
                border-radius: 8px; 
                text-align: center; 
                border: 2px solid;
            }
            .signal-active { 
                background: linear-gradient(135deg, #d4edda, #c3e6cb); 
                border-color: #28a745; 
            }
            .signal-weakening { 
                background: linear-gradient(135deg, #fff3cd, #ffeaa7); 
                border-color: #ffc107; 
            }
            .signal-off { 
                background: linear-gradient(135deg, #f8f9fa, #e9ecef); 
                border-color: #6c757d; 
            }
            .sell-signal { 
                background: linear-gradient(135deg, #f8d7da, #f5c6cb); 
                border-color: #dc3545; 
            }
            .buy-signal { 
                background: linear-gradient(135deg, #d1ecf1, #bee5eb); 
                border-color: #17a2b8; 
            }
            .hold-signal { 
                background: linear-gradient(135deg, #e2e3e5, #d6d8db); 
                border-color: #6c757d; 
            }
            .premium-selling-signal {
                background: linear-gradient(135deg, #fff3cd, #ffeaa7); 
                border-color: #ffc107; 
            }

            .signal-title { 
                font-size: 15px; 
                font-weight: 600; 
                margin-bottom: 6px; 
            }
            .signal-subtitle { 
                font-size: 13px; 
                margin-bottom: 6px;
                opacity: 0.9; 
            }
            .explanation { 
                font-size: 12px; 
                margin-top: 6px; 
                opacity: 0.8; 
                line-height: 1.3;
            }

            .options-strategy {
                margin: 20px 0;
            }
            .options-strategy h3 {
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 12px 0;
                color: #333;
            }

            .laws-section-container {
                grid-column: 1 / -1;
                margin-top: 20px;
                padding: 0 25px 25px 25px;
            }

            .laws-section {
                background: #f8f9fa;
                border: 2px solid #6c757d;
                border-radius: 10px;
                padding: 20px;
            }

            .laws-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 18px;
                padding-bottom: 12px;
                border-bottom: 3px solid #007bff;
            }

            .project-footer { 
                grid-column: 1 / -1;
                margin-top: 30px; 
                padding: 15px 25px; 
                background: #f8f9fa; 
                border-top: 1px solid #dee2e6; 
                text-align: center; 
            }

            .project-links { 
                font-size: 11px; 
                color: #6c757d; 
                margin-top: 8px; 
            }

            .project-links a { 
                color: #007bff; 
                text-decoration: none; 
                margin: 0 8px; 
            }

            .project-description { 
                font-size: 10px; 
                color: #868e96; 
                margin-bottom: 5px; 
                font-style: italic; 
            }

            @media (max-width: 768px) {
                body {
                    padding: 10px;
                }
                .assets-grid { 
                    grid-template-columns: 1fr; 
                }
                .btc-section { 
                    border-right: none; 
                    border-bottom: 2px solid #f0f0f0; 
                }
                .asset-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 8px;
                }
                .asset-symbol, .asset-price {
                    font-size: 20px;
                }
                .header h1 {
                    font-size: 24px;
                }
            }

            /* Money Supply Section Styles */
            .monetary-section-container {
                grid-column: 1 / -1;
                margin-top: 20px;
                padding: 0 25px 25px 25px;
            }

            .monetary-section {
                background: #f8f9fa;
                border: 2px solid #28a745;
                border-radius: 10px;
                padding: 25px;
            }

            .monetary-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 3px solid #28a745;
            }

            .monetary-symbol {
                font-size: 24px;
                font-weight: 700;
                color: #333;
            }

            .monetary-date {
                font-size: 14px;
                color: #666;
                font-weight: 500;
            }

            .fixed-rates-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin-bottom: 25px;
            }

            .rate-card {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            .rate-label {
                font-size: 12px;
                color: #666;
                font-weight: 600;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .rate-value {
                font-size: 20px;
                font-weight: 700;
                color: #28a745;
                margin-bottom: 4px;
            }

            .rate-description {
                font-size: 11px;
                color: #888;
                font-style: italic;
            }

            .monetary-table-container {
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            .monetary-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }

            .monetary-table th {
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 12px 8px;
                text-align: center;
                font-weight: 600;
                font-size: 12px;
                border-right: 1px solid rgba(255,255,255,0.2);
            }

            .monetary-table th:first-child {
                text-align: left;
                padding-left: 15px;
            }

            .monetary-table td {
                padding: 10px 8px;
                text-align: center;
                border-bottom: 1px solid #f0f0f0;
                border-right: 1px solid #f0f0f0;
            }

            .monetary-table td:first-child {
                text-align: left;
                padding-left: 15px;
                font-weight: 600;
                color: #333;
            }

            .monetary-table tbody tr:hover {
                background-color: #f8f9fa;
            }

            .positive-change {
                color: #dc3545;
                font-weight: 600;
            }

            .negative-change {
                color: #28a745;
                font-weight: 600;
            }

            .neutral-change {
                color: #6c757d;
                font-weight: 600;
            }

            @media (max-width: 768px) {
                .fixed-rates-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }

            /* Pi Cycle Section Styles - MINIMAL styles to avoid conflicts */
            .pi-cycle-section-container {
                grid-column: 1 / -1;
                margin-top: 20px;
                padding: 0 25px 25px 25px;
            }

            .pi-cycle-section {
                background: #f8f9fa;
                border: 2px solid #6f42c1;
                border-radius: 10px;
                padding: 20px;
            }

            .pi-cycle-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 3px solid #6f42c1;
            }

            .pi-cycle-symbol {
                font-size: 20px;
                font-weight: 700;
                color: #333;
            }

            .pi-cycle-content {
                display: block;
            }

            @media (max-width: 768px) {
                .pi-cycle-section-container {
                    padding: 0 15px 15px 15px;
                }
            }
        """

    def _generate_enhanced_btc_section_html(self, btc_data: Dict) -> str:
        """Generate enhanced BTC section with unified styling and clear signals"""
        if 'error' in btc_data:
            return f"""
            <div class="asset-section btc-section">
                <div class="asset-header btc-header">
                    <span class="asset-symbol">₿ BTC</span>
                    <span style="color: #dc3545; font-weight: 600;">ERROR</span>
                </div>
                <p style="color: #dc3545; margin: 20px 0;">Error: {btc_data['error']}</p>
            </div>
            """

        # Analyze signals using BTCAnalyzer
        signal_analysis = self.btc_analyzer.analyze_btc_signals(btc_data)

        if 'error' in signal_analysis:
            return f"""
            <div class="asset-section btc-section">
                <div class="asset-header btc-header">
                    <span class="asset-symbol">₿ BTC</span>
                    <span style="color: #dc3545; font-weight: 600;">ANALYSIS ERROR</span>
                </div>
                <p style="color: #dc3545; margin: 20px 0;">Signal analysis error: {signal_analysis['error']}</p>
            </div>
            """

        # Extract analysis results
        price = signal_analysis['price']
        ema_200 = signal_analysis['ema_200']
        is_bull_market = signal_analysis['is_bull_market']
        market_status = "🐂 Bull Market" if is_bull_market else "🐻 Bear Market"
        indicators = signal_analysis['indicators']
        signal_conditions = signal_analysis['signal_conditions']

        # 🎯 NEW: Add mining cost data to signal analysis for signal boxes
        btc_indicators = btc_data.get('indicators', {})
        signal_analysis['indicators'] = {**indicators, **btc_indicators}  # Merge indicators

        return f"""
        <div class="asset-section btc-section">
            <div class="asset-header btc-header">
                <span class="asset-symbol">₿ BTC</span>
                <span class="asset-price btc-price">${price:,.2f}</span>
            </div>

            <div class="market-status {'bull-market' if is_bull_market else 'bear-market'}">
                {market_status}
            </div>

            <div class="indicators">
                <h3>📊 BTC Indicators</h3>
                {self._generate_btc_indicators_html(signal_analysis['indicators'], signal_conditions, ema_200, price)}
            </div>

            {self._generate_btc_signal_boxes_html(signal_analysis)}
        </div>
        """

    def _generate_btc_indicators_html(self, indicators: Dict, signal_conditions: Dict, ema_200: float,
                                      price: float) -> str:
        """Generate enhanced BTC indicators HTML with 2 decimal MVRV + Mining Cost"""
        mvrv_info = signal_conditions.get('mvrv', {})
        rsi_info = signal_conditions.get('rsi', {})

        # Status icons based on conditions
        mvrv_status = "✅" if mvrv_info.get('condition_met', False) else "❌"
        rsi_status = "✅" if rsi_info.get('condition_met', False) else "❌"

        # Price vs EMA percentage
        price_vs_ema_pct = ((price - ema_200) / ema_200 * 100) if ema_200 > 0 else 0
        ema_status = "🔴" if price_vs_ema_pct > 15 else "🟢" if price_vs_ema_pct < -15 else "🟡"

        # 🎯 UPDATED: Mining Cost indicators with new 1.0-4.0 range and traffic light colors
        mining_cost = indicators.get('mining_cost', 'N/A')
        mining_cost_date = indicators.get('mining_cost_date', 'N/A')
        price_cost_ratio = indicators.get('price_cost_ratio', 'N/A')

        # Format mining cost display
        if mining_cost != 'N/A':
            mining_cost_display = f"${mining_cost:,.0f}"
            if mining_cost_date != 'N/A':
                mining_cost_display += f" ({mining_cost_date})"
        else:
            mining_cost_display = "N/A"

        # 🎯 UPDATED: Format price/cost ratio with new traffic light system (1.0-4.0 range)
        if price_cost_ratio != 'N/A':
            ratio_value = float(price_cost_ratio)
            if ratio_value < 1.0:
                ratio_status = "🟢"  # Green - Below cost, buying opportunity
                ratio_display = f"{price_cost_ratio} {ratio_status} (Below Cost - Value Zone)"
            elif 1.0 <= ratio_value <= 4.0:
                ratio_status = "🟡"  # Yellow - Normal range
                ratio_display = f"{price_cost_ratio} {ratio_status} (Normal Range 1.0-4.0)"
            else:  # > 4.0
                ratio_status = "🔴"  # Red - High premium, sell signal
                ratio_display = f"{price_cost_ratio} {ratio_status} (High Premium - Consider Selling)"
        else:
            ratio_display = "N/A"

        return f"""
        <div class="indicator">
            <span>MVRV:</span>
            <span class="indicator-value">{mvrv_info.get('value', 2.1):.2f} {mvrv_status}</span>
        </div>
        <div class="indicator">
            <span>Weekly RSI:</span>
            <span class="indicator-value">{rsi_info.get('value', 65):.1f} {rsi_status}</span>
        </div>
        <div class="indicator">
            <span>EMA 200:</span>
            <span class="indicator-value">${ema_200:,.2f}</span>
        </div>
        <div class="indicator">
            <span>Price vs EMA:</span>
            <span class="indicator-value">{price_vs_ema_pct:+.1f}% {ema_status}</span>
        </div>
        <div class="indicator">
            <span>Average Mining Cost:</span>
            <span class="indicator-value">{mining_cost_display}</span>
        </div>
        <div class="indicator">
            <span>Price/Cost Ratio:</span>
            <span class="indicator-value">{ratio_display}</span>
        </div>
        """

    def _generate_btc_signal_boxes_html(self, signal_analysis: Dict) -> str:
        """Generate BTC signal boxes using actual signal analysis + mining cost signal"""
        signal_status = signal_analysis.get('signal_status', {})

        # Extract real BTC signal data
        status = signal_status.get('status', 'none')
        message = signal_status.get('message', '')
        emoji = signal_status.get('emoji', '🟡')
        prediction = signal_status.get('prediction', '')

        # Determine CSS class and display based on actual signal
        if status == 'active':
            if 'BUY' in message.upper():
                btc_signal_class = "buy-signal"
                btc_title = f"{emoji} BUY SIGNAL ACTIVE"
                btc_subtitle = "Strong Buy Conditions Met"
            elif 'SELL' in message.upper():
                btc_signal_class = "sell-signal"
                btc_title = f"{emoji} SELL SIGNAL ACTIVE"
                btc_subtitle = "Strong Sell Conditions Met"
            else:
                btc_signal_class = "signal-active"
                btc_title = f"{emoji} {message}"
                btc_subtitle = "Signal Active"
        elif status == 'weakening':
            btc_signal_class = "signal-weakening"
            btc_title = f"{emoji} SIGNAL WEAKENING"
            btc_subtitle = "Conditions Deteriorating"
        elif status == 'recently_off':
            btc_signal_class = "signal-off"
            btc_title = f"{emoji} SIGNAL RECENTLY OFF"
            btc_subtitle = "Signal Ended"
        else:  # status == 'none'
            btc_signal_class = "hold-signal"
            btc_title = "🟡 HOLD SIGNAL"
            btc_subtitle = "Monitor Position"
            prediction = "Market trending but conditions not extreme yet"

        # 🎯 UPDATED: Mining cost signal with new traffic light system (1.0-4.0 range)
        indicators = signal_analysis.get('indicators', {})
        price_cost_ratio = indicators.get('price_cost_ratio', 'N/A')

        mining_cost_signal = ""
        if price_cost_ratio != 'N/A':
            ratio_value = float(price_cost_ratio)
            if ratio_value < 1.0:
                signal_class_mining = "buy-signal"
                signal_text = f"🟢 Below Production Cost - Strong Value Opportunity"
            elif 1.0 <= ratio_value <= 4.0:
                signal_class_mining = "hold-signal"
                signal_text = f"🟡 Normal Mining Premium (1.0-4.0x Cost)"
            else:  # > 4.0
                signal_class_mining = "sell-signal"
                signal_text = f"🔴 High Premium Above Normal Range - Consider Profit Taking"

            mining_cost_signal = f"""
            <div class="signal-box {signal_class_mining}" style="margin-top: 10px;">
                <div class="signal-title" style="font-size: 14px;">{signal_text}</div>
            </div>
            """

        return f"""
        <div class="signal-box {btc_signal_class}">
            <div class="signal-title">{btc_title}</div>
            <div class="signal-subtitle">{btc_subtitle}</div>
            <div class="explanation">{prediction}</div>
        </div>
        {mining_cost_signal}
        """

    def _generate_enhanced_mstr_section_html(self, mstr_data: Dict) -> str:
        """🎯 ENHANCED: Generate complete MSTR section with NEW METRICS + options strategy"""
        if 'error' in mstr_data:
            return f"""
            <div class="asset-section mstr-section">
                <div class="asset-header mstr-header">
                    <span class="asset-symbol">📊 MSTR</span>
                    <span style="color: #dc3545; font-weight: 600;">ERROR</span>
                </div>
                <p style="color: #dc3545; margin: 20px 0;">Error: {mstr_data['error']}</p>
            </div>
            """

        # Extract MSTR data
        price = mstr_data.get('price', 0)
        indicators = mstr_data.get('indicators', {})
        analysis = mstr_data.get('analysis', {})

        # Get model price and deviation
        model_price = indicators.get('model_price', 0)
        deviation_pct = indicators.get('deviation_pct', 0)

        # Determine status
        if deviation_pct >= 25:
            status_class = "overvalued"
            status_text = "🔴 SEVERELY OVERVALUED"
        elif deviation_pct >= 15:
            status_class = "overvalued"
            status_text = "🟠 OVERVALUED"
        elif deviation_pct <= -25:
            status_class = "undervalued"
            status_text = "🟢 SEVERELY UNDERVALUED"
        elif deviation_pct <= -15:
            status_class = "undervalued"
            status_text = "🟢 UNDERVALUED"
        else:
            status_class = "neutral"
            status_text = "🟡 FAIR VALUED"

        return f"""
        <div class="asset-section mstr-section">
            <div class="asset-header mstr-header">
                <span class="asset-symbol">📊 MSTR</span>
                <span class="asset-price mstr-price">${price:,.2f}</span>
            </div>

            <div class="market-status {status_class}">
                {status_text} ({deviation_pct:+.1f}%)
            </div>

            <div class="indicators">
                <h3>📈 MSTR Indicators</h3>
                {self._generate_enhanced_mstr_indicators_html(indicators)}
            </div>

            {self._generate_mstr_signals_html(analysis)}

            {self._generate_mstr_footnotes_html()}
        </div>
        """

    def _generate_enhanced_mstr_indicators_html(self, indicators: Dict) -> str:
        """🎯 ENHANCED: Generate MSTR indicators section HTML with NEW METRICS"""
        model_price = indicators.get('model_price', 0)
        deviation_pct = indicators.get('deviation_pct', 0)
        iv = indicators.get('iv', 0)
        iv_percentile = indicators.get('iv_percentile', 0)
        iv_rank = indicators.get('iv_rank', 0)

        # 🎯 NEW: Extract new metrics
        rank = indicators.get('rank', 'N/A')
        mnav = indicators.get('mnav', 'N/A')
        # --- MODIFICATION ---
        pref_nav_ratio = indicators.get('pref_nav_ratio', 'N/A')
        debt_nav_ratio = indicators.get('debt_nav_ratio', 'N/A')
        # --- END MODIFICATION ---
        bitcoin_count = indicators.get('bitcoin_count', 'N/A')
        btc_stress_price = indicators.get('btc_stress_price', 'N/A')

        # 🎯 NEW: Format display values
        rank_display = f"{rank}" if rank != 'N/A' else "N/A"
        mnav_display = f"{mnav}" if mnav != 'N/A' else "N/A"
        # --- MODIFICATION ---
        pref_nav_display = f"{pref_nav_ratio:.0f}%" if pref_nav_ratio != 'N/A' else "N/A"
        debt_nav_display = f"{debt_nav_ratio:.0f}%" if debt_nav_ratio != 'N/A' else "N/A"
        # --- END MODIFICATION ---
        bitcoin_display = f"{bitcoin_count:,.0f} " if bitcoin_count != 'N/A' else "N/A BTC"
        stress_display = f"${btc_stress_price:,.0f}" if btc_stress_price != 'N/A' else "N/A"

        return f"""
        <div class="indicator">
            <span>Model Price:</span>
            <span class="indicator-value">${model_price:,.2f}</span>
        </div>
        <div class="indicator">
            <span>Deviation:</span>
            <span class="indicator-value">{deviation_pct:+.1f}%</span>
        </div>
        <div class="indicator">
            <span>Market Cap Rank:</span>
            <span class="indicator-value">{rank_display}</span>
        </div>
        <div class="indicator">
            <span>mNAV Ratio:</span>
            <span class="indicator-value">{mnav_display}</span>
        </div>
        <div class="indicator">
            <span>Pref/Bitcoin NAV:</span>
            <span class="indicator-value">{pref_nav_display}</span>
        </div>
        <div class="indicator">
            <span>Debt/Bitcoin NAV:</span>
            <span class="indicator-value">{debt_nav_display}</span>
        </div>
        <div class="indicator">
            <span>BTC Stress Price:</span>
            <span class="indicator-value">{stress_display}</span>
        </div>
        <div class="indicator">
            <span>Bitcoin Holdings:</span>
            <span class="indicator-value">{bitcoin_display}</span>
        </div>
        <div class="indicator">
            <span>Implied Volatility:</span>
            <span class="indicator-value">{iv:.1f}%</span>
        </div>
        <div class="indicator">
            <span>IV Percentile:</span>
            <span class="indicator-value">{iv_percentile:.1f}%</span>
        </div>
        <div class="indicator">
             <span>IV Rank:</span>
            <span class="indicator-value">{iv_rank:.1f}%</span>
        </div>
        """

    def _generate_mstr_signals_html(self, analysis: Dict) -> str:
        """Generate MSTR signals HTML INCLUDING options strategy"""
        if not analysis:
            return ""

        html = ""

        # Price Signal
        price_signal = analysis.get('price_signal', {})
        if price_signal:
            status = price_signal.get('status', 'neutral')
            signal = price_signal.get('signal', 'HOLD')
            message = price_signal.get('message', '')

            if status == 'overvalued':
                signal_class = "signal-box sell-signal"
                emoji = "🔴"
            elif status == 'undervalued':
                signal_class = "signal-box buy-signal"
                emoji = "🟢"
            else:
                signal_class = "signal-box hold-signal"
                emoji = "🟡"

            html += f"""
            <div class="{signal_class}">
                <div class="signal-title">{emoji} {signal} SIGNAL</div>
                <div class="signal-subtitle">{message}</div>
            </div>
            """

        # Options Strategy
        options_strategy = analysis.get('options_strategy', {})
        if options_strategy:
            strategy = options_strategy.get('primary_strategy', 'no_preference')
            message = options_strategy.get('message', 'No Options Preference')
            description = options_strategy.get('description', '')
            reasoning = options_strategy.get('reasoning', '')
            confidence = options_strategy.get('confidence', 'medium')

            # Determine CSS class and emoji based on strategy
            if strategy in ['long_calls', 'moderate_bullish']:
                strategy_class = "signal-box buy-signal"
                emoji = "🟢"
            elif strategy in ['long_puts', 'moderate_bearish']:
                strategy_class = "signal-box sell-signal"
                emoji = "🔴"
            elif strategy == 'long_straddle':
                strategy_class = "signal-box hold-signal"
                emoji = "🟡"
            elif strategy in ['short_puts', 'short_calls', 'short_strangle']:
                strategy_class = "signal-box premium-selling-signal"
                emoji = "📊"
            elif strategy == 'wait':
                strategy_class = "signal-box signal-weakening"
                emoji = "⚠️"
            else:
                strategy_class = "signal-box hold-signal"
                emoji = "🟫"

            html += f"""
            <div class="options-strategy">
                <h3>🎯 Options Strategy</h3>

                <div class="{strategy_class}">
                    <div class="signal-title">{emoji} {message}</div>
                    <div class="signal-subtitle">{description}</div>
                    <div class="explanation">{reasoning}</div>
                </div>

                <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 12px; margin-top: 10px;">
                    <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px; color: #333;">💡 Strategy Details:</div>
                    <div style="font-size: 12px; color: #555; line-height: 1.4;">
                        <strong>Reasoning:</strong> {reasoning}<br>
                        <strong>Confidence:</strong> {confidence.title()}
                    </div>
                </div>
            </div>
            """

        return html

    def _generate_mstr_footnotes_html(self) -> str:
        """🎯 NEW: Generate MSTR footnotes explaining new metrics"""
        return f"""
        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
            <div style="font-size: 12px; color: #666; line-height: 1.4;">
                <strong>📊 Metric Explanations:</strong><br>
                • <strong>BTC Stress Price:</strong> The Bitcoin price level that would create significant stress for MSTR based on debt obligations.<br>
                • <strong>mNAV:</strong> Market NAV (Net Asset Value) ratio - MSTR's market value vs Bitcoin holdings value.<br>
                • <strong>Debt/Pref NAV Ratios:</strong> Total debt and preferred stock shown individually as a percentage of Bitcoin NAV.
                </div>
            <p style="margin: 10px 0 0 0; font-size: 11px; color: #666;">
                📊 <a href="https://microstrategist.com/ballistic.html" target="_blank" style="color: #ff6b35; text-decoration: none; font-weight: 600;">
                    View MSTR Ballistic Model
                </a> | 
                <a href="https://www.strategy.com/" target="_blank" style="color: #ff6b35; text-decoration: none; font-weight: 600;">
                    Strategy.com Metrics
                </a>
            </p>
        </div>
        """

    def _generate_bitcoin_laws_section_html_url(self, image_url: str) -> str:
        """Generate Bitcoin Laws section HTML with external image URL"""
        if not image_url:
            return """
            <div class="asset-section laws-section">
                <div class="asset-header laws-header">
                    <span class="asset-symbol">⚖️ Bitcoin Laws</span>
                </div>
                <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #ddd;">
                    <div style="color: #555; font-size: 14px; margin-bottom: 12px; line-height: 1.4;">
                        📋 Tracking Bitcoin strategic reserve legislation across all 50 US states.
                    </div>
                    <p>🔗 <a href="https://bitcoinlaws.io" target="_blank" style="color: #007bff; text-decoration: none; font-weight: 600;">
                        Visit bitcoinlaws.io for latest Bitcoin policy developments →
                    </a></p>
                </div>
            </div>
            """

        return f"""
        <div class="laws-section">
            <div class="laws-header">
                <span class="laws-symbol">⚖️ Bitcoin Laws in USA</span>
                <span style="color: #666; font-size: 13px;">Legislative Tracker</span>
            </div>
            <div style="padding: 15px; background: white; border-radius: 8px;">
                <div style="color: #555; font-size: 14px; margin-bottom: 12px;">
                    📋 State-by-state Bitcoin strategic reserve bill progress and legislative developments.
                </div>
                <p>🔗 <a href="https://bitcoinlaws.io" target="_blank" style="color: #007bff;">
                    Visit bitcoinlaws.io for full details →
                </a></p>
            </div>
        </div>
        """

    def _generate_bitcoin_laws_section_html(self, screenshot_base64: str) -> str:
        """Generate Bitcoin Laws section HTML with embedded image"""
        if not screenshot_base64:
            return """
            <div class="asset-section laws-section">
                <div class="asset-header laws-header">
                    <span class="asset-symbol">⚖️ Bitcoin Laws</span>
                </div>
                <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #ddd;">
                    <div style="color: #555; font-size: 14px; margin-bottom: 12px; line-height: 1.4;">
                        📋 Tracking Bitcoin strategic reserve legislation across all 50 US states.
                    </div>
                    <p>🔗 <a href="https://bitcoinlaws.io" target="_blank" style="color: #007bff; text-decoration: none; font-weight: 600;">
                        Visit bitcoinlaws.io for latest developments →
                    </a></p>
                </div>
            </div>
            """

        return f"""
        <div class="laws-section">
            <div class="laws-header">
                <span class="laws-symbol">⚖️ Bitcoin Laws in USA</span>
                <span style="color: #666; font-size: 13px;">Legislative Tracker</span>
            </div>
            <div style="padding: 15px; background: white; border-radius: 8px;">
                <div style="color: #555; font-size: 14px; margin-bottom: 12px;">
                    📋 State-by-state Bitcoin strategic reserve bill progress and legislative developments.
                </div>
                <p>🔗 <a href="https://bitcoinlaws.io" target="_blank" style="color: #007bff;">
                    Visit bitcoinlaws.io for full details →
                </a></p>
            </div>
        </div>
        """

    def _generate_project_footer_html(self) -> str:
        """Generate project links footer"""
        return """
        <div class="project-footer">
            <div class="project-description">
                Learn more about this automated Bitcoin market intelligence system
            </div>
            <div class="project-links">
                <a href="https://github.com/danielluimkuk/dan_btc_report_gen/blob/main/README.md" target="_blank">
                    📖 About This Project (English)
                </a>
                |
                <a href="https://github.com/danielluimkuk/dan_btc_report_gen/blob/main/README_TRAD_CHI.md" target="_blank">
                    📖 關於此項目 (繁體中文)
                </a>
            </div>
        </div>
        """

    def _generate_error_report_html(self, report_date: str, error: str) -> str:
        """Generate error report HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                {self._get_email_css()}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Dan's Market Report</h1>
                    <h2>📅 {report_date}</h2>
                </div>
                <div style="padding: 30px; text-align: center;">
                    <div style="background: #f8d7da; border: 2px solid #dc3545; padding: 20px; border-radius: 10px;">
                        <h3>⚠️ Data Collection Error</h3>
                        <p>{error}</p>
                        <p>Please check the system logs for more details.</p>
                    </div>
                </div>
                {self._generate_project_footer_html()}
            </div>
        </body>
        </html>
        """

    def send_error_notification(self, error_message: str) -> None:
        """Send error notification to EMAIL_USER only (not all recipients)"""
        try:
            subject = "⚠️ Market Monitor Error"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="background: #f8d7da; border: 1px solid #dc3545; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #721c24;">Market Monitor Error</h2>
                    <p>An error occurred in Dan's market monitoring function:</p>
                    <pre style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; white-space: pre-wrap;">
    {error_message}
                    </pre>
                    <p>Please check the Azure Function logs for more details.</p>
                    <p style="font-size: 12px; color: #666; margin-top: 20px;">
                        📧 This error notification was sent to administrator only. 
                        Regular market reports will resume once the issue is resolved.
                    </p>
                </div>
            </body>
            </html>
            """

            # 🎯 MINIMAL CHANGE: Send only to EMAIL_USER instead of all recipients
            self._send_error_email_to_admin_only(subject, body)
            logging.info(f'Error notification sent to admin only: {self.email_user}')

        except Exception as e:
            logging.error(f'Failed to send error notification: {str(e)}')

    # Add this NEW method to your enhanced_notification_handler.py file:

    def _send_error_email_to_admin_only(self, subject: str, body: str) -> None:
        """Send email to EMAIL_USER only (for error notifications)"""
        if not all([self.email_user, self.email_password]):
            logging.warning('Email credentials not configured')
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['Subject'] = subject
            msg['To'] = self.email_user  # Only send to yourself

            msg.attach(MIMEText(body, 'html'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg, to_addrs=[self.email_user])  # Only to yourself
            server.quit()

            logging.info(f"Error notification sent successfully to admin: {self.email_user}")

        except Exception as e:
            logging.error(f"Failed to send error notification to admin: {str(e)}")
            raise

    def _send_email_to_multiple(self, subject: str, body: str, is_html: bool = False) -> None:
        """Send email to multiple recipients efficiently"""
        if not all([self.email_user, self.email_password]):
            logging.warning('Email credentials not configured')
            return

        if not self.recipients:
            logging.warning('No email recipients configured')
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['Subject'] = subject

            # Add recipients to BCC for privacy
            msg['To'] = self.email_user
            msg['Bcc'] = ', '.join(self.recipients)

            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)

            all_recipients = [self.email_user] + self.recipients
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()

            logging.info(f"Email sent successfully to {len(self.recipients)} recipients")

        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise
