"""
Streamlit UI for Frame Analysis System
Matches PRD requirements for UI components
"""

import streamlit as st
import requests
import time
import json
from datetime import datetime
import base64

# API Configuration
API_BASE_URL = st.secrets.get("API_URL", "https://your-api.onrender.com")

# Page config
st.set_page_config(
    page_title="Frame Analysis System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .finding-high {
        background-color: #fee2e2;
        border-left: 4px solid #dc2626;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.375rem;
    }
    .finding-medium {
        background-color: #fed7aa;
        border-left: 4px solid #ea580c;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.375rem;
    }
    .finding-low {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.375rem;
    }
    .metric-card {
        background-color: #f3f4f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .warning-banner {
        background-color: #fffbeb;
        border: 1px solid #fcd34d;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

# Header
st.markdown('<div class="main-header">🎬 Frame Analysis System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Detect temporal anomalies in videos and image sequences</div>', unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Media Type Selection
    media_type = st.radio(
        "Media Type",
        ["Video", "Image Sequence"],
        help="Select the type of media to analyze"
    )
    
    # Analysis Mode
    analysis_mode = st.selectbox(
        "Analysis Mode",
        ["standard", "high_sensitivity", "deep_scan"],
        format_func=lambda x: {
            "standard": "Standard (Default)",
            "high_sensitivity": "High Sensitivity",
            "deep_scan": "Deep Scan"
        }[x]
    )
    
    if media_type == "Video":
        # Sampling Mode
        sampling_mode = st.selectbox(
            "Sampling Mode",
            ["sampled", "full"],
            format_func=lambda x: "Sampled (2-5 fps)" if x == "sampled" else "Full Scan (All Frames)"
        )
    else:
        # Sequence Type
        sequence_type = st.selectbox(
            "Sequence Type",
            ["ordered", "unordered"],
            format_func=lambda x: "Ordered Sequence" if x == "ordered" else "Unordered Batch"
        )
    
    st.divider()
    
    # API Status
    st.subheader("🔌 API Status")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline")

# Main content area
tab1, tab2 = st.tabs(["📤 Upload & Analyze", "📊 Results"])

with tab1:
    st.header("Upload Media")
    
    if media_type == "Video":
        # Video upload
        uploaded_file = st.file_uploader(
            "Upload Video File",
            type=["mp4", "mov"],
            help="Maximum file size: 500MB"
        )
        
        if uploaded_file:
            st.video(uploaded_file)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📹 **{uploaded_file.name}** - {uploaded_file.size / 1024 / 1024:.2f} MB")
            with col2:
                if st.button("🚀 Analyze Video", type="primary", use_container_width=True):
                    with st.spinner("Uploading and analyzing..."):
                        try:
                            # Upload video
                            files = {'video': uploaded_file.getvalue()}
                            data = {
                                'mode': analysis_mode,
                                'sampling_mode': sampling_mode
                            }
                            
                            response = requests.post(
                                f"{API_BASE_URL}/api/analyze/video",
                                files=files,
                                data=data,
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.session_state.job_id = result['job_id']
                                st.success(f"✅ Analysis started! Job ID: {result['job_id'][:8]}...")
                                
                                # Poll for results
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                max_attempts = 150
                                for attempt in range(max_attempts):
                                    status_response = requests.get(
                                        f"{API_BASE_URL}/api/job/{st.session_state.job_id}",
                                        timeout=5
                                    )
                                    
                                    if status_response.status_code == 200:
                                        status_data = status_response.json()
                                        
                                        if status_data['status'] == 'completed':
                                            progress_bar.progress(100)
                                            status_text.success("✅ Analysis complete!")
                                            
                                            # Get results
                                            results_response = requests.get(
                                                f"{API_BASE_URL}/api/result/{st.session_state.job_id}",
                                                timeout=5
                                            )
                                            
                                            if results_response.status_code == 200:
                                                st.session_state.results = results_response.json()
                                                st.session_state.analysis_complete = True
                                                st.rerun()
                                            break
                                        
                                        elif status_data['status'] == 'failed':
                                            st.error(f"❌ Analysis failed: {status_data.get('error', 'Unknown error')}")
                                            break
                                        
                                        else:
                                            # Still processing
                                            progress = min((attempt / max_attempts) * 100, 95)
                                            progress_bar.progress(int(progress))
                                            status_text.info(f"⏳ Processing... ({attempt * 2}s elapsed)")
                                            time.sleep(2)
                                    
                                    else:
                                        st.error("Failed to check status")
                                        break
                            else:
                                st.error(f"Upload failed: {response.status_code}")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
    else:
        # Image sequence upload
        uploaded_files = st.file_uploader(
            "Upload Images (minimum 2)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload at least 2 images for sequence analysis"
        )
        
        if uploaded_files:
            st.info(f"📸 {len(uploaded_files)} images uploaded")
            
            # Show thumbnails
            cols = st.columns(min(len(uploaded_files), 5))
            for idx, (col, img_file) in enumerate(zip(cols, uploaded_files[:5])):
                with col:
                    st.image(img_file, caption=img_file.name, use_container_width=True)
            
            if len(uploaded_files) > 5:
                st.caption(f"... and {len(uploaded_files) - 5} more images")
            
            if len(uploaded_files) < 2:
                st.warning("⚠️ Please upload at least 2 images for sequence analysis")
            else:
                if st.button("🚀 Analyze Images", type="primary", use_container_width=True):
                    with st.spinner("Uploading and analyzing..."):
                        try:
                            # Upload images
                            files = [('images', img.getvalue()) for img in uploaded_files]
                            data = {
                                'sequence_type': sequence_type,
                                'mode': analysis_mode
                            }
                            
                            response = requests.post(
                                f"{API_BASE_URL}/api/analyze/images",
                                files=files,
                                data=data,
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.session_state.job_id = result['job_id']
                                st.success(f"✅ Analysis started! Job ID: {result['job_id'][:8]}...")
                                
                                # Poll for results (same as video)
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                max_attempts = 150
                                for attempt in range(max_attempts):
                                    status_response = requests.get(
                                        f"{API_BASE_URL}/api/job/{st.session_state.job_id}"
                                    )
                                    
                                    if status_response.status_code == 200:
                                        status_data = status_response.json()
                                        
                                        if status_data['status'] == 'completed':
                                            progress_bar.progress(100)
                                            status_text.success("✅ Analysis complete!")
                                            
                                            results_response = requests.get(
                                                f"{API_BASE_URL}/api/result/{st.session_state.job_id}"
                                            )
                                            
                                            if results_response.status_code == 200:
                                                st.session_state.results = results_response.json()
                                                st.session_state.analysis_complete = True
                                                st.rerun()
                                            break
                                        
                                        elif status_data['status'] == 'failed':
                                            st.error(f"❌ Analysis failed: {status_data.get('error', 'Unknown error')}")
                                            break
                                        
                                        else:
                                            progress = min((attempt / max_attempts) * 100, 95)
                                            progress_bar.progress(int(progress))
                                            status_text.info(f"⏳ Processing... ({attempt * 2}s elapsed)")
                                            time.sleep(2)
                            else:
                                st.error(f"Upload failed: {response.status_code}")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

with tab2:
    if st.session_state.results:
        results = st.session_state.results
        
        # Warning Banner
        st.markdown("""
        <div class="warning-banner">
            <strong>⚠️ Important Notice</strong><br>
            Findings represent anomaly signals, not proof of manipulation. 
            Platform recompression may affect results.
        </div>
        """, unsafe_allow_html=True)
        
        # Media Information
        st.header("📊 Media Information")
        
        media_info = results.get('media_info', {})
        cols = st.columns(4)
        
        for idx, (key, value) in enumerate(media_info.items()):
            with cols[idx % 4]:
                st.metric(
                    label=key.replace('_', ' ').title(),
                    value=value
                )
        
        st.divider()
        
        # Timeline/Sequence Bar
        findings = results.get('findings', [])
        
        if findings:
            st.header("📈 Timeline Overview")
            
            # Create timeline visualization
            timeline_data = []
            for finding in findings:
                severity = str(finding.get('severity', '')).lower()
                if 'high' in severity:
                    color = '#dc2626'
                elif 'medium' in severity:
                    color = '#ea580c'
                else:
                    color = '#f59e0b'
                
                location = finding.get('location', {})
                start = location.get('start', 0)
                end = location.get('end', 0)
                
                timeline_data.append({
                    'start': start,
                    'end': end,
                    'color': color,
                    'type': finding.get('type', 'Unknown')
                })
            
            # Simple timeline representation
            st.write("**Anomaly Distribution:**")
            severity_counts = {
                'High': len([f for f in findings if 'high' in str(f.get('severity', '')).lower()]),
                'Medium': len([f for f in findings if 'medium' in str(f.get('severity', '')).lower()]),
                'Low': len([f for f in findings if 'low' in str(f.get('severity', '')).lower()])
            }
            
            cols = st.columns(3)
            with cols[0]:
                st.metric("🔴 High Severity", severity_counts['High'])
            with cols[1]:
                st.metric("🟠 Medium Severity", severity_counts['Medium'])
            with cols[2]:
                st.metric("🟡 Low Severity", severity_counts['Low'])
            
            st.divider()
            
            # Findings List
            st.header(f"🔍 Findings ({len(findings)})")
            
            # Filter options
            severity_filter = st.multiselect(
                "Filter by Severity",
                ["High", "Medium", "Low"],
                default=["High", "Medium", "Low"]
            )
            
            # Group by severity
            high_findings = [f for f in findings if 'high' in str(f.get('severity', '')).lower()]
            medium_findings = [f for f in findings if 'medium' in str(f.get('severity', '')).lower()]
            low_findings = [f for f in findings if 'low' in str(f.get('severity', '')).lower()]
            
            # Display High Severity
            if "High" in severity_filter and high_findings:
                st.subheader("🔴 High Severity Findings")
                for finding in high_findings:
                    display_finding(finding, "high")
            
            # Display Medium Severity
            if "Medium" in severity_filter and medium_findings:
                st.subheader("🟠 Medium Severity Findings")
                for finding in medium_findings:
                    display_finding(finding, "medium")
            
            # Display Low Severity
            if "Low" in severity_filter and low_findings:
                st.subheader("🟡 Low Severity Findings")
                for finding in low_findings:
                    display_finding(finding, "low")
            
            st.divider()
            
            # Export Options
            st.header("💾 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # JSON Export
                json_str = json.dumps(results, indent=2, default=str)
                st.download_button(
                    label="📄 Download JSON",
                    data=json_str,
                    file_name=f"frame-analysis-{st.session_state.job_id[:8]}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # PDF Export
                if st.button("📑 Download PDF", use_container_width=True):
                    try:
                        pdf_response = requests.get(
                            f"{API_BASE_URL}/api/export/pdf/{st.session_state.job_id}",
                            timeout=30
                        )
                        
                        if pdf_response.status_code == 200:
                            st.download_button(
                                label="💾 Save PDF Report",
                                data=pdf_response.content,
                                file_name=f"frame-analysis-report-{st.session_state.job_id[:8]}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.error("PDF generation failed")
                    except Exception as e:
                        st.error(f"Error downloading PDF: {str(e)}")
        
        else:
            st.success("✅ No anomalies detected - media appears consistent")
    
    else:
        st.info("👆 Upload and analyze media in the 'Upload & Analyze' tab to see results here")

# Helper function to display findings
def display_finding(finding, severity):
    """Display a single finding with metrics"""
    finding_type = finding.get('type', 'Unknown').replace('FindingType.', '').replace('_', ' ')
    location = finding.get('location', {})
    explanation = finding.get('explanation', '')
    metrics = finding.get('metrics', {})
    
    # Format location
    if 'start' in location and 'end' in location:
        loc_str = f"{location['start']:.2f}s - {location['end']:.2f}s"
    elif 'frames' in location:
        frames = location['frames']
        loc_str = f"Frames: {', '.join(map(str, frames[:5]))}"
        if len(frames) > 5:
            loc_str += f"... ({len(frames)} total)"
    else:
        loc_str = "N/A"
    
    # Display finding card
    st.markdown(f"""
    <div class="finding-{severity}">
        <strong>{finding_type}</strong> - {loc_str}<br>
        <small>{explanation}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics in expander
    if metrics:
        with st.expander("📊 View Metrics"):
            metric_cols = st.columns(3)
            for idx, (key, value) in enumerate(metrics.items()):
                with metric_cols[idx % 3]:
                    formatted_key = key.replace('_', ' ').title()
                    if isinstance(value, float):
                        st.metric(formatted_key, f"{value:.4f}")
                    else:
                        st.metric(formatted_key, value)

# Footer
st.divider()
st.caption("🎬 Frame Analysis System | Powered by Advanced Computer Vision")
