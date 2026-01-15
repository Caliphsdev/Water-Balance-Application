# Installation Guide
## Water Balance Application

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **Processor**: Intel Core i3 or equivalent
- **Memory**: 4 GB RAM
- **Storage**: 500 MB available space
- **Display**: 1366x768 resolution

### Recommended Requirements
- **Operating System**: Windows 11 (64-bit)
- **Processor**: Intel Core i5 or better
- **Memory**: 8 GB RAM
- **Storage**: 1 GB available space
- **Display**: 1920x1080 resolution or higher

### Software Dependencies
- **Python**: 3.14+ (included in installer)
- **Internet Connection**: Required for license activation

---

## Installation Methods

### Method 1: Windows Installer (Recommended)

1. **Download** the latest installer:
   - `WaterBalanceSetup_v1.0.0.exe`

2. **Run the installer**:
   - Double-click the downloaded file
   - If prompted, click "Yes" to allow changes

3. **Follow the setup wizard**:
   - Accept the license agreement
   - Choose installation directory (default: `C:\Program Files\Water Balance`)
   - Select Start Menu folder
   - Choose to create desktop shortcut (recommended)

4. **Complete installation**:
   - Click "Install"
   - Wait for files to be copied
   - Click "Finish"

5. **First launch**:
   - The application will request license activation
   - Enter your license key
   - Click "Activate"

### Method 2: Portable Version

1. **Download** the portable package:
   - `WaterBalance_Portable_v1.0.0.zip`

2. **Extract** the archive:
   - Right-click → Extract All
   - Choose destination folder

3. **Run** the application:
   - Navigate to extracted folder
   - Double-click `WaterBalance.exe`

---

## License Activation

### Initial Activation

1. **Launch the application**
2. **License dialog appears automatically**
3. **Enter your license key** (format: `XXXX-XXXX-XXXX-XXXX`)
4. **Click "Activate"**
5. **Wait for verification** (requires internet)
6. **Confirmation message** displays remaining days

### Hardware Transfer

If moving to a new computer:

1. **On old computer**:
   - Open application
   - Go to Help → License Information
   - Click "Request Transfer"
   - Email sent to administrator

2. **On new computer**:
   - Install application
   - Enter license key
   - Activate normally

---

## Configuration

### First-Time Setup

1. **Data Source Configuration**:
   - Go to Settings → Data Sources
   - Configure Excel file path
   - Set Google Sheets credentials (if applicable)

2. **Area Configuration**:
   - Go to Settings → Areas
   - Activate required areas
   - Configure area-specific parameters

3. **Balance Check Settings**:
   - Go to Settings → Balance Check
   - Set tolerance levels
   - Configure alert thresholds

### Google Sheets Integration

1. **Obtain credentials**:
   - Contact your administrator
   - Request `credentials.json` file

2. **Place credentials**:
   - Copy `credentials.json` to `config/` folder

3. **Test connection**:
   - Go to Settings → Data Sources
   - Click "Test Connection"

---

## Uninstallation

### Windows Installer Version

1. **Open Windows Settings**
2. **Apps → Installed apps**
3. **Find "Water Balance Application"**
4. **Click "Uninstall"**
5. **Follow prompts**

### Portable Version

1. **Close application if running**
2. **Delete the application folder**
3. **Remove desktop shortcut (if created)**

---

## Troubleshooting Installation

### Installer won't run
- **Cause**: Windows SmartScreen protection
- **Solution**: Click "More info" → "Run anyway"

### License activation fails
- **Cause**: No internet connection
- **Solution**: Connect to internet and retry

### Application won't start
- **Cause**: Missing dependencies
- **Solution**: Reinstall using latest installer

### Database errors on first launch
- **Cause**: Corrupted installation
- **Solution**: Uninstall completely, delete app data folder, reinstall

---

## Post-Installation

### Verify Installation

1. **Launch application**
2. **Check version**: Help → About
3. **Verify license**: Help → License Information
4. **Load sample data**: File → Import Sample Data
5. **Run balance check**: Calculations → Run Balance Check

### Getting Started

1. **Read**: User Guide (docs/USER_GUIDE.md)
2. **Watch**: Tutorial videos (if available)
3. **Contact support**: For additional help

---

## Support

- **Email**: support@transafrica-resources.com
- **Documentation**: See README.md and docs/
- **Updates**: Check Help → Check for Updates

---

_Last updated: January 14, 2026_
