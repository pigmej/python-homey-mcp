# HomeyPro MCP Server

A Model Context Protocol (MCP) server for interacting with HomeyPro home automation systems. This server provides paginated access to devices, zones, and flows with comprehensive management capabilities.

## Features

- **Device Management**: List, search, and control devices with full capability support
- **Zone Management**: Browse zones and their associated devices
- **Flow Management**: List and trigger automation flows
- **System Management**: Get and update system configuration (location, address, language, units)
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


### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
