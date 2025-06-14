TA Timetable App - README
==========================

Overview:
---------
This Streamlit app automatically allocates teaching assistants (TAs) to timetable slots based on their availability and subject/year group preferences. Users can upload a formatted Excel file, set TA preferences, and download an updated timetable.

Excel File Requirements:
-------------------------
Your Excel file **must include the following three sheets** (named exactly as below):

1. **Timetable**
2. **Availability**
3. **Preferences**

Each sheet should follow the structure outlined below:

---

1. Timetable Sheet:
-------------------
| Year Group | Subject   | Day    | Period |
|------------|-----------|--------|--------|
| Year 7     | English   | Monday | P1     |
| Year 8     | Maths     | Tuesday| P2     |
| ...        | ...       | ...    | ...    |

- "Day" should be a string like "Monday", "Tuesday", etc.
- "Period" should be a unique string like "P1", "P2", etc.

---

2. Availability Sheet:
----------------------
| TA Name | Monday P1 | Monday P2 | Tuesday P1 | ... |
|---------|-----------|-----------|------------|-----|
| Alice   | ✓         |           | ✓          | ... |
| Bob     | ✓         | ✓         |            | ... |

- Columns after "TA Name" should match the format: "Day Period" (e.g., "Monday P1")
- Use ✓ to indicate a TA is available for that slot.
- Leave blank if unavailable.

---

3. Preferences Sheet:
---------------------
| Year Group | Subject   | TA Name |
|------------|-----------|---------|
| Year 7     | English   | Alice   |
| Year 8     | Maths     | Bob     |

- You can leave Year Group or Subject blank if a TA is happy to work across all.
- These preferences are optional and editable in the app.

---

Authentication Setup:
---------------------
Provide your own login details through a `.streamlit/secrets.toml` file or environment variables.

Example `secrets.toml`:
```
[auth]
usernames = ["user1", "user2"]
names = ["User One", "User Two"]
hashed_passwords = ["<hash1>", "<hash2>"]
```

Environment variable alternative:
- `AUTH_USERNAMES="user1,user2"`
- `AUTH_NAMES="User One,User Two"`
- `AUTH_HASHED_PASSWORDS="<hash1>,<hash2>"`

You can generate password hashes using `streamlit_authenticator.Hasher` in a Python shell.

---

Using the App:
--------------
1. Upload the formatted Excel file when prompted.
2. Review or set TA preferences using the dropdowns.
3. View the automatically assigned timetable.
4. Download the updated version or edit manually within the app.

Note: The app saves preferences to a local `saved_preferences.csv` file. This
file is ignored by Git, so create your own copy to keep preferences between runs.

---

For any issues or suggestions, feel free to raise an issue on this GitHub repository.

