import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageFont
from rembg import remove, new_session
import requests
from io import BytesIO
import os

st.set_page_config(page_title="Data Vidwan Independence Day Portrait")

MAIN_BG_URL = "https://i.pinimg.com/originals/7d/a7/1c/7da71cec97c84a82d01280fbbb66c145.jpg"

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

    bg_blurred = main_bg.filter(ImageFilter.GaussianBlur(radius=4))
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

    glow_size = 12
    glow_alpha = Image.new("L", (target_w + glow_size * 2, target_h + glow_size * 2), 0)
    glow_mask = cutout_scaled.split()[3].filter(ImageFilter.GaussianBlur(radius=6))
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

# Custom CSS for styling
st.markdown("""
<style>
    .main-heading {
        color: #1E3A8A; /* Dark Blue */
        font-size: 2.1rem !important;
        font-weight: 800;
        margin-bottom: 0rem;
    }
    .sub-heading {
        color: #3B82F6; /* Lighter Blue */
        font-size: 1.05rem;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
    }
    /* Style both buttons identically */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #1E3A8A !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #2563EB !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-heading"><img src="https://i.ibb.co/dwQt56Cf/DV-Logo.png" style="height: 1em; vertical-align: middle; margin-right: 10px; margin-bottom: 5px;"> Data Vidwan Independence Day Portrait</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-heading">Upload your photo below, and our advanced AI engine will do the magic to generate your portrait.</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your photo", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Convert uploaded file using PIL for maximum compatibility
    user_pil = Image.open(uploaded_file).convert("RGB")
    user_img = np.array(user_pil)
    
    # Display the uploaded image
    st.image(user_img, caption="Uploaded Image", use_container_width=True)
    
    if st.button("Generate Portrait"):
        with st.spinner("Generating your portrait... This might take a few seconds."):
            result_img = process_independence_day_avatar_v2(user_img)
            
            if result_img:
                st.image(result_img, caption="Your Advanced Independence Day Portrait", use_container_width=True)
                
                # Allow user to download
                buf = BytesIO()
                result_img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="Download Portrait",
                    data=byte_im,
                    file_name="independence_day_portrait.png",
                    mime="image/png"
                )
