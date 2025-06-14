import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import os
from collections import defaultdict
import inspect
import yaml

ADMIN_USERS = ["admin"]
CREDENTIALS_FILE = "user_credentials.yaml"
current_credentials = {}

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_credentials(creds: dict) -> None:
    with open(CREDENTIALS_FILE, "w") as f:
        yaml.safe_dump(creds, f)

st.set_page_config(layout="wide")


def setup_authenticator():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            file_creds = yaml.safe_load(f) or {}
        usernames = file_creds.get("usernames", [])
        names = file_creds.get("names", [])
        hashed_passwords = file_creds.get("hashed_passwords", [])
    elif "auth" in st.secrets:
        creds = st.secrets["auth"]
        usernames = creds.get("usernames", [])
        names = creds.get("names", [])
        hashed_passwords = creds.get("hashed_passwords", [])
    else:
        usernames = os.getenv("AUTH_USERNAMES", "").split(",") if os.getenv("AUTH_USERNAMES") else []
        names = os.getenv("AUTH_NAMES", "").split(",") if os.getenv("AUTH_NAMES") else []
        hashed_passwords = os.getenv("AUTH_HASHED_PASSWORDS", "").split(",") if os.getenv("AUTH_HASHED_PASSWORDS") else []

    if not (usernames and names and hashed_passwords):
        usernames = ["admin", "hannah", "wendy"]
        names = ["Admin", "Hannah", "Wendy"]
        hashed_passwords = [
            "$2b$12$zXvvOuoI9xdg9qvhptMXQew0AXl6I4h77OWD20biQImrnZ2Yze0h.",
            "$2b$12$rLVuAJgX6cHIdJ1bl4DP3eALX0rOv.lzRGMh1ukM6oP.TZStBJHcW",
            "$2b$12$Zx9lY2bKf7kqjTR5IduUw.OTqT6Ybvv8y7ggcZk0OeWUM/OE/Ig2m",
        ]
        st.warning("Using default demo credentials. Set your own via secrets or environment variables.")

    credentials = {
        usernames[i]: {
            "name": names[i],
            "password": hashed_passwords[i],
        }
        for i in range(
            min(len(usernames), len(names), len(hashed_passwords))
        )
    }

    global current_credentials
    current_credentials = {
        "usernames": usernames,
        "names": names,
        "hashed_passwords": hashed_passwords,
    }
    if not os.path.exists(CREDENTIALS_FILE):
        save_credentials(current_credentials)

    authenticator = stauth.Authenticate(
        {"usernames": credentials}, "timetable_auth", "abcdef", cookie_expiry_days=1
    )
    return authenticator


def perform_login(auth):
    """Handle Authenticate.login across library versions."""
    try:
        params = inspect.signature(auth.login).parameters
    except (TypeError, ValueError):
        params = {}

    if "form_name" in params and "location" in params:
        return auth.login(form_name="Login", location="main")

    if params and next(iter(params)) == "location":
        try:
            return auth.login("main", "Login")
        except TypeError:
            return auth.login("main")

    return auth.login("Login", location="main")


def admin_page():
    st.title("Admin")
    creds = load_credentials()
    usernames = creds.get("usernames", [])
    names = creds.get("names", [])
    hashed_passwords = creds.get("hashed_passwords", [])

    with st.form("add_user"):
        new_user = st.text_input("Username")
        new_name = st.text_input("Display Name")
        new_pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Add User")
    if submitted:
        if not (new_user and new_name and new_pw):
            st.error("All fields required")
        elif new_user in usernames:
            st.error("User already exists")
        else:
            usernames.append(new_user)
            names.append(new_name)
            hashed_passwords.append(stauth.Hasher.hash(new_pw))
            save_credentials({
                "usernames": usernames,
                "names": names,
                "hashed_passwords": hashed_passwords,
            })
            st.success(f"Added {new_user}")

    if usernames:
        st.subheader("Delete User")
        to_delete = st.selectbox("Select", usernames)
        if st.button("Delete"):
            idx = usernames.index(to_delete)
            usernames.pop(idx)
            names.pop(idx)
            hashed_passwords.pop(idx)
            save_credentials({
                "usernames": usernames,
                "names": names,
                "hashed_passwords": hashed_passwords,
            })
            st.success(f"Deleted {to_delete}")


# --- Call it here ---
authenticator = setup_authenticator()
# In some versions of `streamlit-authenticator` the first positional argument of
# `login` represents the location of the login form rather than its title.
# Pass an explicit form name and use the `location` keyword so the call works
# across package versions and ensures the form is displayed in the main area.
# The function can return ``None`` if an unexpected version of the library is
# installed, so guard against that before unpacking.
login_data = perform_login(authenticator)
if login_data is None:
    # Fallback to session state values when perform_login returns None
    name = st.session_state.get("name")
    authentication_status = st.session_state.get("authentication_status")
else:
    try:
        name, authentication_status, _ = login_data
    except ValueError:
        # Some versions of streamlit-authenticator return two values
        name, authentication_status = login_data


if authentication_status is False:
    st.error("Username/password is incorrect")
    st.stop()
elif authentication_status is None:
    st.warning("Please enter your username and password")
    st.stop()
else:
    st.success(f"Welcome, {name} 👋")

    authenticator.logout("Logout", "sidebar")

    pages = ["Home"]
    if name in ADMIN_USERS:
        pages.append("Admin")
    choice = st.sidebar.radio("Navigation", pages)
    if choice == "Admin":
        admin_page()
        st.stop()


st.title("TA Timetable Assignment")

# Functions to load and save TA preference data

PREF_FILE = "saved_preferences.csv"


def load_preferences():
    if os.path.exists(PREF_FILE):
        return pd.read_csv(PREF_FILE)
    return pd.DataFrame(columns=["Year Group", "Subject", "TA Name"])


def save_preferences(df):
    df.to_csv(PREF_FILE, index=False)


uploaded_file = st.file_uploader("Upload the TA Timetable Excel File", type=["xlsx"])
if uploaded_file:
    timetable_df = pd.read_excel(uploaded_file, sheet_name="Timetable")
    availability_df = pd.read_excel(uploaded_file, sheet_name="Availability")
    excel_preferences_df = pd.read_excel(uploaded_file, sheet_name="Preferences")

    saved_preferences_df = load_preferences()

    all_preferences_df = pd.concat(
        [saved_preferences_df, excel_preferences_df], ignore_index=True
    )
    all_preferences_df.drop_duplicates(
        subset=["Year Group", "Subject", "TA Name"], inplace=True
    )

    st.subheader("Set TA Preferences")
    ta_name = st.selectbox(
        "Select TA", sorted(availability_df["TA Name"].dropna().unique())
    )
    selected_years = st.multiselect(
        "Select Year Groups (leave blank for all)",
        sorted(timetable_df["Year Group"].dropna().unique()),
    )
    selected_subjects = st.multiselect(
        "Select Subjects (leave blank for all)",
        sorted(timetable_df["Subject"].dropna().unique()),
    )

    if st.button("Add Preferences"):
        years = selected_years if selected_years else [None]
        subjects = selected_subjects if selected_subjects else [None]
        new_prefs = pd.DataFrame(
            [(y, s, ta_name) for y in years for s in subjects],
            columns=["Year Group", "Subject", "TA Name"],
        )
        all_preferences_df = all_preferences_df[
            ~(
                (all_preferences_df["TA Name"] == ta_name)
                & (
                    all_preferences_df["Year Group"].isin(years)
                    | all_preferences_df["Year Group"].isna()
                )
                & (
                    all_preferences_df["Subject"].isin(subjects)
                    | all_preferences_df["Subject"].isna()
                )
            )
        ]
        all_preferences_df = pd.concat(
            [all_preferences_df, new_prefs], ignore_index=True
        )
        all_preferences_df.drop_duplicates(
            subset=["Year Group", "Subject", "TA Name"], inplace=True
        )
        save_preferences(all_preferences_df)
        st.success("Preferences saved and cleaned up!")
        st.rerun()

    st.dataframe(all_preferences_df)

    st.subheader("Assign Individual Preferences (click-to-set)")
    full_years = timetable_df["Year Group"].dropna().unique()
    full_subjects = timetable_df["Subject"].dropna().unique()
    ta_list = sorted(availability_df["TA Name"].dropna().unique())

    placeholder_prefs = pd.DataFrame(
        [(y, s) for y in full_years for s in full_subjects],
        columns=["Year Group", "Subject"],
    )
    merged = pd.merge(
        placeholder_prefs, all_preferences_df, how="left", on=["Year Group", "Subject"]
    )
    grouped = merged.sort_values(["Year Group", "Subject"])

    for yg in sorted(grouped["Year Group"].unique()):
        with st.expander(f"{yg} Preferences", expanded=False):
            subset = grouped[grouped["Year Group"] == yg].copy()
            for idx, row in subset.iterrows():
                if pd.isna(row["TA Name"]):
                    ta_choice = st.selectbox(
                        f"{row['Subject']} ({row['Year Group']})",
                        ["None"] + ta_list,
                        key=f"{row['Year Group']}_{row['Subject']}_assign",
                    )
                    if ta_choice != "None":
                        new_row = pd.DataFrame(
                            [[row["Year Group"], row["Subject"], ta_choice]],
                            columns=["Year Group", "Subject", "TA Name"],
                        )
                        all_preferences_df = all_preferences_df[
                            ~(
                                (all_preferences_df["Year Group"] == row["Year Group"])
                                & (all_preferences_df["Subject"] == row["Subject"])
                            )
                        ]
                        all_preferences_df = pd.concat(
                            [all_preferences_df, new_row], ignore_index=True
                        )
                        save_preferences(all_preferences_df)
                        st.rerun()

    st.subheader("Edit/Delete Preferences")
    if not all_preferences_df.empty:
        pref_index = st.number_input(
            "Row index to delete",
            min_value=0,
            max_value=len(all_preferences_df) - 1,
            step=1,
        )
        if st.button("Delete Selected Row"):
            all_preferences_df.drop(all_preferences_df.index[pref_index], inplace=True)
            all_preferences_df.reset_index(drop=True, inplace=True)
            save_preferences(all_preferences_df)
            st.success("Preference deleted!")
            st.rerun()

    timetable_df = timetable_df.dropna(
        subset=["Year Group", "Subject", "Day", "Period"]
    )
    timetable_df["Slot"] = timetable_df["Day"] + " " + timetable_df["Period"]
    timetable_df["Assigned TA"] = ""

    duplicates = availability_df[availability_df["TA Name"].duplicated(keep=False)][
        "TA Name"
    ].unique()
    if len(duplicates) > 0:
        st.error(
            "Duplicate TA names found in Availability sheet: "
            f"{', '.join(sorted(map(str, duplicates)))}. "
            "Please ensure each TA appears only once."
        )
        st.stop()

    availability_lookup = (
        availability_df.set_index("TA Name").replace("\u2713", True).fillna(False)
    )
    ta_assignment_count = defaultdict(int)

    def is_available(ta, slot):
        try:
            return bool(availability_lookup.loc[ta, slot])
        except KeyError:
            return False
        except Exception:
            return False

    def assign_best_ta(year, subject, slot):
        preferences = all_preferences_df[
            (
                (all_preferences_df["Year Group"].isna())
                | (all_preferences_df["Year Group"] == year)
            )
            & (
                (all_preferences_df["Subject"].isna())
                | (all_preferences_df["Subject"] == subject)
            )
        ]
        preferred_tas = preferences["TA Name"].tolist()

        valid_preferred = [
            ta
            for ta in preferred_tas
            if ta in availability_lookup.index
            and is_available(ta, slot)
            and timetable_df[
                (timetable_df["Slot"] == slot) & (timetable_df["Assigned TA"] == ta)
            ].empty
        ]

        consistency_preferred = [
            ta
            for ta in valid_preferred
            if not timetable_df[
                (timetable_df["Year Group"] == year)
                & (timetable_df["Subject"] == subject)
                & (timetable_df["Assigned TA"] == ta)
            ].empty
        ]

        if consistency_preferred:
            return min(consistency_preferred, key=lambda t: ta_assignment_count[t])
        if valid_preferred:
            return min(valid_preferred, key=lambda t: ta_assignment_count[t])

        available_tas = [
            ta
            for ta in availability_lookup.index
            if is_available(ta, slot)
            and timetable_df[
                (timetable_df["Slot"] == slot) & (timetable_df["Assigned TA"] == ta)
            ].empty
        ]
        if available_tas:
            return min(available_tas, key=lambda t: ta_assignment_count[t])

        return "⚠ No TA available"

    for idx, row in timetable_df.iterrows():
        year = row["Year Group"]
        subject = row["Subject"]
        slot = row["Slot"]

        assigned_ta = assign_best_ta(year, subject, slot)
        timetable_df.at[idx, "Assigned TA"] = assigned_ta
        if assigned_ta and not assigned_ta.startswith("⚠"):
            ta_assignment_count[assigned_ta] += 1

    st.subheader("Assigned Timetable")
    st.dataframe(
        timetable_df[["Year Group", "Subject", "Day", "Period", "Assigned TA"]]
    )

    st.download_button(
        "Download Updated Timetable",
        data=timetable_df.to_csv(index=False).encode("utf-8"),
        file_name="TA_Assigned_Timetable.csv",
        mime="text/csv",
    )

    st.subheader("Unassigned or Conflicted Slots")
    unassigned = timetable_df[timetable_df["Assigned TA"].str.contains("⚠")]
    st.dataframe(unassigned)

    st.subheader("TA Load Summary")
    ta_summary = pd.DataFrame.from_dict(
        ta_assignment_count, orient="index", columns=["Assigned Periods"]
    )
    ta_summary.index.name = "TA Name"
    st.dataframe(ta_summary.reset_index())
