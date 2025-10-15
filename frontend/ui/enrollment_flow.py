import tkinter as tk
from tkinter import messagebox, font as tkFont
import os
import sys
import frontend_config as config
from ui import ui_helpers
from utils.validators import validate_email, validate_password

# Ensure backend is importable
import os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # .../frontend/ui
PROJECT_ROOT = HERE.parent.parent                 # .../ (project root)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Now always import with the full package path
# from backend.locked_files_store import (
#     load_locked_files,
#     save_locked_files,
#     append_locked_file,
#     remove_locked_file_by_index,
#     build_meta_for_existing_path,
#     relink_locked_file,
#     add_and_copy_file, 
# )

from backend.locked_files_store import load_locked_files, add_and_move_file


# If OTP lives at project_root/OTP, this works. If it lives inside frontend, keep as-is.
from OTP.send_otp import send_otp, verify_otp

print("add_and_move_file loaded:", add_and_move_file)

def navigate_to_enrollment(app, event=None):
    ui_helpers.update_nav_selection(app, "enrollment")

    # CASE 1: No logged-in user → Show login prompt or first step
    if not app.currently_logged_in_user:
        show_enrollment_step1(app)
        return

    # CASE 2: Logged in → Show message "You are already enrolled"
    show_enrollment_status(app)

def show_enrollment_status(app):
    """Profile-like screen + 'Deactivate Account' button with an enhanced UI (no destructive logic)."""
    # --- Theme / Styling ---
    COLOR_BACKGROUND = "#AD567C"
    COLOR_CARD_BG    = "#AD567C"
    COLOR_TEXT       = "#f4b9d0"
    COLOR_LABEL      = "#ffffff"
    COLOR_DANGER     = "#950D58"

    FONT_FAMILY = "Segoe UI"
    font_title  = tkFont.Font(family=FONT_FAMILY, size=18, weight="bold")
    font_label  = tkFont.Font(family=FONT_FAMILY, size=11)
    font_value  = tkFont.Font(family=FONT_FAMILY, size=12, weight="bold")
    font_button = tkFont.Font(family=FONT_FAMILY, size=10, weight="bold")
    font_icon   = tkFont.Font(family=FONT_FAMILY, size=60)

    # --- Guard & reset ---
    if not hasattr(app, "content_frame"):
        raise AttributeError("App is missing 'content_frame' Frame.")

    for widget in app.content_frame.winfo_children():
        widget.destroy()
    app.content_frame.configure(bg=COLOR_BACKGROUND)

    # --- Card ---
    card = tk.Frame(app.content_frame, bg=COLOR_CARD_BG, padx=40, pady=30)
    card.pack(expand=True)

    # Make grid behave nicely
    card.grid_columnconfigure(0, weight=0)  # icon column
    card.grid_columnconfigure(1, weight=1)  # content column

    # --- Profile Icon ---
    profile_icon = tk.Label(card, text="👤", font=font_icon, bg=COLOR_CARD_BG, fg=COLOR_LABEL)
    profile_icon.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 30))

    # --- Title ---
    title_label = tk.Label(card, text="You are already Enrolled", font=font_title, fg=COLOR_LABEL, bg=COLOR_CARD_BG)
    title_label.grid(row=0, column=1, sticky="w", pady=(0, 20))

    # --- Details ---
    details_frame = tk.Frame(card, bg=COLOR_CARD_BG)
    details_frame.grid(row=1, column=1, sticky="ew")
    details_frame.grid_columnconfigure(0, weight=0)
    details_frame.grid_columnconfigure(1, weight=1)

    user = app.currently_logged_in_user if isinstance(getattr(app, "currently_logged_in_user", None), dict) else {}
    full_name = user.get("full_name", "N/A")
    username  = user.get("username", "—")
    email     = user.get("email", "—")

    rows = [("Full Name", full_name), ("Username", username), ("Email", email)]
    for i, (label_text, value_text) in enumerate(rows):
        tk.Label(details_frame, text=label_text, font=font_label, fg=COLOR_LABEL, bg=COLOR_CARD_BG)\
          .grid(row=i, column=0, sticky="w", pady=2)
        tk.Label(details_frame, text=value_text, font=font_value, fg=COLOR_TEXT, bg=COLOR_CARD_BG)\
          .grid(row=i, column=1, sticky="w", padx=(15, 0), pady=2)

    # --- Deactivate Button ---
    def on_deactivate():
        _deactivate_current_user(app)  # safe stub (no DB writes yet)

    deactivate_button = tk.Button(
        card,
        text="Deactivate Account",
        font=font_button,
        bg=COLOR_DANGER,
        fg=COLOR_LABEL,
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        activebackground="#950D58",
        activeforeground=COLOR_TEXT,
        pady=8,
        padx=15,
        command=on_deactivate
    )
    deactivate_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(40, 0))


def _deactivate_current_user(app):
    """
    Stub: Confirmation + 'Not Implemented' notice.
    No changes to users.json, no logout, no navigation.
    Replace later with real logic when you're ready.
    """
    from tkinter import messagebox

    user = getattr(app, "currently_logged_in_user", None)
    who = ""
    if isinstance(user, dict):
        who = user.get("full_name") or user.get("username") or user.get("email") or ""
        who = f" ({who})" if who else ""

    proceed = messagebox.askyesno(
        "Confirm Deactivation",
        f"Are you sure you want to deactivate your account{who}?\n\n"
        "Note: Deactivation isn't available yet."
    )
    if not proceed:
        return

    messagebox.showinfo(
        "Not Implemented",
        "Deactivation is not available yet. No changes were made."
    )

def show_enrollment_step1(app):
    """STEP 1: Account setup."""
    LIGHT_CARD_BG = "#AD567C"

    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step1_account_setup'
    app.new_enrollment_data = {}        # will hold full_name, username, email, password (in memory)
    app.pending_voice_file = None       # set after recording, used post-OTP to enroll
    app.selected_lock_path = None       # used in step 4

    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=700, height=400, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)
    card.grid_columnconfigure(1, weight=1)

    tk.Label(card, text="STEP 1: Account Setup", font=font_title,
             fg="white", bg=LIGHT_CARD_BG).grid(row=0, column=0, columnspan=2,
                                               sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Enter your basic account information",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG).grid(row=1, column=0,
                                                                   columnspan=2,
                                                                   sticky="w",
                                                                   pady=(0, 20),
                                                                   padx=40)

    fields = {
        "Full Name:": "full_name",
        "Username:": "username",
        "Email Address:": "email",
        "Password:": "password",
        "Confirm Password:": "confirm_password"
    }
    app.entry_widgets = {}

    def make_password_field(parent, key):
        entry_frame = tk.Frame(parent, bg="white")
        entry = tk.Entry(entry_frame, font=font_entry, width=22,
                         bg="white", fg="black", relief="flat", bd=0,
                         show="*", insertbackground="black")
        entry.pack(side="left", ipady=4, padx=(5, 0))
        app.entry_widgets[key] = entry

        def toggle_visibility():
            if entry.cget("show") == "*":
                entry.config(show=""); btn.config(image=app.eye_closed_img)
            else:
                entry.config(show="*"); btn.config(image=app.eye_open_img)

        btn = tk.Button(entry_frame, image=app.eye_open_img, bg="white", relief="flat", bd=0,
                        activebackground="white", cursor="hand2", command=toggle_visibility)
        btn.pack(side="right", padx=(0, 5))
        return entry_frame

    for i, (label, key) in enumerate(fields.items()):
        tk.Label(card, text=label, font=font_label,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=0,
                                                    sticky="w", pady=6, padx=(40, 20))
        if "Password" in label:
            frame = make_password_field(card, key)
            frame.grid(row=i + 2, column=1, pady=6, padx=(0, 40), sticky="ew")
        else:
            entry = tk.Entry(card, font=font_entry, width=25,
                             bg="white", fg="black", relief="flat", bd=0,
                             insertbackground="black")
            entry.grid(row=i + 2, column=1, pady=6, ipady=4, padx=(0, 40), sticky="ew")
            app.entry_widgets[key] = entry

    app.enroll_error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(10, 0))

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    dots_frame = tk.Frame(bf, bg=bf.cget('bg'))
    dots_frame.pack(side="left")
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)

    tk.Button(bf, text="Next Step →", font=font_button,
              bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
              command=lambda: validate_step1(app)).pack(side="right")

def validate_step1(app):
    data = {key: entry.get() for key, entry in app.entry_widgets.items()}

    # Email and password validation
    email_valid, email_err = validate_email(data.get("email", ""))
    if not email_valid:
        app.enroll_error_label.config(text=email_err)
        return

    password_valid, password_err = validate_password(data.get("password", ""))
    if not password_valid:
        app.enroll_error_label.config(text=password_err)
        return

    if data["password"] != data["confirm_password"]:
        app.enroll_error_label.config(text="Passwords do not match.")
        return

    # Save in-memory (do NOT persist yet)
    app.new_enrollment_data = {k: v for k, v in data.items() if k != "confirm_password"}
    app.enroll_error_label.config(text="")
    show_enrollment_step2(app)

def show_enrollment_step2(app):
    """STEP 2: Voice intro."""
    LIGHT_CARD_BG = "#AD567C"
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step2_voice_intro'
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30); card.pack_propagate(False)

    tk.Label(card, text="STEP 2: Voice Authentication", font=font_title, fg="white", bg=LIGHT_CARD_BG)\
        .pack(anchor="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Record your voice for added security.\nYou will record 5 phrases to create your voiceprint.",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG, justify="left", wraplength=600)\
        .pack(anchor="w", pady=(0, 25), padx=40)

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG); bf.pack(fill="x", padx=60, pady=(0, 10))
    tk.Button(bf, text="< Back", font=font_button, bg=config.BUTTON_LIGHT_COLOR,
              fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4,
              command=lambda: show_enrollment_step1(app)).pack(side="left")

    dots_frame = tk.Frame(bf, bg=bf.cget('bg')); dots_frame.pack(side="left", padx=20)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)

    tk.Button(bf, text="Start →", font=font_button, bg=config.BUTTON_LIGHT_COLOR,
              fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4,
              command=lambda: show_enrollment_voice_record(app)).pack(side="right")

def show_enrollment_voice_record(app):
    """STEP 3: Voice record phrases."""
    LIGHT_CARD_BG = "#AD567C"
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step3_voice_record'
    font_title = tkFont.Font(family="Poppins", size=12, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30); card.pack_propagate(False)

    tk.Label(card, text=f"{app.current_phrase_index + 1} of {len(app.enrollment_phrases)}",
             font=font_text, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 0))
    tk.Label(card, text=f'"{app.enrollment_phrases[app.current_phrase_index]}"',
             font=font_title, fg="white", bg=LIGHT_CARD_BG, wraplength=600).pack(expand=True)

    mic_label = tk.Label(card, image=app.mic_img, bg=LIGHT_CARD_BG, highlightthickness=0, cursor="hand2")
    mic_label.pack(pady=10); mic_label.bind("<Button-1>", app.toggle_recording)
    app.recording_status_label = tk.Label(card, text="Click the mic to record", font=font_text, fg="white", bg=LIGHT_CARD_BG)
    app.recording_status_label.pack(pady=(0, 20))

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG); bf.pack(fill="x", padx=60, pady=(0, 10))
    tk.Button(bf, text="< Back", font=font_button, bg=config.BUTTON_LIGHT_COLOR,
              fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4,
              command=lambda: go_back_phrase(app)).pack(side="left")

    # After enough audio is recorded, this button is enabled by your recorder.
    app.next_btn = tk.Button(
        bf, text="Next →", font=font_button, bg=config.BUTTON_LIGHT_COLOR,
        fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4,
        command=lambda: handle_final_enrollment_upload(app, next_step="otp"),
        state="disabled"
    )
    app.next_btn.pack(side="right")

def go_back_phrase(app):
    if app.current_phrase_index > 0:
        app.current_phrase_index -= 1
        show_enrollment_voice_record(app)
    else:
        show_enrollment_step2(app)

def go_next_phrase(app):
    """Kept for completeness if you still navigate by phrases."""
    if app.current_phrase_index < len(app.enrollment_phrases) - 1:
        app.current_phrase_index += 1
        show_enrollment_voice_record(app)
    else:
        handle_final_enrollment_upload(app, next_step="otp")

def handle_final_enrollment_upload(app, next_step="otp"):
    """
    NEW FLOW: Do NOT register the user here.
    We only verify the required audio exists, then go to OTP.
    Registration & voice enrollment happen AFTER OTP success.
    """
    username = app.new_enrollment_data.get("username")
    if not username:
        messagebox.showerror("Error", "Missing username from Step 1.")
        return

    audio_path = os.path.join(config.AUDIO_DIR, f"{username}_phrase_1.wav")
    if not os.path.exists(audio_path):
        messagebox.showerror("Error", "Primary enrollment audio not found. Please record phrase 1 again.")
        return

    # Stash the path for post-OTP voice enrollment
    app.pending_voice_file = audio_path

    # Move to OTP step
    show_enrollment_step3_otp(app)

def show_enrollment_step3_otp(app):
    """STEP 3.5: OTP verification (before user registration)."""
    LIGHT_CARD_BG = "#AD567C"

    # Bind email from Step 1 for OTP
    app.user_email_for_otp = app.new_enrollment_data.get('email', 'your_email@example.com')
    email_from_step1 = app.user_email_for_otp

    # Clear old widgets
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=12)
    font_small = tkFont.Font(family="Poppins", size=10)

    # --- Card ---
    card = tk.Frame(app.content_frame, width=420, height=280, bg=LIGHT_CARD_BG)
    card.pack(pady=(30, 20))
    card.pack_propagate(False)

    # --- Title ---
    tk.Label(card, text="OTP Verification", font=font_title, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 10))

    # --- Info Text ---
    tk.Label(card, text=f"Enter the 6-digit code sent to {email_from_step1}",
             font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 15))

    # --- OTP Entry ---
    app.otp_entry = tk.Entry(card, font=font_text, width=20, justify="center")
    app.otp_entry.pack(ipady=6, pady=(0, 10))

    # --- Error Label ---
    app.otp_error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    app.otp_error_label.pack(pady=(0, 10))

    # --- Send Code ---
    def send_code():
        email = app.user_email_for_otp
        try:
            success, message = send_otp(email)
            if success:
                messagebox.showinfo("OTP Sent", message)
            else:
                app.otp_error_label.config(text=message)
        except Exception as e:
            err_msg = f"❌ Error sending OTP: {e}"
            app.otp_error_label.config(text=err_msg)
            messagebox.showerror("Error", err_msg)

    tk.Button(card, text="Send Code", font=font_small, command=send_code, bg="#F5F5F5").pack(pady=(0, 10))

    # --- Verify ---
    def verify_otp_ui():
        otp = app.otp_entry.get()
        try:
            success = verify_otp(otp)
            if not success:
                app.otp_error_label.config(text="Invalid or expired OTP. Please try again.")
                return

            messagebox.showinfo("Success", "OTP verified successfully!")

            # ✅ NOW register the user (email is verified)
            try:
                save_response = app.api.register_user(app.new_enrollment_data)
            except Exception as e:
                messagebox.showerror("Enrollment Failed", f"Could not save user data: {e}")
                return

            if not save_response or save_response.get("status") != "success":
                messagebox.showerror("Enrollment Failed", save_response.get("message", "Could not save user data."))
                return

            # ✅ Enroll voice now that the user exists
            username = app.new_enrollment_data.get("username")
            audio_path = app.pending_voice_file
            if not username or not audio_path or not os.path.exists(audio_path):
                messagebox.showerror("Error", "Voice recording not found for enrollment.")
                return

            resp = app.api.enroll_voice(username, audio_path)
            if not resp or resp.get("status") != "success":
                messagebox.showerror("Enrollment Failed", resp.get("message", "Voice enrollment failed."))
                return

            # → Proceed to Step 4 (file upload)
            show_enrollment_step4_file_upload(app)

        except Exception as e:
            err_msg = f"❌ Error verifying OTP: {e}"
            app.otp_error_label.config(text=err_msg)
            messagebox.showerror("Error", err_msg)

    # Rounded button (using your existing helper style)
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG); wrapper.pack(pady=0)
        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0,
                           relief="flat", cursor="hand2")
        canvas.pack()
        x1, y1, x2, y2 = 2, 2, width-2, height-2
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)
        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=app.font_normal)
        def on_click(_):
            if command: command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)
        return wrapper

    button_wrapper = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    button_wrapper.pack(pady=(0, 30))
    create_rounded_button(button_wrapper, "Verify OTP", command=verify_otp_ui)

def show_enrollment_step4_file_upload(app):
    """STEP 4: First locked file (enrollment: allow exactly one)."""
    import tkinter.filedialog as fd
    LIGHT_CARD_BG = "#AD567C"

    # Reset content
    for w in app.content_frame.winfo_children():
        w.destroy()

    app.enrollment_state = 'step4_file_upload'
    font_title  = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_normal = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=760, height=360, bg=LIGHT_CARD_BG)
    card.pack(pady=24)
    card.pack_propagate(False)

    tk.Label(card, text="STEP 4: Lock your Files", font=font_title, fg="white", bg=LIGHT_CARD_BG)\
        .pack(anchor="w", pady=(20, 6), padx=28)

    tk.Label(card, text="Only one file can be locked during enrollment. You can add and delete later in Manage Files.",
             font=font_normal, fg="white", bg=LIGHT_CARD_BG, justify="left", wraplength=640)\
        .pack(anchor="w", pady=(0, 10), padx=28)

    controls = tk.Frame(card, bg=LIGHT_CARD_BG)
    controls.pack(fill="x", padx=28, pady=(6, 6))

    # Selected path label
    path_var = tk.StringVar(value="No file/folder selected")
    if getattr(app, "selected_lock_path", None):
        path_var.set(os.path.normpath(app.selected_lock_path))

    tk.Label(controls, textvariable=path_var, anchor="w",
             font=font_normal, fg="white", bg=LIGHT_CARD_BG, wraplength=680, justify="left")\
        .pack(fill="x", pady=(0, 10))

    row = tk.Frame(controls, bg=LIGHT_CARD_BG)
    row.pack(fill="x")

    def _set_selection(p: str | None):
        app.selected_lock_path = p
        if p:
            path_var.set(os.path.normpath(p))
            finish_btn.config(state="normal")
        else:
            path_var.set("No file/folder selected")
            finish_btn.config(state="disabled")

    def _choose_file():
        p = fd.askopenfilename(title="Select a file to lock")
        if p:
            _set_selection(p)

    def _choose_folder():
        p = fd.askdirectory(title="Select a folder to lock")
        if p:
            _set_selection(p)

    btn_style = dict(font=font_normal, relief="flat",
                     bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
                     padx=14, pady=8, highlightthickness=1, highlightbackground="#ffffff", highlightcolor="#ffffff")

    tk.Button(row, text="Upload File",   command=_choose_file,   **btn_style).pack(side="left", padx=(0, 10))
    # tk.Button(row, text="Upload Folder", command=_choose_folder, **btn_style).pack(side="left", padx=(10, 0))

    # Bottom bar
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=48, pady=(8, 12))

    tk.Button(bf, text="< Back", font=font_normal,
              bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
              relief="flat", padx=12, pady=6,
              command=lambda: show_enrollment_step3_otp(app)).pack(side="left")

    dots_frame = tk.Frame(bf, bg=bf.cget('bg')); dots_frame.pack(side="left", padx=16)
    tk.Label(dots_frame, image=app.dot_empty_img,  bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img,  bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img,  bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)

    finish_btn = tk.Button(
        bf, text="Finish Enrollment", font=font_normal,
        bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
        relief="flat", padx=12, pady=6,
        state=("normal" if getattr(app, "selected_lock_path", None) else "disabled"),
        command=lambda: finalize_file_lock_and_finish(app)
    )
    finish_btn.pack(side="right")  # <-- this was missing earlier

def finalize_file_lock_and_finish(app):
    """
    Enrollment Step 4 finalizer:
    - Allows only ONE file during enrollment.
    - MOVES the selected file into keyvoxUserFiles/<username>/
    - Appends metadata to backend/user_files_db/<username>.json
    - Shows summary on success.
    """
    import os
    from tkinter import messagebox
    # Safe import (works whether you import as backend.module or module)
    try:
        from backend.locked_files_store import load_locked_files, add_and_move_file
    except Exception:
        from locked_files_store import load_locked_files, add_and_move_file

    username = (getattr(app, "new_enrollment_data", {}) or {}).get("username")
    if not username:
        messagebox.showerror("Error", "Missing username for enrollment.")
        return

    # Only one file during enrollment
    try:
        existing = load_locked_files(username) or []
    except Exception as e:
        messagebox.showerror("Error", f"Could not load locked files: {e}")
        return

    if len(existing) >= 1:
        messagebox.showwarning(
            "Limit",
            "Only one file can be locked during enrollment.\nYou can add/delete more later in Manage Files."
        )
        return

    # Ensure a selection exists
    sel_path = getattr(app, "selected_lock_path", None)
    if not sel_path or not os.path.isfile(sel_path):
        messagebox.showwarning("Missing", "Please select a file to lock.")
        return

    # MOVE the file and append metadata
    try:
        add_and_move_file(username, sel_path)
    except Exception as e:
        messagebox.showerror("Save Failed", f"Could not save locked file: {e}")
        return

    # Done
    show_enrollment_summary(app)

def show_enrollment_summary(app):
    LIGHT_CARD_BG = "#AD567C"
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=11)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30); card.pack_propagate(False)

    tk.Label(card, text="Enrollment Process Complete", font=font_title, fg="white", bg=LIGHT_CARD_BG)\
        .grid(row=0, column=0, columnspan=2, sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="You've successfully enrolled. Your credentials are now securely registered.",
             font=font_text, fg="white", bg=LIGHT_CARD_BG, justify="left", wraplength=600)\
        .grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 25), padx=40)

    summary_data = {
        "Full Name:": app.new_enrollment_data.get('full_name'),
        "Username:": app.new_enrollment_data.get('username'),
        "Password:": '******',
        "Email:": app.new_enrollment_data.get('email'),
        "Voice Pattern:": "Saved"
    }
    for i, (label, value) in enumerate(summary_data.items()):
        tk.Label(card, text=label, font=font_text, fg="white", bg=LIGHT_CARD_BG)\
            .grid(row=i + 2, column=0, sticky="w", pady=5, padx=40)
        tk.Label(card, text=value, font=font_text, fg="white", bg=LIGHT_CARD_BG)\
            .grid(row=i + 2, column=1, sticky="w", pady=5, padx=20)

    tk.Button(card, text="Finish", font=font_button, bg=config.BUTTON_LIGHT_COLOR,
              fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=30, pady=5,
              command=app._finish_enrollment)\
        .grid(row=len(summary_data) + 2, column=0, columnspan=2, pady=30)

def finish_enrollment(app):
    messagebox.showinfo("Success", "New user enrollment complete! Please log in.")
    app.just_enrolled_username = app.new_enrollment_data.get("username")
    app.just_enrolled = True
    app.enrollment_state = 'not_started'
    app.show_home_screen()
