# HomeyPro MCP Server

A Model Context Protocol (MCP) server for interacting with HomeyPro home automation systems. This server provides paginated access to devices, zones, and flows with comprehensive management capabilities.

## Features

- **Device Management**: List, search, and control devices with full capability support
- **Zone Management**: Browse zones and their associated devices
- **Flow Management**: List and trigger automation flows
- **System Management**: Get and update system configuration (location, address, language, units)
- **AI-Powered Prompts**: Context-aware guidance for device control, troubleshooting, and automation
- **Resource Caching**: Efficient data access with intelligent caching and stale data fallback
- **Pagination Support**: Efficient handling of large datasets with cursor-based pagination
- **Real-time Data**: Get current device states, capabilities, and insights
- **Error Handling**: Comprehensive error handling with detailed error messages

## Installation

### Local Development

1. Clone the repository and navigate to the project directory:
```bash
cd python-homey-mcp
```

2. Install dependencies using uv:
```bash
uv sync
```

### Docker

Pull the pre-built Docker image:

```bash
docker pull ghcr.io/pigmej/python-homey-mcp:latest
```

No additional installation steps are required when using Docker.

## Configuration

Before running the server, you need to configure your HomeyPro connection:

### Environment Variables

Set the following environment variables:

```bash
export HOMEY_API_URL="http://YOUR_HOMEY_IP_ADDRESS"
export HOMEY_API_TOKEN="YOUR_PERSONAL_ACCESS_TOKEN"
```

### Getting Your HomeyPro Token

1. Open the HomeyPro web interface
2. Go to Settings > General > API
3. Create a new Personal Access Token
4. Copy the token and set it as the `HOMEY_API_TOKEN` environment variable

### Finding Your HomeyPro IP Address

You can find your HomeyPro's IP address in:
- HomeyPro web interface: Settings > General > Network
- Your router's admin panel
- HomeyPro mobile app: More > Settings > General > Network

## Usage

### Running the Server

#### Local Development

```bash
uv run fastmcp run -t http --host 0.0.0.0 -p 4445 -l DEBUG main.py
```

#### Docker Container

Run the MCP server in a Docker container:

```bash
docker run -p 4445:4445 \
  -e HOMEY_API_URL="http://YOUR_HOMEY_IP_ADDRESS" \
  -e HOMEY_API_TOKEN="YOUR_PERSONAL_ACCESS_TOKEN" \
  ghcr.io/pigmej/python-homey-mcp:latest
```

Or using docker-compose:

```yaml
version: '3.8'
services:
  python-homey-mcp:
    image: ghcr.io/pigmej/python-homey-mcp:latest
    ports:
      - "4445:4445"
    environment:
      - HOMEY_API_URL=http://YOUR_HOMEY_IP_ADDRESS
      - HOMEY_API_TOKEN=YOUR_PERSONAL_ACCESS_TOKEN
```

The server will start and connect to your HomeyPro instance. You'll see a connection confirmation message. But basically please yield to [FastMCP docs](https://gofastmcp.com/patterns/cli)

## AI-Powered Prompts

The server provides context-aware prompts that help you interact with your HomeyPro system more effectively. These prompts analyze your current system state and provide tailored guidance.

### Available Prompts

#### Device Control Assistant
Provides structured guidance for controlling different types of devices in your HomeyPro system.
- **Context**: Current device counts, online/offline status, available device types
- **Guidance**: Control patterns for lighting, climate, security, and entertainment devices
- **Best Practices**: Device status checking, capability usage, troubleshooting tips

#### Device Troubleshooting
Systematic diagnostic guidance for common HomeyPro device issues.
- **System Health**: Overall device health percentage and status indicators
- **Step-by-Step Process**: Structured troubleshooting workflow
- **Device-Specific**: Targeted solutions for offline and unresponsive devices
- **Advanced Diagnostics**: Network, performance, and system-level troubleshooting

#### Device Capability Explorer
Helps you discover and understand device capabilities without overwhelming detail.
- **Capability Categories**: Control, sensor, and status capabilities
- **Value Types**: Boolean, numeric, string, and enum capability formats
- **Usage Patterns**: Common capability combinations and best practices
- **Device Type Patterns**: Capability patterns for different device categories

#### Flow Creation Assistant
Structured guidance for creating HomeyPro automation flows.
- **Flow Framework**: WHEN (trigger), AND (conditions), THEN (actions) structure
- **Common Scenarios**: Security, comfort, energy, convenience, and safety automations
- **System Context**: Available zones, device types, and existing flows
- **Templates**: Ready-to-use flow templates for common use cases

#### Flow Optimization
Guidance for improving existing flow performance and reliability.
- **Performance Analysis**: Flow execution patterns and optimization opportunities
- **Resource Usage**: Device and system resource considerations
- **Best Practices**: Flow organization, naming, and maintenance strategies

#### Flow Debugging
Systematic approach to diagnosing and fixing flow issues.
- **Common Problems**: Flow execution failures, timing issues, device conflicts
- **Diagnostic Tools**: Log analysis, condition testing, action verification
- **Resolution Strategies**: Step-by-step debugging workflow

#### System Health Check
Comprehensive system health analysis and recommendations.
- **Health Indicators**: Device connectivity, flow status, system performance
- **Status Overview**: Connection status, system configuration, resource usage
- **Recommendations**: Maintenance suggestions and optimization opportunities

#### Zone Organization
Guidance for organizing and optimizing zone structure.
- **Zone Planning**: Logical grouping strategies for devices and areas
- **Hierarchy Management**: Parent-child zone relationships
- **Device Assignment**: Best practices for device-to-zone mapping

### Prompt Features

- **Context-Aware**: All prompts analyze your current system state
- **Real-Time Data**: Information is based on current device and system status
- **Graceful Degradation**: Prompts work even when HomeyPro is temporarily unavailable
- **Error Handling**: Clear error messages with suggested actions
- **Actionable Guidance**: Practical steps you can take immediately

## Resource Caching

The server provides intelligent resource caching with automatic fallback to stale data when HomeyPro is temporarily unavailable.

### Available Resources

#### System Overview (`homey://system/overview`)
Comprehensive system overview including device counts, zone counts, and health indicators.
- **Content**: Device statistics, zone summary, system health percentage
- **Cache TTL**: 5 minutes
- **Use Case**: Dashboard displays, system monitoring, health checks

#### Device Registry (`homey://devices/registry`)
Complete device inventory with current states, capabilities, and online/offline indicators.
- **Content**: Full device list with capabilities, states, and metadata
- **Cache TTL**: 30 seconds (dynamic data)
- **Use Case**: Device management interfaces, capability discovery, status monitoring

#### Zone Hierarchy (`homey://zones/hierarchy`)
Zone structure with device associations and parent-child relationships.
- **Content**: Zone tree, device assignments, zone types and statistics
- **Cache TTL**: 5 minutes
- **Use Case**: Zone management, device organization, spatial automation

#### Flow Catalog (`homey://flows/catalog`)
Available flows with metadata, status, and execution statistics.
- **Content**: Flow list with triggers, conditions, actions, and execution data
- **Cache TTL**: 2 minutes
- **Use Case**: Flow management, automation analysis, debugging

### Caching Features

- **Intelligent TTL**: Different cache durations based on data volatility
- **Stale Data Fallback**: Returns cached data when HomeyPro is unreachable
- **Error Handling**: Graceful degradation with detailed error information
- **Connection Resilience**: Continues operation during network issues
- **Performance Optimization**: Reduces API calls and improves response times

### Cache Behavior

1. **Fresh Data**: Returns current data when cache is valid and HomeyPro is accessible
2. **Stale Data**: Returns cached data with staleness indicators when HomeyPro is unreachable
3. **Error Response**: Returns structured error information when no cached data is available
4. **Automatic Refresh**: Cache automatically refreshes when HomeyPro becomes available again

## API Tools

The server provides comprehensive API tools for direct HomeyPro interaction. All tools support pagination and error handling with detailed responses.

### Device Tools

#### Device Discovery and Information
- **`list_devices`**: List all devices with pagination support
  - Optional compact mode for reduced data transfer
  - Excludes hidden devices automatically
  - Includes online/offline status for each device

- **`get_device`**: Get detailed information about a specific device
  - Complete device details including capabilities and settings
  - Capability values and detailed configuration
  - Energy information and UI settings

- **`get_devices_classes`**: List all available device classes
  - Useful for understanding device types before searching
  - Returns complete list of supported device categories

- **`get_devices_capabilities`**: List all possible device capabilities
  - Comprehensive capability reference
  - Essential for understanding control options

#### Device Search and Filtering
- **`search_devices_by_name`**: Search devices by name with pagination
  - Fuzzy matching against device names
  - Includes note field information for context
  - Supports pagination for large result sets

- **`search_devices_by_class`**: Search devices by class/type
  - Filter devices by specific categories (lights, sensors, etc.)
  - Paginated results with metadata

#### Device Control and Monitoring
- **`control_device`**: Control device capabilities
  - Set capability values (on/off, dimming, temperature, etc.)
  - JSON value parsing with fallback handling
  - Returns current device state after control

- **`get_device_insights`**: Get historical device data
  - Multiple time resolutions (hour, day, week, month)
  - Custom timestamp ranges supported
  - Capability-specific insights and trends

### Zone Tools

#### Zone Management
- **`list_zones`**: List all zones with pagination
  - Complete zone hierarchy information
  - Parent-child relationships included

- **`get_zone_devices`**: Get all devices in a specific zone
  - Zone-based device filtering
  - Compact mode option for performance
  - Online/offline status per device

#### Zone Monitoring
- **`get_zone_temp`**: Get average temperature for a zone
  - Automatically averages temperature sensors in the zone
  - Handles zones without temperature sensors gracefully

### Flow Tools

#### Unified Flow Management
- **`list_flows`**: List all flows (both normal and advanced) with pagination
  - Automatically combines normal and advanced flows
  - Each flow includes a `flow_type` field ("normal" or "advanced")
  - Complete flow metadata and configuration
  - Seamless pagination across combined results

- **`trigger_flow`**: Execute any flow (automatically detects type)
  - Automatically detects whether flow is normal or advanced
  - Manual flow triggering with unified interface
  - Success confirmation with flow details and type

- **`get_flow_folders`**: Get all flow organization folders
  - Flow organization structure
  - Folder hierarchy for better management

- **`get_flows_by_folder`**: Get flows in a specific folder
  - Folder-based flow filtering
  - Organizational flow management

- **`get_flows_without_folder`**: Get unorganized flows
  - Find flows that need organization
  - Cleanup and maintenance assistance

#### Flow Organization
- **`get_flow_folders`**: Get all flow organization folders
  - Flow organization structure
  - Folder hierarchy for better management

- **`get_flows_by_folder`**: Get flows in a specific folder
  - Folder-based flow filtering
  - Organizational flow management
  - Note: Only returns normal flows in folder

- **`get_flows_without_folder`**: Get unorganized flows
  - Find flows that need organization
  - Cleanup and maintenance assistance
  - Note: Only returns normal flows without folder

### System Tools

#### System Information
- **`get_system_info`**: Get comprehensive system overview
  - Connection status and system health
  - Device, zone, and flow counts
  - Online/offline device statistics
  - Flow status (enabled/disabled/broken)
  - System configuration (address, language, units)
  - Location coordinates and regional settings
  - Recommended as first call before other operations

### Tool Features

#### Pagination Support
- **Cursor-based pagination**: Efficient handling of large datasets
- **Configurable page sizes**: Optimize for your use case
- **Total count tracking**: Know the full dataset size
- **Next page indicators**: Easy navigation through results

#### Data Formats
- **Compact mode**: Reduced data transfer for performance
- **Full detail mode**: Complete information when needed
- **JSON value handling**: Automatic parsing with fallbacks
- **Error responses**: Structured error information with details

#### Performance Optimization
- **Hidden device filtering**: Automatic exclusion of system devices
- **Efficient queries**: Optimized API calls to HomeyPro
- **Connection reuse**: Persistent connections for better performance
- **Graceful degradation**: Continues operation during partial failures

#### Error Handling
- **Detailed error messages**: Clear problem descriptions
- **Connection status**: Network and API health indicators
- **Fallback responses**: Graceful handling of API failures
- **Logging integration**: Comprehensive error tracking

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.