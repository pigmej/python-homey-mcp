# HomeyPro MCP Server

A Model Context Protocol (MCP) server for interacting with HomeyPro home automation systems. This server provides paginated access to devices, zones, and flows with comprehensive management capabilities.

## Features

- **Device Management**: List, search, and control devices with full capability support
- **Zone Management**: Browse zones and their associated devices
- **Flow Management**: List and trigger automation flows
- **Pagination Support**: Efficient handling of large datasets with cursor-based pagination
- **Real-time Data**: Get current device states, capabilities, and insights
- **Error Handling**: Comprehensive error handling with detailed error messages

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd python-homey-mcp
```

2. Install dependencies using uv:
```bash
uv sync
```

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

```bash
python main.py
```

The server will start and connect to your HomeyPro instance. You'll see a connection confirmation message.

### Available Tools

#### Device Management

##### `list_devices`
List all devices with pagination support.

**Parameters:**
- `cursor` (optional): Pagination cursor for getting subsequent pages

**Returns:**
- `devices`: Array of device objects
- `pagination`: Pagination metadata including total count and next cursor

**Example:**
```python
# Get first page of devices
result = await list_devices()

# Get next page using cursor
result = await list_devices(cursor=result["pagination"]["next_cursor"])
```

##### `get_device`
Get detailed information about a specific device.

**Parameters:**
- `device_id`: The unique identifier of the device

**Returns:**
- `device`: Complete device object with capabilities and settings

##### `search_devices`
Search devices by name with pagination support.

**Parameters:**
- `query`: Search query to match against device names
- `cursor` (optional): Pagination cursor

**Returns:**
- `devices`: Array of matching device objects
- `query`: The search query used
- `pagination`: Pagination metadata

##### `control_device`
Control a device by setting a capability value.

**Parameters:**
- `device_id`: The unique identifier of the device
- `capability`: The capability to control (e.g., 'onoff', 'dim', 'target_temperature')
- `value`: The value to set for the capability

**Returns:**
- `success`: Boolean indicating success
- `current_value`: The current value after setting
- `device_name`: Name of the controlled device

**Example:**
```python
# Turn on a light
await control_device(device_id="light-123", capability="onoff", value=True)

# Set dimmer to 50%
await control_device(device_id="light-123", capability="dim", value=0.5)

# Set thermostat temperature
await control_device(device_id="thermostat-456", capability="target_temperature", value=21.5)
```

#### Zone Management

##### `list_zones`
List all zones with pagination support.

**Parameters:**
- `cursor` (optional): Pagination cursor

**Returns:**
- `zones`: Array of zone objects
- `pagination`: Pagination metadata

##### `get_zone_devices`
Get all devices in a specific zone with pagination support.

**Parameters:**
- `zone_id`: The unique identifier of the zone
- `cursor` (optional): Pagination cursor

**Returns:**
- `devices`: Array of device objects in the zone
- `zone_id`: The zone identifier
- `pagination`: Pagination metadata

#### Flow Management

##### `list_flows`
List all flows with pagination support.

**Parameters:**
- `cursor` (optional): Pagination cursor

**Returns:**
- `flows`: Array of flow objects
- `pagination`: Pagination metadata

##### `trigger_flow`
Trigger a specific flow.

**Parameters:**
- `flow_id`: The unique identifier of the flow to trigger

**Returns:**
- `success`: Boolean indicating success
- `flow_name`: Name of the triggered flow
- `flow_type`: Type of the flow

#### System Information

##### `get_system_info`
Get basic system information about the Homey instance.

**Returns:**
- `connection_status`: Connection status to HomeyPro
- `total_devices`: Total number of devices
- `online_devices`: Number of online devices
- `offline_devices`: Number of offline devices
- `total_zones`: Total number of zones
- `total_flows`: Total number of flows
- `enabled_flows`: Number of enabled flows
- `disabled_flows`: Number of disabled flows

##### `get_device_insights`
Get insights data for a specific device with pagination support.

**Parameters:**
- `device_id`: The unique identifier of the device
- `cursor` (optional): Pagination cursor

**Returns:**
- `insights`: Array of insight data points
- `device_id`: The device identifier
- `pagination`: Pagination metadata

## Pagination

This server implements cursor-based pagination to efficiently handle large datasets. All list operations support pagination with the following parameters:

### Cursor Format

Cursors are JSON-encoded strings containing:
- `offset`: Starting position in the dataset
- `page_size`: Number of items per page (default: 50, max: 100)

### Pagination Response

All paginated responses include a `pagination` object with:
- `total_count`: Total number of items available
- `page_size`: Number of items in the current page
- `offset`: Starting position of the current page
- `has_next`: Boolean indicating if more pages are available
- `next_cursor`: Cursor for the next page (null if no more pages)

### Example Pagination Usage

```python
# Get first page
result = await list_devices()
devices = result["devices"]

# Check if there are more pages
if result["pagination"]["has_next"]:
    # Get next page
    next_result = await list_devices(cursor=result["pagination"]["next_cursor"])
    more_devices = next_result["devices"]
```

## Error Handling

The server provides comprehensive error handling:

- **Connection Errors**: Issues connecting to HomeyPro
- **Authentication Errors**: Invalid token or permissions
- **Validation Errors**: Invalid device IDs, capability names, or values
- **Pagination Errors**: Invalid cursor format or parameters
- **API Errors**: HomeyPro API-specific errors

All errors are returned in a consistent format:
```json
{
  "error": "Detailed error message"
}
```

## Common Device Capabilities

Here are some common device capabilities you can control:

- `onoff`: Turn device on/off (boolean)
- `dim`: Dimmer level (0.0 to 1.0)
- `target_temperature`: Target temperature (number)
- `volume_set`: Volume level (0.0 to 1.0)
- `windowcoverings_set`: Window covering position (0.0 to 1.0)
- `alarm_motion`: Motion detection (boolean)
- `measure_temperature`: Current temperature (read-only)
- `measure_humidity`: Current humidity (read-only)
- `measure_power`: Current power consumption (read-only)

## Troubleshooting

### Connection Issues

1. **Check Network Connectivity**: Ensure your HomeyPro is accessible from your network
2. **Verify IP Address**: Confirm the `HOMEY_API_URL` is correct
3. **Check Token**: Ensure your Personal Access Token is valid and not expired
4. **Firewall Settings**: Check if any firewalls are blocking the connection

### Authentication Issues

1. **Token Expiry**: Personal Access Tokens may expire, generate a new one
2. **Token Permissions**: Ensure the token has the necessary permissions
3. **URL Format**: Ensure the base URL includes the protocol (http:// or https://)

### Performance Tips

1. **Use Pagination**: Always use pagination for large datasets
2. **Appropriate Page Sizes**: Use smaller page sizes for better performance
3. **Cache Results**: Cache frequently accessed data on the client side
4. **Batch Operations**: Group multiple operations when possible

## Development

### Dependencies

- `fastmcp>=2.10.2`: MCP server framework
- `python-homey`: HomeyPro API client library

### Project Structure

```
python-homey-mcp/
├── main.py          # Main MCP server implementation
├── pyproject.toml   # Project configuration
├── README.md        # This file
└── uv.lock         # Dependency lock file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.