import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageFont
from rembg import remove, new_session
import requests
from io import BytesIO
import os
import base64

st.set_page_config(page_title="Data Vidwan Independence Day Portrait")

MAIN_BG_URL = "https://i.ibb.co/wrgwQByv/Whats-App-Image-2026-08-13-at-4-22-52-PM.jpg"

# --- Background Image Setup ---
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_image = get_base64_image("assets/independence_bg.png")
logo_base64 = get_base64_image("assets/logo.png")

@st.cache_resource(show_spinner="Downloading/verifying background-removal model...")
def load_rembg_session():
    # Make sure we use a writeable directory in the cloud
    os.environ["U2NET_HOME"] = os.path.expanduser("~/.u2net")
    return new_session("u2net")

session = load_rembg_session()

def process_independence_day_avatar_v2(user_img):
    if user_img is None:
        return None

    # Canvas (1080x1350)
    canvas_w, canvas_h = 1080, 1350
    final_canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))

    def load_image_from_url(url, size=None):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=10)
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
            if size:
                img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            print(f"Error loading {url}: {e}")
            if size:
                return Image.new("RGBA", size, (245, 245, 245, 255))
            return None

    def make_white_transparent(img):
        if img is None:
            return None
        img = img.convert("RGBA")
        data = img.getdata()
        new_data = []
        for item in data:
            if item[0] > 180 and item[1] > 180 and item[2] > 180:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)
        return img

    orig_pil = Image.fromarray(user_img).convert("RGBA")
    cutout = remove(orig_pil, session=session)

    r, g, b, alpha = cutout.split()
    alpha_refined = alpha.filter(ImageFilter.GaussianBlur(radius=1.5))
    cutout.putalpha(alpha_refined)

    main_bg = load_image_from_url(MAIN_BG_URL, (canvas_w, canvas_h))

    bg_blurred = main_bg.filter(ImageFilter.GaussianBlur(radius=2.7))
    final_canvas.paste(bg_blurred, (0, 0))

    gradient = Image.new("RGBA", (canvas_w, canvas_h))
    draw_g = ImageDraw.Draw(gradient)
    draw_g.rectangle([0, 0, canvas_w, int(canvas_h*0.33)], fill=(255, 153, 51, 70))
    draw_g.rectangle([0, int(canvas_h*0.33), canvas_w, int(canvas_h*0.66)], fill=(255, 255, 255, 30))
    draw_g.rectangle([0, int(canvas_h*0.66), canvas_w, canvas_h], fill=(19, 136, 8, 70))
    gradient = gradient.filter(ImageFilter.GaussianBlur(radius=25))
    final_canvas.paste(gradient, (0, 0), gradient)

    bbox = cutout.getbbox()
    if bbox:
        cutout = cutout.crop(bbox)

    aspect = cutout.width / cutout.height
    target_h = int(canvas_h * 0.55)
    target_w = int(target_h * aspect)

    cutout_scaled = cutout.resize((target_w, target_h), Image.Resampling.LANCZOS)

    glow_size = 0
    glow_alpha = Image.new("L", (target_w + glow_size * 2, target_h + glow_size * 2), 0)
    glow_mask = cutout_scaled.split()[3].filter(ImageFilter.GaussianBlur(radius=0))
    glow_alpha.paste(glow_mask, (glow_size, glow_size))
    glow_color = Image.new("RGBA", (target_w + glow_size * 2, target_h + glow_size * 2), (255, 255, 255, 35))
    glow_color.putalpha(glow_alpha)
    
    paste_x = (canvas_w - target_w) // 2
    paste_y = canvas_h - target_h

    final_canvas.paste(glow_color, (paste_x - glow_size, paste_y - glow_size), glow_color)
    final_canvas.paste(cutout_scaled, (paste_x, paste_y), cutout_scaled)

    logo_url = "https://i.ibb.co/dwQt56Cf/DV-Logo.png"
    logo_img = load_image_from_url(logo_url)

    if logo_img:
        transparent_logo = make_white_transparent(logo_img)
        bbox_logo = transparent_logo.getbbox()
        if bbox_logo:
            transparent_logo = transparent_logo.crop(bbox_logo)

        target_logo_w = 180
        logo_aspect = transparent_logo.height / transparent_logo.width
        target_logo_h = int(target_logo_w * logo_aspect)
        resized_logo = transparent_logo.resize((target_logo_w, target_logo_h), Image.Resampling.LANCZOS)

        padding_x = 20
        padding_y = 20
        logo_x = canvas_w - target_logo_w - padding_x
        logo_y = canvas_h - target_logo_h - padding_y

        final_canvas.paste(resized_logo, (logo_x, logo_y), resized_logo)

    return final_canvas.convert("RGB")

# Custom CSS for styling + Independence Day background
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

    /* Independence Day Background */
    .stApp {{
        background-image: url("data:image/png;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Make Streamlit containers transparent */
    [data-testid="stAppViewContainer"] {{
        background: transparent;
    }}
    [data-testid="stHeader"] {{
        background: transparent;
    }}
    [data-testid="stMain"] {{
        background: transparent;
    }}

    /* Title container centering */
    .title-container {{
        text-align: center;
        margin-top: 1rem;
    }}
    
    .logo-img {{
        height: 100px;
        margin-bottom: 10px;
    }}

    .main-heading {{
        font-family: 'Dancing Script', cursive;
        font-size: 4.5rem !important;
        margin-bottom: 0rem;
        line-height: 1.2;
    }}
    
    .saffron {{ color: #FF9933; }}
    .green {{ color: #138808; }}

    .sub-heading {{
        color: #4A4A4A;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }}

    /* =========================================
       PERFECT CUSTOM UPLOADER UI
       ========================================= */

    /* Hide the default Streamlit label */
    [data-testid="stWidgetLabel"] {{
        display: none !important;
    }}

    /* Style our custom HTML container */
    .custom-upload-container {{
        background-color: white;
        border-radius: 24px;
        padding: 12px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        max-width: 550px;
        margin: 0 auto;
        position: relative;
    }}

    /* Style the inner dashed border */
    .custom-upload-inner {{
        border: 2px dashed #A7F3D0; /* Light green dashed border */
        border-radius: 16px;
        padding: 40px 20px 30px 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        background-color: #FAFAFA;
    }}

    /* Cloud Icon */
    .cloud-icon {{
        width: 64px;
        height: 64px;
        margin-bottom: 20px;
        opacity: 0.6;
    }}

    /* Main Text */
    .upload-text-main {{
        color: #374151;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 10px;
    }}

    /* Divider */
    .upload-divider {{
        display: flex;
        align-items: center;
        width: 50%;
        margin: 15px 0;
    }}
    .upload-divider::before, .upload-divider::after {{
        content: "";
        flex: 1;
        border-bottom: 1px solid #E5E7EB;
    }}
    .upload-divider span {{
        padding: 0 15px;
        color: #9CA3AF;
        font-size: 0.9rem;
    }}

    /* Fake Button */
    .upload-btn-fake {{
        background-color: #FF9933;
        color: white;
        font-weight: 600;
        padding: 12px 36px;
        border-radius: 30px;
        font-size: 1.05rem;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(255, 153, 51, 0.3);
    }}

    /* Sub Text */
    .upload-text-sub {{
        color: #9CA3AF;
        font-size: 0.85rem;
    }}

    /* Make the real Streamlit uploader invisible and overlay it on top */
    [data-testid="stFileUploader"] {{
        opacity: 0 !important;
        position: relative;
        top: -340px; /* Pull it up over the custom UI */
        margin-bottom: -340px; /* Prevent it from taking up extra space */
        height: 340px !important;
        z-index: 999;
    }}
    [data-testid="stFileUploader"] > section {{
        height: 100% !important;
        cursor: pointer !important;
    }}

    /* Center the Generate/Download buttons (Colors applied dynamically) */
    div.stButton > button, div.stDownloadButton > button {{
        border-radius: 25px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        display: block;
        margin: 0 auto;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown(f'''
<div class="title-container">
    <img src="data:image/png;base64,{logo_base64}" class="logo-img">
    <div class="main-heading">
        <span class="saffron">Tricolor in </span> <span class="green">Every Frame</span>
    </div>
    <p class="sub-heading">Upload your photo and let AI create your <b style="color: #FF9933;">Independence</b> <b style="color: #138808;">Day</b> portrait.</p>
</div>
''', unsafe_allow_html=True)


# Handle state
if "result_img" not in st.session_state:
    st.session_state.result_img = None
if "portrait_generated" not in st.session_state:
    st.session_state.portrait_generated = False

# Create a placeholder for the custom HTML box so it always renders BEFORE the file uploader in the DOM
box_placeholder = st.empty()

# Render the invisible file uploader right after the placeholder
uploaded_files = st.file_uploader("Upload your photo", type=["png", "jpg", "jpeg"], accept_multiple_files=True, label_visibility="hidden")

if not uploaded_files:
    # STATE 1: UPLOAD
    st.session_state.result_img = None
    st.session_state.portrait_generated = False
    
    # Fill the placeholder with the initial upload box
    box_placeholder.markdown('''
    <div class="custom-upload-container">
        <div class="custom-upload-inner">
            <svg class="cloud-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="#6B7280">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div class="upload-text-main">Drag & drop your photo here</div>
            <div class="upload-divider"><span>or</span></div>
            <div class="upload-btn-fake">Browse Files</div>
            <div class="upload-text-sub">PNG, JPG up to 20MB</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
else:
    # A file is uploaded. Hide the invisible uploader completely.
    st.markdown('<style>[data-testid="stFileUploader"] { display: none !important; }</style>', unsafe_allow_html=True)
    
    uploaded_file = uploaded_files[0]
    user_pil = Image.open(uploaded_file).convert("RGB")
    user_img = np.array(user_pil)
    
    if not st.session_state.portrait_generated:
        # STATE 2: GENERATE
        box_placeholder.markdown('''
        <div class="custom-upload-container">
            <div class="custom-upload-inner" style="padding-bottom: 20px;">
                <svg class="cloud-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="#1E3A8A">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div class="upload-text-main">Image Uploaded Successfully!</div>
                <div class="upload-text-sub" style="margin-bottom: 20px;">Ready to generate your tricolor portrait.</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<style>div.stButton { margin-top: 10px; } div.stButton > button { background-color: white !important; color: #FF9933 !important; border: 2px solid #FF9933 !important; } div.stButton > button:hover { background-color: #FFF3E0 !important; }</style>', unsafe_allow_html=True)
        
        if st.button("Generate Portrait"):
            with st.spinner("Generating your portrait... This might take a few seconds."):
                res = process_independence_day_avatar_v2(user_img)
                if res:
                    st.session_state.result_img = res
                    st.session_state.portrait_generated = True
                    st.rerun()
    else:
        # STATE 3: DOWNLOAD
        box_placeholder.markdown('''
        <div class="custom-upload-container">
            <div class="custom-upload-inner" style="padding-bottom: 20px;">
                <svg class="cloud-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="#138808">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <div class="upload-text-main">Portrait Generated!</div>
                <div class="upload-text-sub" style="margin-bottom: 20px;">Your Independence Day portrait is ready.</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<style>div.stDownloadButton { margin-top: 10px; margin-bottom: 40px; } div.stDownloadButton > button { background-color: #138808 !important; color: white !important; border: none !important; box-shadow: 0 4px 6px -1px rgba(19, 136, 8, 0.3) !important; } div.stDownloadButton > button:hover { background-color: #0F6B06 !important; }</style>', unsafe_allow_html=True)
        
        buf = BytesIO()
        st.session_state.result_img.save(buf, format="JPEG", quality=95)
        byte_im = buf.getvalue()
        
        st.download_button(
            label="Download Portrait",
            data=byte_im,
            file_name="independence_day_portrait.jpg",
            mime="image/jpeg"
        )
        
        st.image(st.session_state.result_img, caption="Your Advanced Independence Day Portrait", use_container_width=True)
