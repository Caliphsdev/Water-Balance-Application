# Alerts Quick Reference Guide

## 🚀 Quick Start

### Accessing Alerts
**Settings → ⚠️ Alerts Tab**

### Alert Summary (Top Section)
- **🚨 Critical**: Red - Immediate action needed
- **⚠️ Warning**: Yellow - Attention required  
- **ℹ️ Info**: Blue - Informational only

## 📋 Common Tasks

### Check Current Alerts
1. Navigate to **Settings** → **⚠️ Alerts**
2. View summary counts at top
3. Scroll through active alerts list

### Acknowledge an Alert
1. Select alert in table
2. Click **✅ Acknowledge Selected**
3. Alert stays active but marked as "seen"

### Resolve an Alert
1. Select alert in table
2. Click **✔️ Resolve Selected**
3. Confirm resolution
4. Alert removed from active list

### Enable/Disable Alert Rule
1. Scroll to "Alert Rules Configuration"
2. Select a rule
3. Click **🔄 Toggle Enable/Disable**

## 🎯 Default Alert Rules

| Alert | Trigger | Action Required |
|-------|---------|-----------------|
| 🚨 **Critical Storage** | < 3 days cover | Order water immediately |
| 🚨 **Low Level Alarm** | < 10% facility level | Check facility, add water |
| ⚠️ **Low Storage** | < 7 days cover | Plan water procurement |
| ⚠️ **Minimum Level** | < 5 days to minimum | Monitor closely, prepare action |
| ⚠️ **High Storage** | > 90% utilization | Consider discharge options |
| ⚠️ **High Error** | > 5% closure error | Review calculations, check data |
| ℹ️ **Excellent Security** | > 30 days cover | Good position maintained |

## 💡 Tips

### Alert Response Priority
1. **Critical** - Respond within hours
2. **Warning** - Respond within 1-2 days  
3. **Info** - Review when convenient

### Reduce Alert Noise
- Acknowledge alerts you're working on
- Clear resolved alerts regularly (🗑️ Clear All Resolved)
- Disable rules that aren't relevant to your operation

### Auto-Resolution
Alerts automatically resolve when conditions improve:
- Storage increases above threshold → Alert auto-resolves
- Facility level rises → Alert auto-resolves
- Error rate drops → Alert auto-resolves

## 🔍 When to Disable Rules

Consider disabling a rule if:
- It triggers too frequently for your normal operations
- The threshold doesn't match your operational needs
- You have alternative monitoring for that metric

**Note**: Disabled rules can be re-enabled anytime!

## ⚡ Keyboard Shortcuts (Future)
Coming soon:
- `Ctrl+A` - Acknowledge selected
- `Ctrl+R` - Resolve selected
- `F5` - Refresh alerts

## 📞 Need Help?
See **ALERT_SYSTEM.md** for complete documentation.
