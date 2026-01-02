"""Constants for the Student Meetup Bot."""

# Conversation states
(
    HOMEPAGE,
    AWAITING_PHOTOS,
    AWAITING_UNIVERSITY,
    AWAITING_PROGRAM,
    AWAITING_BIO,
    EDIT_MENU,
    EDIT_PHOTOS,
    EDIT_UNIVERSITY,
    EDIT_PROGRAM,
    EDIT_BIO,
    BROWSING,  # New state for profile discovery
) = range(11)

# Button text constants
BTN_FILL_PROFILE = "📝 Fill Profile"
BTN_EDIT_PROFILE = "✏️ Edit Profile"
BTN_VIEW_PROFILE = "👤 View My Profile"
BTN_SEARCH = "🔍 Search"
BTN_BACK_HOME = "🔙 Back to Home"
BTN_DONE_PHOTOS = "✅ Done with Photos"
BTN_EDIT_PHOTOS = "📷 Photos"
BTN_EDIT_UNIVERSITY = "🏫 University"
BTN_EDIT_PROGRAM = "📚 Program"
BTN_EDIT_BIO = "📝 Bio"
BTN_CANCEL_EDITING = "❌ Cancel"

# Browse buttons
BTN_LIKE = "👍 Like"
BTN_PASS = "👎 Pass"
BTN_STOP_BROWSING = "🔙 Stop"
