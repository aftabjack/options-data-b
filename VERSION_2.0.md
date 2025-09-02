# Version 2.0 - Enhanced Options Tracker

## Release Date: September 2, 2025

## Major Features & Improvements

### 1. **Dynamic Asset Management**
- Assets now read from environment variables (`OPTION_ASSETS`)
- Automatic persistence of ETH and other configured assets
- Support for adding/removing assets through the UI
- Assets properly persist across application restarts

### 2. **Standardized Expiry Date Format**
- All expiry dates now use consistent 2-digit day format (e.g., "03SEP25" instead of "3SEP25")
- Proper chronological sorting of expiry dates
- Uniform format across all API endpoints and UI components
- Prevents data inconsistencies and filtering errors

### 3. **Column Visibility Controls**
- Added dropdown menu for showing/hiding table columns
- Persistent column preferences using localStorage
- Quick preset views (Trader View, Greeks Focus, etc.)
- Improved table readability and customization

### 4. **Performance Optimizations**
- Removed 500-item limitation in API responses
- Now displays all available options data (1,400+ contracts)
- Improved data fetching and rendering performance
- Better pagination support with configurable page sizes

### 5. **Enhanced Configuration System**
- Comprehensive GUI configuration file (`gui_config.json`)
- Support for custom column formats and descriptions
- Configurable display presets for different trading styles
- Better integration between environment variables and runtime config

## Technical Improvements

### Backend Changes
- Fixed Redis connection compatibility issues with macOS
- Improved WebSocket connection stability
- Better error handling and recovery mechanisms
- Standardized data formatting across all endpoints

### Frontend Enhancements
- Responsive design improvements
- Better data counter displays
- Enhanced dropdown menus with search functionality
- Improved real-time update handling

## Bug Fixes
- Fixed ETH not persisting between application restarts
- Resolved Redis socket_keepalive_options compatibility issue
- Fixed WebSocket subscription method errors
- Corrected data display limitations showing only partial data
- Fixed expiry date format inconsistencies

## Configuration Changes

### Environment Variables (.env)
```bash
OPTION_ASSETS=BTC,ETH,SOL  # Configurable asset list
REDIS_HOST=localhost        # Updated for local development
```

### Config File (config.yaml)
```yaml
tracker:
  assets:
    - "BTC"
    - "ETH"
    - "SOL"
```

## Breaking Changes
- Expiry date format changed from single-digit to double-digit days
- AssetManager class now reads from environment variables instead of hardcoded values

## Migration Guide

To upgrade from Version 1.0 to 2.0:

1. Update your `.env` file with the new `OPTION_ASSETS` variable
2. Clear Redis cache: `redis-cli FLUSHDB`
3. Restart both the tracker and web application
4. Column visibility preferences will be reset (users need to reconfigure)

## Files Modified
- `webapp/app_fastapi.py` - Major refactoring for asset management and date standardization
- `webapp/templates/dashboard.html` - Added column visibility controls
- `webapp/static/gui_config.json` - New configuration file for GUI settings
- `.env` - Updated environment variables
- `config.yaml` - Updated asset configuration
- `docker-compose.yml` - Updated service configurations

## Known Issues
- Deprecation warnings for FastAPI event handlers (will be addressed in next version)
- Manual asset additions through UI require restart to fully persist

## Future Enhancements (Planned for v2.1)
- Real-time asset addition without restart
- Advanced filtering and search capabilities
- Historical data tracking and analysis
- Export functionality for options data
- Mobile-responsive improvements

## Contributors
- Development and Implementation: Claude AI Assistant
- Project Owner: @aftabjack

## License
Same as Version 1.0

---

**Note**: This version maintains backward compatibility with existing Redis data structures while enhancing the overall functionality and user experience.