
from pathlib import Path
from io import BytesIO

import streamlit as st
from PIL import Image

from bg_removal import (
    BackgroundModelDownloadError,
    remove_background,
    replace_with_color,
    replace_with_image,
)


# -----------------------------------
# Page configuration
# -----------------------------------

st.set_page_config(
    page_title="AI Background Remover",
    page_icon="✂️",
    layout="wide",
)

st.title("AI Background Remover")

st.write(
    "Upload an image and remove its background "
    "using computer vision."
)

st.caption(
    "Supports PNG, JPG, JPEG and WEBP images."
)


# -----------------------------------
# Upload original image
# -----------------------------------

uploaded_file = st.file_uploader(
    "Upload your image",
    type=["png", "jpg", "jpeg", "webp"],
)

if uploaded_file is None:
    st.info("Upload an image to get started.")
    st.stop()


source_bytes = uploaded_file.getvalue()
source_name = Path(uploaded_file.name).stem


# Reset the old result if a new image is uploaded.
if st.session_state.get("source_bytes") != source_bytes:
    st.session_state["source_bytes"] = source_bytes
    st.session_state.pop("removed_png", None)


try:
    original_image = Image.open(
        BytesIO(source_bytes)
    ).convert("RGB")

except Exception:
    st.error("Unable to open this image.")
    st.stop()


st.subheader("Original image")

st.image(
    original_image,
    use_container_width=True
)

st.caption(
    f"Image dimensions: "
    f"{original_image.width} × {original_image.height}"
)


# -----------------------------------
# Remove the background
# -----------------------------------

if st.button(
    "Remove Background",
    type="primary"
):

    try:
        with st.spinner(
            "AI is removing the background..."
        ):
            st.session_state["removed_png"] = (
                remove_background(source_bytes)
            )

        st.success("Background removed successfully!")

    except BackgroundModelDownloadError as error:
        st.error(str(error))
    except Exception as error:
        st.error("Background removal failed.")
        st.exception(error)


if "removed_png" not in st.session_state:
    st.info(
        "Click Remove Background to process your image."
    )
    st.stop()


removed_png = st.session_state["removed_png"]


# -----------------------------------
# Choose output background
# -----------------------------------

st.divider()
st.subheader("Customize your result")

background_mode = st.radio(
    "Background option",
    [
        "Transparent",
        "Solid color",
        "Background image"
    ],
    horizontal=True,
)

final_png = removed_png


if background_mode == "Solid color":

    color = st.color_picker(
        "Choose a background color",
        "#FFFFFF"
    )

    final_png = replace_with_color(
        removed_png,
        color
    )


elif background_mode == "Background image":

    background_file = st.file_uploader(
        "Upload a replacement background",
        type=["png", "jpg", "jpeg", "webp"],
        key="replacement_background",
    )

    if background_file is not None:

        try:
            final_png = replace_with_image(
                removed_png,
                background_file.getvalue()
            )

        except Exception as error:
            st.error("Unable to process the new background.")
            st.exception(error)


# -----------------------------------
# Display both results
# -----------------------------------

left, right = st.columns(2)

with left:
    st.subheader("Transparent cutout")

    st.image(
        removed_png,
        use_container_width=True
    )

with right:
    st.subheader("Final result")

    st.image(
        final_png,
        use_container_width=True
    )


# -----------------------------------
# Download the result
# -----------------------------------

output_name = (
    f"{source_name}_background_removed.png"
    if background_mode == "Transparent"
    else f"{source_name}_new_background.png"
)

st.download_button(
    label="Download Image",
    data=final_png,
    file_name=output_name,
    mime="image/png",
    type="primary",
)

st.caption(
    "The result is downloaded as a PNG image."
)