
# ✅ SMB File Sharing on macOS (for Testing File Transfers)

Use this guide to share a directory between two MacBooks over your local Wi-Fi network using **SMB file sharing** — great for testing file transfer apps.

---

## 🖥️ 1. Enable File Sharing on the Source Mac

1. Go to **System Settings** → **General** → **Sharing**
2. Toggle **File Sharing** to **ON**
3. Click the **ⓘ (Info)** button next to File Sharing
4. Under **Shared Folders**, click **+** and add the folder you want to share
5. Under **Users**, set access permissions (e.g., Read/Write)
6. Click **Options…**
   - Ensure **“Share files and folders using SMB”** is checked
   - Enable your user account under **Windows File Sharing**
   - Enter your password if prompted

---

## 🌐 2. Find Your Mac’s Local IP Address

Open Terminal and run:

```bash
ipconfig getifaddr en0
```

This returns your Wi-Fi IP (e.g., `192.168.1.23`)

---

## 💻 3. Connect from the Other Mac

1. In **Finder**, press **Cmd + K** or go to **Go → Connect to Server**
2. Enter:

   ```
   smb://<SOURCE_MAC_IP>
   ```

   Example:
   ```
   smb://192.168.1.23
   ```

3. Click **Connect**
4. Enter the **username and password** of the source Mac
5. Select the shared folder and mount it

---

## 🛠️ Tips for Local Testing

- ✅ Ensure both Macs are on the **same Wi-Fi network**
- ✅ Turn off or configure firewalls to allow SMB
  - System Settings → Network → Firewall → Options → **Allow File Sharing**
- ✅ Use `ping <other-mac-ip>` to verify network visibility

---

## 🔄 Optional: Make It Easier Next Time

- Create a desktop alias to the mounted share
- Add the share to **Login Items** to auto-connect
