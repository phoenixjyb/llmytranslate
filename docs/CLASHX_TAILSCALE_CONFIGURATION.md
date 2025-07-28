# ClashX VPN Configuration for Tailscale Compatibility

## Issue Resolved
Previously, ClashX proxy was intercepting Tailscale traffic (100.x.x.x IP range), causing 502 Bad Gateway errors when accessing the translation service from Mac.

## Solution: ClashX Bypass Rules

Add the following rules to your ClashX configuration to bypass Tailscale IP ranges:

### Method 1: Using ClashX GUI
1. Open ClashX preferences
2. Go to "Rules" or "Config" section
3. Add bypass rules for Tailscale IP ranges:
   - `100.64.0.0/10` (Tailscale CGNAT range)
   - `fd7a:115c:a1e0::/48` (Tailscale IPv6 range)

### Method 2: Configuration File
Add these rules to your ClashX config.yaml:

```yaml
rules:
  # Bypass Tailscale IP ranges
  - IP-CIDR,100.64.0.0/10,DIRECT
  - IP-CIDR6,fd7a:115c:a1e0::/48,DIRECT
  
  # Specific rules for your setup (adjust as needed)
  - DOMAIN-SUFFIX,tailscale.com,DIRECT
  - DOMAIN-SUFFIX,tailscale.io,DIRECT
```

### Method 3: PAC File (if using PAC mode)
Add exclusions for Tailscale ranges in your PAC file:

```javascript
function FindProxyForURL(url, host) {
    // Bypass Tailscale IPs
    if (isInNet(host, "100.64.0.0", "255.192.0.0")) {
        return "DIRECT";
    }
    
    // Your other proxy rules...
    return "PROXY your-proxy-server:port";
}
```

## Testing
After applying these rules:
1. ✅ `curl http://100.104.28.77:8000/api/health` should work without `--noproxy` flag
2. ✅ Browser access to `http://100.104.28.77:8000` should work normally
3. ✅ No more 502 Bad Gateway errors

## Network Layout
- **Windows Service**: 100.104.28.77:8000 (Tailscale IP)
- **Mac Client**: 100.80.206.25 (Tailscale IP)
- **Regular Traffic**: Still proxied through ClashX
- **Tailscale Traffic**: Direct connection, bypassing proxy

## Date Resolved
July 28, 2025

## Benefits
- ✅ Seamless access to Tailscale services without manual proxy bypassing
- ✅ Normal proxy functionality preserved for internet traffic
- ✅ Browser and curl both work without special flags
- ✅ Permanent solution requiring no manual intervention
