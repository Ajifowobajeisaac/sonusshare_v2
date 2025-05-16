# SonusShare Apple Music Integration: Challenges Overcome

## 1. MusicKit Authorization Fails Instantly ("Unauthorized")

**Symptom:**
- `musicKitInstance.authorize()` fails immediately, no popup appears.
- Console/log: `"Authorization failed"`, `"Unauthorized"`.

**Root Cause:**
- The Apple ID used for authorization did **not** have an active Apple Music subscription.

**Solution:**
- Subscribed to Apple Music with the test Apple ID.
- After subscribing, the authorization popup appeared as expected.

---

## 2. Authorization Popup Appears, But Main Window Not Updated

**Symptom:**
- After clicking "Allow" in the Apple Music popup, the popup redirects, but the main app window still shows "Not Authorized" and does not update.

**Root Cause:**
- The main window and popup could not communicate, often due to:
  - Mismatched or missing `origin` claim in the developer token.
  - Using different hostnames (e.g., `localhost` vs `127.0.0.1`).
  - Browser privacy settings or CORS issues.

**Solution:**
- Ensured the developer token's `origin` claim matched the exact domain and port used for testing.
- Used a single, consistent domain (e.g., always `127.0.0.1:8000`).
- Cleared cookies and local storage, restarted browser.

---

## 3. Race Condition: Button Clickable Before MusicKit Ready

**Symptom:**
- Clicking "Convert Selected Songs to Apple Music" sometimes resulted in:
  ```
  Failed to create Apple Music playlist: null is not an object (evaluating 'musicKitInstance.authorize')
  ```
- The button was enabled before MusicKit was initialized.

**Root Cause:**
- The button was enabled and the click handler was active before the `musickitloaded` event fired and `MusicKit.configure()` completed.

**Solution:**
- Disabled the button by default.
- Only enabled the button after MusicKit was initialized and `musicKitInstance` was set.
- Kept a null check in the click handler for extra safety.

---

## 4. Scoping Error: `musicKitInstance` is `null` in Click Handler

**Symptom:**
- Even after initialization, `musicKitInstance` was `null` in the click handler.
- Error:
  ```
  Failed to create Apple Music playlist: null is not an object (evaluating 'musicKitInstance.authorize')
  ```

**Root Cause:**
- `musicKitInstance` was declared in a different scope (e.g., inside a function or a different `<script>` block) than where it was used in the click handler.
- Multiple `<script>` blocks or redeclarations caused variable shadowing.

**Solution:**
- Declared `musicKitInstance` only once, at the top of the main script block.
- Ensured all MusicKit logic (initialization and click handler) shared the same variable scope.

---

## 5. MusicKit Not Found: ReferenceError for `waitForMusicKit` or `initializeMusicKit`

**Symptom:**
- Error:
  ```
  ReferenceError: Can't find variable: waitForMusicKit
  ```
  or
  ```
  ReferenceError: Can't find variable: initializeMusicKit
  ```

**Root Cause:**
- Functions were defined inside a block or after their use, or in a different `<script>` block, making them unavailable in the global scope when called.

**Solution:**
- Defined all MusicKit-related functions and variables in the same script block and scope.
- Ensured event listeners and function definitions were in the correct order.

---

## 6. MusicKit Not Loaded: Script Tag Placement

**Symptom:**
- MusicKit was not available in the main script, even though the script tag was present elsewhere.

**Root Cause:**
- The `<script src="https://js-cdn.music.apple.com/musickit/v3/musickit.js">` tag was not in the right place or block, so the main script executed before MusicKit was loaded.

**Solution:**
- Placed the MusicKit script tag in the correct `{% block extra_head %}` or at the top of the HTML, before any script that uses MusicKit.

---

## 7. General Best Practices Established

- Only call `MusicKit.configure()` once per page load.
- Always check for `musicKitInstance` before using it.
- Use the `musickitloaded` event to know when MusicKit is available.
- Keep all MusicKit logic in a single script block to avoid scoping issues.
- Disable UI elements until MusicKit is ready.
- Use consistent domains and correct developer token `origin` claims.

---

# Conclusion

Through these errors and solutions, SonusShare's Apple Music integration became robust and production-ready.  
This log can serve as a reference for future development, troubleshooting, and as the foundation for technical blog posts or documentation. 
