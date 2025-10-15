import tkinter as tk
from tkinter import font, messagebox
import frontend_config as config
from . import ui_helpers
from PIL import Image, ImageTk
# ---- top of file ----
import os, sys

# Ensure project root is on sys.path so "backend" is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.locked_files_store import load_locked_files


# def show_applications_screen(app):
#     """Shows the application management screen for a logged-in user with modern card + rounded button style."""
#     ui_helpers.update_nav_selection(app, "applications")

#     LIGHT_CARD_BG = "#AD567C"

#     card = ui_helpers.create_main_card(app, width=820, height=520)
#     card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
#     card.pack(expand=True, fill="both")   
#     # If not logged in
#     if not app.currently_logged_in_user:
#         card = ui_helpers.create_main_card(app, width=600, height=300)
#         card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

#         tk.Label(
#             card,
#             text="Please log in to manage application settings.",
#             font=app.font_large,
#             fg=config.TEXT_COLOR,
#             bg=LIGHT_CARD_BG,
#             wraplength=400
#         ).pack(expand=True)
#         return

#     user = app.currently_logged_in_user

#     # --- Main Card ---
#     card = ui_helpers.create_main_card(app, width=820, height=420)
#     card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

#     # Title
#     tk.Label(
#         card,
#         text="Manage Applications",
#         font=app.font_large,
#         fg=config.TEXT_COLOR,
#         bg=LIGHT_CARD_BG
#     ).pack(pady=(20, 10))

#     # Wrapper for cards
#     cards_frame = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
#     # cards_frame.pack(expand=True, pady=10)
#     cards_frame.pack(expand=True, fill="both", padx=20, pady=10)

#     # --- Helper to create consistent cards ---
#     def _create_app_card(parent, icon, title, details, button_text, button_command):
#         c = tk.Frame(parent, bg=config.CARD_BG_COLOR, width=230, height=300, relief="flat", bd=0)
#         c.pack(side="left", padx=15, pady=10)
#         c.pack_propagate(False)

#         # Icon
#         tk.Label(c, image=icon, bg=config.CARD_BG_COLOR).pack(pady=(20, 10))
#         # Title
#         tk.Label(c, text=title, font=app.font_medium_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack()
#         # Details
#         for line in details:
#             tk.Label(c, text=line, font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR, wraplength=200).pack(pady=3)

#         # Button
#         tk.Button(
#             c,
#             text=button_text,
#             font=app.font_small,
#             bg=config.BUTTON_LIGHT_COLOR,
#             fg=config.BUTTON_LIGHT_TEXT_COLOR,
#             relief="flat",
#             padx=12, pady=6,
#             command=button_command
#         ).pack(side=tk.BOTTOM, pady=15)

#         return c

#     # --- Password Card ---
#     _create_app_card(
#         cards_frame,
#         app.key_img,
#         "Password",
#         ["********"],
#         "Edit Password",
#         app.show_change_password_screen
#     )

#     # --- Voice Biometrics Card ---
#     voice_status = "Enrolled" if user.get('voiceprint_path') else "Not Enrolled"
#     _create_app_card(
#         cards_frame,
#         app.mic_img,
#         "Voice Biometrics",
#         [f"Status: {voice_status}"],
#         "Edit Biometrics",
#         app.show_password_screen_voice_entry1
#     )

#     # --- OTP Settings Card ---
#     masked_email = app._mask_email(user.get('email', ''))
#     _create_app_card(
#         cards_frame,
#         app.otp_img,
#         "OTP Settings",
#         ["Account:", masked_email],
#         "Edit Email Address",
#         app.show_change_otp_settings_screen
#     )


def show_applications_screen(app):
    """Shows the application management screen for a logged-in user with modern card + rounded button style."""
    import tkinter as tk

    ui_helpers.update_nav_selection(app, "applications")
    LIGHT_CARD_BG = "#AD567C"

    # --- Main card ---
    card = ui_helpers.create_main_card(app, width=820, height=440)
    card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    card.pack(expand=True, fill="both")

    # If not logged in
    if not app.currently_logged_in_user:
        card = ui_helpers.create_main_card(app, width=600, height=300)
        card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
        tk.Label(
            card,
            text="Please log in to manage application settings.",
            font=app.font_large,
            fg=config.TEXT_COLOR,
            bg=LIGHT_CARD_BG,
            wraplength=400,
            justify="center"
        ).pack(expand=True, padx=24, pady=24)
        return

    user = app.currently_logged_in_user

    # Title
    tk.Label(
        card,
        text="Manage Applications",
        font=app.font_large,
        fg=config.TEXT_COLOR,
        bg=LIGHT_CARD_BG
    ).pack(pady=(16, 6))

    # === Cards row (uses GRID for perfect columns) ===
    # Outer padding for the card area
    cards_frame = tk.Frame(card, bg=LIGHT_CARD_BG)
    cards_frame.pack(fill="x", padx=24, pady=(6, 18))

    # Grid config: 4 equal columns with a uniform name for equal sizing
    for col in range(4):
        cards_frame.grid_columnconfigure(col, weight=1, uniform="cards")

    # Tidy vertical padding in the row
    cards_frame.grid_rowconfigure(0, weight=1)

    # ---- Card builder (fixed size; internal grid keeps button at bottom) ----
    CARD_MIN_W = 170
    CARD_MIN_H = 250
    ICON_AREA_H = 60

    def _create_app_card(parent, col, icon, title, details, button_text, button_command):
        c = tk.Frame(parent, bg=config.CARD_BG_COLOR, bd=0, relief="flat")
        c.grid(row=0, column=col, padx=12, pady=8, sticky="nsew")  # even gutters
        c.update_idletasks()  # ensure geometry exists
        c.grid_propagate(False)  # we’ll control size via minsize below

        # Give each column a min size so all cards match width/height
        parent.grid_columnconfigure(col, minsize=CARD_MIN_W)

        # Internal grid: icon / title / details (expand) / button (bottom)
        c.grid_rowconfigure(0, minsize=ICON_AREA_H)
        c.grid_rowconfigure(1, minsize=26)
        c.grid_rowconfigure(2, weight=1, minsize=80)
        c.grid_rowconfigure(3, minsize=44)
        c.grid_columnconfigure(0, weight=1)

        # Icon (centered, consistent height)
        icon_wrap = tk.Frame(c, bg=config.CARD_BG_COLOR, height=ICON_AREA_H)
        icon_wrap.grid(row=0, column=0, sticky="nsew", pady=(12, 4))
        icon_wrap.pack_propagate(False)
        tk.Label(icon_wrap, image=icon, bg=config.CARD_BG_COLOR).pack(expand=True)

        # Title
        tk.Label(
            c, text=title, font=app.font_medium_bold,
            fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR
        ).grid(row=1, column=0, sticky="n", pady=(0, 2))

        # Details (fills remaining space so buttons align across cards)
        details_box = tk.Frame(c, bg=config.CARD_BG_COLOR)
        details_box.grid(row=2, column=0, sticky="nsew", padx=10)
        for line in details:
            tk.Label(
                details_box, text=line, font=app.font_normal,
                fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR,
                wraplength=CARD_MIN_W - 24, justify="center"
            ).pack(pady=2)

        # Button (pinned to bottom)
        tk.Button(
            c, text=button_text, command=button_command,
            font=app.font_small, relief="flat",
            bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
            padx=10, pady=6
        ).grid(row=3, column=0, pady=(6, 12))

        # Enforce overall min height for each card
        c.update_idletasks()
        c.configure(height=max(CARD_MIN_H, c.winfo_height()))

        return c

    # Data
    voice_status = "Enrolled" if user.get('voiceprint_path') else "Not Enrolled"
    masked_email = app._mask_email(user.get('email', ''))

    # Password Card
    _create_app_card(
        cards_frame, 
        0, 
        app.key_img, 
        "Password", 
        ["********"],
        "Edit Password", 
        app.show_change_password_screen)

    # Voice Biometrics Card
    _create_app_card(
        cards_frame, 
        1, 
        app.mic_img, 
        "Voice Biometrics", 
        [f"Status: {voice_status}"],
        "Edit Biometrics", app.show_password_screen_voice_entry1)

    # OTP Settings Card
    _create_app_card(
        cards_frame, 
        2, app.otp_img, 
        "OTP Settings", 
        ["Account:", masked_email],
        "Edit Email", 
        app.show_change_otp_settings_screen)

    # File Manager Card
    file_status_lines = _files_status_lines(app)
    _create_app_card(
        cards_frame, 
        3,
        getattr(app, "files_img", getattr(app, "folder_img", app.key_img)),
        "File Manager",
        file_status_lines,                 # <-- use the dynamic status line
        "Manage Files",
        getattr(app, "show_file_settings_screen", app.show_manage_files_screen)
    )

def _files_status_lines(app):
    """Return ['No files yet'] or ['N files uploaded'] safely."""
    user = getattr(app, "currently_logged_in_user", None) or {}
    username = user.get("username")
    if not username:
        return ["No files yet"]  # not logged in / no username

    try:
        locked_files = load_locked_files(username) or []
    except Exception:
        locked_files = []

    n = len(locked_files)
    if n == 0:
        return ["No files yet"]
    if n == 1:
        return ["1 file uploaded"]
    return [f"{n} files uploaded"]

def show_about_screen(app, event=None):
    """Displays the About Us screen with an icon + modern card design."""
    ui_helpers.update_nav_selection(app, None)

    LIGHT_CARD_BG = "#AD567C"
    INFO_CARD_BG = "#AD567C"
    INFO_CARD_TEXT = "#ffffff"

    card = ui_helpers.create_main_card(app, width=820, height=480)
    card.config(bg=LIGHT_CARD_BG, relief="flat", bd=0, highlightthickness=0)

    content_frame = tk.Frame(card, bg=LIGHT_CARD_BG)
    content_frame.pack(expand=True, pady=20, padx=30, fill="both")

    # --- Title Row with Icon ---
    title_frame = tk.Frame(content_frame, bg=LIGHT_CARD_BG)
    title_frame.pack(anchor="w", pady=(0, 20))

    icon_font = font.Font(family=config.FONT_FAMILY, size=24, weight="bold")
    title_font = font.Font(family=config.FONT_FAMILY, size=22, weight="bold")

    # tk.Label(title_frame, text="ℹ️", font=icon_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left", padx=(0, 10))
    tk.Label(title_frame, text="About Us", font=title_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left")

    # --- About Text Card ---
    about_card = tk.Frame(content_frame, bg=INFO_CARD_BG, bd=0, relief="flat")
    about_card.pack(pady=(0, 20), fill="x")

    body_font = font.Font(family=config.FONT_FAMILY, size=12)
    about_text = (
        "KeyVox is a plug-and-play hardware authentication token that uses "
        "your unique voice as a robust and secure second factor of authentication (2FA), "
        "powered by advanced LSTM neural networks.\n\n"
        "The key is designed to work with multi-protocol systems such as "
        "FIDO U2F, OATH TOTP, and challenge-response systems."
    )
    tk.Label(
        about_card, text=about_text,
        font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG,
        justify="left", wraplength=720
    ).pack(padx=25, pady=20, anchor="w")

    # --- Subtitle + Bullets ---
    subtitle_font = font.Font(family=config.FONT_FAMILY, size=16, weight="bold")
    tk.Label(
        content_frame, text="How Voice Authentication Works",
        font=subtitle_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG
    ).pack(anchor="w", padx=20, pady=(0, 15))

    bullets = [
        "Analyze and learn the unique patterns in your voice.",
        "Match live voice input against your stored encrypted voiceprint.",
        "Authenticate only if the match is within the secure threshold."
    ]
    for bullet in bullets:
        tk.Label(
            content_frame, text=f"• {bullet}",
            font=body_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG,
            justify="left", wraplength=700
        ).pack(anchor="w", padx=40, pady=3)

def show_help_screen(app, event=None):
    """Displays the Help/FAQ screen with a modern card design similar to the About Us page."""
    ui_helpers.update_nav_selection(app, None)

    LIGHT_CARD_BG = "#AD567C"
    INFO_CARD_BG = "#AD567C"
    INFO_CARD_TEXT = "#ffffff"

    # --- Main Card ---
    card = ui_helpers.create_main_card(app, width=820, height=480)
    card.config(bg=LIGHT_CARD_BG, relief="flat", bd=0, highlightthickness=0)

    content_frame = tk.Frame(card, bg=LIGHT_CARD_BG)
    content_frame.pack(expand=True, pady=20, padx=30, fill="both")

    # --- Title Row with Icon ---
    title_frame = tk.Frame(content_frame, bg=LIGHT_CARD_BG)
    title_frame.pack(anchor="w", pady=(0, 20))

    icon_font = font.Font(family=config.FONT_FAMILY, size=24, weight="bold")
    title_font = font.Font(family=config.FONT_FAMILY, size=22, weight="bold")

    # tk.Label(title_frame, text="❓", font=icon_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left", padx=(0, 10))
    tk.Label(title_frame, text="Need Help?", font=title_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left")

    # --- Info Card: Setup Instructions ---
    setup_card = tk.Frame(content_frame, bg=INFO_CARD_BG, bd=0, relief="flat")
    setup_card.pack(pady=(0, 20), fill="x")

    subtitle_font = font.Font(family=config.FONT_FAMILY, size=16, weight="bold")
    body_font = font.Font(family=config.FONT_FAMILY, size=12)

    tk.Label(
        setup_card, text="Setup Instructions",
        font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG
    ).pack(anchor="w", padx=20, pady=(20, 10))

    setup_steps = [
        "1. Connect your KeyVox device to your computer via USB.",
        "2. Launch the KeyVox App — it can be pre-installed or downloaded from the official source.",
        "3. Begin the voice enrollment process by following the on-screen instructions.",
        "4. Record a short voice phrase 3–5 times in a quiet place to build your secure voiceprint.",
        "5. Configure your preferred authentication protocols (FIDO, OATH, or challenge-response)."
    ]

    for step in setup_steps:
        tk.Label(
            setup_card, text=f"{step}",
            font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG,
            justify="left", wraplength=720
        ).pack(anchor="w", padx=20, pady=3)

    # --- Info Card: Security Tips ---
    tips_card = tk.Frame(content_frame, bg=INFO_CARD_BG, bd=0, relief="flat")
    tips_card.pack(pady=(0, 25), fill="x")

    tk.Label(
        tips_card, text="Security Tips",
        font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG
    ).pack(anchor="w", padx=20, pady=(20, 10))

    tips = [
        "• Enroll in a quiet environment to ensure clear and accurate voice capture.",
        "• Re-enroll your voice if you experience major changes in your voice tone or quality.",
        "• Avoid sharing your voice recordings or authentication phrases publicly.",
        "• Keep your KeyVox device secure and avoid using it on untrusted computers.",
    ]

    for tip in tips:
        tk.Label(
            tips_card, text=tip,
            font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG,
            justify="left", wraplength=720
        ).pack(anchor="w", padx=20, pady=3)

    # --- Footer Note ---
    footer_font = font.Font(family=config.FONT_FAMILY, size=11, slant="italic")
    tk.Label(
        content_frame,
        text="If you continue experiencing issues, contact KeyVox Support for assistance.",
        font=footer_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG, justify="left", wraplength=720
    ).pack(anchor="w", pady=(10, 0), padx=20)


