"""Prompt-related tools for HomeyPro MCP Server."""

import time
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from ..client.manager import ensure_client
from ..utils.logging import get_logger
from ..mcp_instance import mcp

logger = get_logger(__name__)


@dataclass
class PromptContext:
    """Context data for prompts including system summaries."""

    system_info: Dict[str, Any]
    device_summary: Dict[str, Any]
    zone_summary: Dict[str, Any]
    flow_summary: Dict[str, Any]
    timestamp: str

    @classmethod
    def empty(cls) -> "PromptContext":
        """Create an empty context for fallback scenarios."""
        return cls(
            system_info={"connection_status": "unavailable"},
            device_summary={
                "total_count": 0,
                "online_count": 0,
                "has_device_types": False,
                "has_capabilities": False,
            },
            zone_summary={"total_count": 0, "zone_names": []},
            flow_summary={"total_count": 0, "enabled_count": 0, "has_flows": False},
            timestamp=datetime.now().isoformat(),
        )


async def get_prompt_context() -> PromptContext:
    """
    Generate lightweight system context for prompts.

    Creates summaries of devices, zones, flows, and system status without
    overwhelming detail. Handles connection failures gracefully by returning
    empty context.

    Returns:
        PromptContext with system summaries or empty context on failure
    """
    try:
        client = await ensure_client()

        # Get basic system data
        devices = await client.devices.get_devices()
        zones = await client.zones.get_zones()
        flows = await client.flows.get_flows()
        advanced_flows = await client.flows.get_advanced_flows()
        system_config = await client.system.get_system_config()

        # Create device summary without overwhelming detail
        online_devices = [d for d in devices if d.is_online()]
        device_classes: Set[str] = set()
        device_capabilities: Set[str] = set()

        for device in devices:
            if device.class_:
                device_classes.add(device.class_)
            if hasattr(device, "capabilities") and device.capabilities:
                device_capabilities.update(device.capabilities)

        device_summary = {
            "total_count": len(devices),
            "online_count": len(online_devices),
            "offline_count": len(devices) - len(online_devices),
            "has_device_types": len(device_classes) > 0,
            "device_type_count": len(device_classes),
            "has_capabilities": len(device_capabilities) > 0,
            "capability_count": len(device_capabilities),
            "sample_device_types": list(device_classes)[:10] if device_classes else [],
        }

        # Create zone summary
        zone_summary = {
            "total_count": len(zones),
            "zone_names": [z.name for z in zones if hasattr(z, "name") and z.name],
            "has_zones": len(zones) > 0,
        }

        # Create flow summary
        total_flows = len(flows) + len(advanced_flows)
        enabled_flows = await client.flows.get_enabled_flows()
        enabled_advanced_flows = await client.flows.get_enabled_advanced_flows()
        total_enabled = len(enabled_flows) + len(enabled_advanced_flows)

        flow_summary = {
            "total_count": total_flows,
            "enabled_count": total_enabled,
            "disabled_count": total_flows - total_enabled,
            "has_flows": total_flows > 0,
            "has_advanced_flows": len(advanced_flows) > 0,
        }

        # Create system info summary
        system_info = {
            "connection_status": "connected",
            "address": getattr(system_config, "address", "unknown"),
            "language": getattr(system_config, "language", "unknown"),
            "units": getattr(system_config, "units", "unknown"),
            "is_metric": system_config.is_metric()
            if hasattr(system_config, "is_metric")
            else False,
            "location_available": bool(
                getattr(system_config, "get_location_coordinates", lambda: None)()
            ),
        }

        return PromptContext(
            system_info=system_info,
            device_summary=device_summary,
            zone_summary=zone_summary,
            flow_summary=flow_summary,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        raise
        logger.warning(f"Failed to get prompt context: {e}")
        return PromptContext.empty()


@mcp.prompt()
async def device_control_assistant(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides structured guidance for controlling HomeyPro devices.

    This prompt helps users understand how to control different types of devices
    in their HomeyPro system, including available capabilities and common control
    patterns. It includes contextual information about the current system state.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for device control guidance
    """
    try:
        logger.debug("Generating device control assistant prompt")
        context = await get_prompt_context()

        prompt_template = f"""# HomeyPro Device Control Assistant

## Current System Status
- **Connection**: {context.system_info.get("connection_status", "unknown")}
- **Total Devices**: {context.device_summary.get("total_count", 0)}
- **Online Devices**: {context.device_summary.get("online_count", 0)}
- **Offline Devices**: {context.device_summary.get("offline_count", 0)}
- **Device Types Available**: {context.device_summary.get("device_type_count", 0)}
- **Capabilities Available**: {context.device_summary.get("capability_count", 0)}

## Device Control Guidance

### Getting Started
1. **List Available Devices**: Use the device listing tools to see all devices in your system
2. **Check Device Status**: Verify device online status before attempting control
3. **Identify Capabilities**: Each device has specific capabilities that determine what actions are possible

### Common Device Types and Control Patterns

#### Lighting Devices
- **Turn On/Off**: Use the `onoff` capability
- **Dimming**: Use the `dim` capability (0.0 to 1.0)
- **Color Control**: Use `light_hue`, `light_saturation`, `light_temperature` capabilities
- **Example**: "Turn on bedroom light to 50% brightness"

#### Climate Control
- **Temperature**: Use `target_temperature` capability
- **Mode Control**: Use `thermostat_mode` capability (heat, cool, auto, off)
- **Example**: "Set living room thermostat to 22°C in heating mode"

#### Security Devices
- **Motion Sensors**: Read `alarm_motion` capability
- **Door/Window Sensors**: Read `alarm_contact` capability
- **Cameras**: Use device-specific capabilities for recording/streaming

#### Entertainment Devices
- **Volume Control**: Use `volume_set` capability
- **Power Control**: Use `onoff` capability
- **Input Selection**: Use device-specific input capabilities

### Control Best Practices
1. **Check Device Status First**: Always verify a device is online before sending commands
2. **Use Appropriate Values**: Respect capability value ranges (e.g., 0.0-1.0 for dimming)
3. **Handle Errors Gracefully**: Some devices may not respond immediately
4. **Group Similar Actions**: Use zones to control multiple devices efficiently

### Available Device Types in Your System
{", ".join(context.device_summary.get("sample_device_types", [])) if context.device_summary.get("sample_device_types") else "No device types detected"}

### Zone-Based Control
Your system has {context.zone_summary.get("total_count", 0)} zones configured:
{", ".join(context.zone_summary.get("zone_names", [])) if context.zone_summary.get("zone_names") else "No zones configured"}

Use zone-based control to manage multiple devices simultaneously within the same area.

### Troubleshooting Tips
- If a device doesn't respond, check its online status
- Verify the capability exists before using it
- Some devices may have delays in status updates
- Check device-specific documentation for special requirements

---
*System context generated at: {context.timestamp}*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate device control assistant prompt: {e}")
        return f"""# HomeyPro Device Control Assistant

## Error
Unable to generate contextual device control guidance due to system connectivity issues.

## Basic Device Control Guidance
1. Use device listing tools to see available devices
2. Check device online status before control attempts
3. Identify device capabilities to understand available actions
4. Use appropriate value ranges for each capability
5. Handle connection errors gracefully

Please check your HomeyPro connection and try again.

Error details: {str(e)}
"""


@mcp.prompt()
async def device_troubleshooting(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides structured guidance for diagnosing common HomeyPro device issues.

    This prompt helps users systematically troubleshoot device problems by
    providing step-by-step diagnostic guidance and system health indicators.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for device troubleshooting guidance
    """
    try:
        logger.debug("Generating device troubleshooting prompt")
        context = await get_prompt_context()

        # Calculate system health indicators
        total_devices = context.device_summary.get("total_count", 0)
        online_devices = context.device_summary.get("online_count", 0)
        offline_devices = context.device_summary.get("offline_count", 0)

        health_percentage = (
            (online_devices / total_devices * 100) if total_devices > 0 else 0
        )
        health_status = (
            "Good"
            if health_percentage >= 90
            else "Warning"
            if health_percentage >= 70
            else "Critical"
        )

        prompt_template = f"""# HomeyPro Device Troubleshooting Guide

## System Health Overview
- **Overall Health**: {health_status} ({health_percentage:.1f}% devices online)
- **Total Devices**: {total_devices}
- **Online Devices**: {online_devices}
- **Offline Devices**: {offline_devices}
- **Connection Status**: {context.system_info.get("connection_status", "unknown")}

## Step-by-Step Diagnostic Process

### Step 1: Identify the Problem
**Common Device Issues:**
- Device not responding to commands
- Device showing as offline
- Device capabilities not working
- Delayed or inconsistent responses
- Device missing from system

### Step 2: Basic System Checks
1. **Verify HomeyPro Connection**
   - Check if HomeyPro is accessible on the network
   - Verify internet connectivity if using cloud features
   - Restart HomeyPro if connection issues persist

2. **Check Device Power and Connectivity**
   - Ensure device has power (battery devices: check battery level)
   - For wireless devices: check signal strength
   - For wired devices: verify physical connections

### Step 3: Device-Specific Diagnostics

#### For Offline Devices ({offline_devices} currently offline)
1. **Power Cycle the Device**
   - Turn device off and on again
   - For battery devices: remove and reinsert batteries
   - Wait 30 seconds before testing

2. **Check Network Connectivity**
   - Verify device is within range of HomeyPro
   - Check for interference from other devices
   - Test with device closer to HomeyPro

3. **Re-pair if Necessary**
   - Remove device from HomeyPro
   - Follow manufacturer's pairing instructions
   - Add device back to system

#### For Unresponsive Devices (online but not working)
1. **Test Basic Capabilities**
   - Try simple on/off commands first
   - Test one capability at a time
   - Check if specific capabilities are failing

2. **Check Device Settings**
   - Verify device configuration in HomeyPro
   - Check if device firmware needs updating
   - Review any custom device settings

### Step 4: Advanced Troubleshooting

#### Network and Connectivity Issues
- **Z-Wave Devices**: Check Z-Wave network health and perform healing
- **Zigbee Devices**: Verify Zigbee network stability
- **Wi-Fi Devices**: Check Wi-Fi signal strength and network congestion
- **Infrared Devices**: Ensure clear line of sight and proper positioning

#### Performance Issues
- **Slow Response**: Check system load and network latency
- **Intermittent Failures**: Look for patterns (time of day, specific commands)
- **Multiple Device Issues**: May indicate HomeyPro system problems

### Step 5: System-Level Diagnostics

#### HomeyPro System Health
- **Memory Usage**: Check if system is running low on memory
- **Storage Space**: Verify adequate storage is available
- **App Conflicts**: Identify if specific apps are causing issues
- **System Updates**: Ensure HomeyPro firmware is up to date

#### Flow and Automation Impact
- **Flow Conflicts**: Check if flows are interfering with device control
- **Timing Issues**: Verify flow execution timing doesn't conflict
- **Logic Errors**: Review flow conditions and actions

### Step 6: Documentation and Reporting

#### Information to Gather
1. **Device Details**
   - Device type, model, and manufacturer
   - Firmware version and capabilities
   - Installation date and location

2. **Problem Description**
   - When the issue started
   - Frequency of the problem
   - Specific error messages or behaviors

3. **System Context**
   - Recent changes to system or network
   - Other devices affected
   - Environmental factors

#### Next Steps
- **Contact Support**: If issues persist after troubleshooting
- **Community Forums**: Search for similar issues and solutions
- **Device Manufacturer**: For device-specific problems
- **Professional Help**: For complex network or installation issues

### Quick Reference: Common Solutions

| Problem | Quick Fix |
|---------|-----------|
| Device offline | Power cycle device, check batteries |
| Slow response | Restart HomeyPro, check network |
| Commands ignored | Verify device capabilities, check flows |
| Pairing fails | Reset device, clear HomeyPro cache |
| Intermittent issues | Check for interference, update firmware |

### Zone-Specific Issues
Your zones: {", ".join(context.zone_summary.get("zone_names", [])) if context.zone_summary.get("zone_names") else "No zones configured"}

If multiple devices in the same zone are having issues, consider:
- Environmental factors (temperature, humidity, interference)
- Power supply problems in that area
- Network coverage issues in that location

---
*Diagnostic information generated at: {context.timestamp}*
*System health calculated based on current device status*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate device troubleshooting prompt: {e}")
        return f"""# HomeyPro Device Troubleshooting Guide

## Error
Unable to generate contextual troubleshooting guidance due to system connectivity issues.

## Basic Troubleshooting Steps
1. Check device power and connectivity
2. Verify HomeyPro system is accessible
3. Power cycle problematic devices
4. Check for network interference
5. Review recent system changes
6. Test with simple commands first
7. Re-pair devices if necessary

Please check your HomeyPro connection and try again for detailed diagnostics.

Error details: {str(e)}
"""


@mcp.prompt()
async def device_capability_explorer(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides guidance for understanding and utilizing HomeyPro device capabilities.

    This prompt helps users discover and understand device capabilities without
    overwhelming them with complete capability lists. It focuses on practical
    usage patterns and capability exploration strategies.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for device capability exploration guidance
    """
    try:
        logger.debug("Generating device capability explorer prompt")
        context = await get_prompt_context()

        prompt_template = f"""# HomeyPro Device Capability Explorer

## System Capability Overview
- **Total Devices**: {context.device_summary.get("total_count", 0)}
- **Device Types**: {context.device_summary.get("device_type_count", 0)} different types
- **Unique Capabilities**: {context.device_summary.get("capability_count", 0)} available
- **Sample Device Types**: {", ".join(context.device_summary.get("sample_device_types", [])) if context.device_summary.get("sample_device_types") else "None detected"}

## Understanding Device Capabilities

### What Are Capabilities?
Capabilities define what actions a device can perform or what information it can provide. Each device has a unique set of capabilities based on its type and manufacturer.

### Common Capability Categories

#### **Control Capabilities** (Actions you can perform)
- `onoff` - Turn devices on or off
- `dim` - Control brightness/intensity (0.0 to 1.0)
- `target_temperature` - Set desired temperature
- `volume_set` - Control audio volume
- `windowcoverings_set` - Control blinds/curtains position

#### **Sensor Capabilities** (Information devices provide)
- `measure_temperature` - Current temperature readings
- `measure_humidity` - Humidity percentage
- `measure_power` - Power consumption
- `alarm_motion` - Motion detection status
- `alarm_contact` - Door/window open/closed status

#### **Status Capabilities** (Device state information)
- `alarm_battery` - Low battery warnings
- `alarm_generic` - General alarm conditions
- `meter_power` - Cumulative power usage
- `measure_luminance` - Light level measurements

### Capability Discovery Process

#### Step 1: List Your Devices
Use device listing tools to see all devices in your system and their basic information.

#### Step 2: Examine Individual Devices
For each device of interest:
1. Check the device's available capabilities
2. Note the capability types (control vs. sensor)
3. Understand the value ranges and formats

#### Step 3: Test Capabilities Safely
1. **Read-Only First**: Start with sensor capabilities that only read data
2. **Simple Controls**: Test basic on/off or simple value changes
3. **Advanced Features**: Explore complex capabilities once basics work

### Capability Value Types and Ranges

#### **Boolean Capabilities**
- `true/false` values (e.g., onoff, alarm states)
- Example: `onoff: true` (device is on)

#### **Numeric Capabilities**
- **Percentage**: 0.0 to 1.0 (e.g., dim, volume_set)
- **Temperature**: Celsius or Fahrenheit based on system settings
- **Power**: Watts or kilowatts
- Example: `dim: 0.5` (50% brightness)

#### **String Capabilities**
- Text values for modes or states
- Example: `thermostat_mode: "heat"`

#### **Enum Capabilities**
- Predefined list of valid values
- Example: `windowcoverings_state: "up", "down", "idle"`

### Device Type Capability Patterns

#### **Lighting Devices**
Common capabilities: `onoff`, `dim`, `light_hue`, `light_saturation`, `light_temperature`
- Control brightness, color, and color temperature
- Some lights support scenes or effects

#### **Climate Devices**
Common capabilities: `target_temperature`, `measure_temperature`, `thermostat_mode`
- Set and monitor temperature
- Control heating/cooling modes

#### **Security Devices**
Common capabilities: `alarm_motion`, `alarm_contact`, `alarm_tamper`
- Detect motion, door/window status
- Provide security alerts

#### **Entertainment Devices**
Common capabilities: `onoff`, `volume_set`, `speaker_playing`, `speaker_track`
- Control playback and volume
- Manage audio content

### Capability Exploration Strategies

#### **Start with Familiar Devices**
1. Choose devices you use regularly
2. Explore their basic capabilities first
3. Gradually discover advanced features

#### **Group Similar Devices**
1. Find devices of the same type
2. Compare their capabilities
3. Understand common patterns

#### **Use Zone Context**
Your zones: {", ".join(context.zone_summary.get("zone_names", [])) if context.zone_summary.get("zone_names") else "No zones configured"}

Explore capabilities within specific zones to understand room-based automation possibilities.

### Advanced Capability Usage

#### **Capability Combinations**
- Use multiple capabilities together for complex control
- Example: Set light brightness AND color simultaneously

#### **Conditional Logic**
- Use sensor capabilities to trigger control capabilities
- Example: Turn on lights when motion is detected

#### **Value Monitoring**
- Track capability values over time
- Identify patterns and optimize automation

### Troubleshooting Capability Issues

#### **Capability Not Working**
1. Verify the capability exists for the device
2. Check if the device is online
3. Ensure you're using correct value types/ranges
4. Test with simple values first

#### **Unexpected Behavior**
1. Check device documentation for capability specifics
2. Verify value ranges and formats
3. Test capabilities individually before combining

#### **Missing Capabilities**
1. Some capabilities may be device-specific
2. Check if device firmware needs updating
3. Verify device is properly paired

### Best Practices for Capability Usage

1. **Always Check Device Status**: Ensure device is online before using capabilities
2. **Respect Value Ranges**: Use appropriate values for each capability type
3. **Test Incrementally**: Start simple, add complexity gradually
4. **Document Your Findings**: Keep notes on what works for each device
5. **Handle Errors Gracefully**: Not all devices respond immediately

### Getting Help

- **Device Documentation**: Check manufacturer specifications
- **HomeyPro Community**: Search for device-specific capability information
- **Experimentation**: Safe testing with read-only capabilities first
- **Support Resources**: Contact device manufacturer for capability questions

---
*Capability information generated at: {context.timestamp}*
*Based on {context.device_summary.get("total_count", 0)} devices in your system*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate device capability explorer prompt: {e}")
        return f"""# HomeyPro Device Capability Explorer

## Error
Unable to generate contextual capability exploration guidance due to system connectivity issues.

## Basic Capability Exploration
1. List all devices in your system
2. Examine individual device capabilities
3. Start with read-only sensor capabilities
4. Test simple control capabilities safely
5. Understand value types and ranges
6. Combine capabilities for advanced control

Common capability types:
- Control: onoff, dim, target_temperature
- Sensors: measure_temperature, alarm_motion
- Status: alarm_battery, meter_power

Please check your HomeyPro connection and try again for detailed capability information.

Error details: {str(e)}
"""


@mcp.prompt()
async def flow_creation_assistant(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides structured guidance for creating HomeyPro automation flows.

    This prompt helps users build automation flows by providing templates
    for trigger, condition, and action setup with context about available
    zones and device types in their system.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for flow creation guidance
    """
    try:
        logger.debug("Generating flow creation assistant prompt")
        context = await get_prompt_context()

        prompt_template = f"""# HomeyPro Flow Creation Assistant

## Current System Context
- **Total Devices**: {context.device_summary.get("total_count", 0)} ({context.device_summary.get("online_count", 0)} online)
- **Available Zones**: {context.zone_summary.get("total_count", 0)} zones
- **Existing Flows**: {context.flow_summary.get("total_count", 0)} ({context.flow_summary.get("enabled_count", 0)} enabled)
- **Device Types**: {", ".join(context.device_summary.get("sample_device_types", [])) if context.device_summary.get("sample_device_types") else "None detected"}

## Flow Creation Framework

### Understanding Flow Structure
Every HomeyPro flow consists of three main components:
1. **WHEN** (Trigger) - What starts the flow
2. **AND** (Conditions) - Optional conditions that must be met
3. **THEN** (Actions) - What happens when triggered

### Step 1: Define Your Automation Goal

#### Common Automation Scenarios
- **Security**: "Turn on lights when motion is detected at night"
- **Comfort**: "Adjust temperature when someone arrives home"
- **Energy**: "Turn off devices when no one is home"
- **Convenience**: "Start morning routine at sunrise"
- **Safety**: "Send notification if door is left open"

#### Questions to Ask Yourself
1. What event should trigger this automation?
2. Are there specific conditions when it should/shouldn't run?
3. What actions should happen when triggered?
4. Which devices and zones are involved?

### Step 2: Choose Your Trigger (WHEN)

#### **Time-Based Triggers**
- **Specific Time**: "At 7:00 AM on weekdays"
- **Sunrise/Sunset**: "30 minutes before sunset"
- **Interval**: "Every 15 minutes"

#### **Device-Based Triggers**
- **Motion Detection**: "When motion is detected in [zone]"
- **Door/Window**: "When front door opens"
- **Temperature**: "When temperature drops below 18°C"
- **Power Usage**: "When device power consumption changes"

#### **System-Based Triggers**
- **Presence**: "When someone arrives/leaves home"
- **Weather**: "When it starts raining"
- **App Events**: "When specific app condition is met"

#### **Manual Triggers**
- **Button Press**: "When physical button is pressed"
- **Voice Command**: "When voice command is spoken"
- **Mobile App**: "When flow is manually started"

### Step 3: Set Conditions (AND) - Optional but Powerful

#### **Time Conditions**
- "Only between 6 PM and 11 PM"
- "Only on weekdays"
- "Not during vacation mode"

#### **Device State Conditions**
- "Only if living room lights are off"
- "Only if no one is home"
- "Only if outdoor temperature is below 15°C"

#### **Logic Conditions**
- "AND all conditions must be true"
- "OR any condition can be true"
- "NOT condition must be false"

### Step 4: Define Actions (THEN)

#### **Device Control Actions**
- **Lighting**: Turn on/off, set brightness, change color
- **Climate**: Adjust temperature, change mode
- **Entertainment**: Play music, adjust volume
- **Security**: Arm/disarm, send notifications

#### **System Actions**
- **Notifications**: Send to phone, email, or other apps
- **Variables**: Set/change system variables
- **Other Flows**: Start or stop other flows
- **Delays**: Wait before next action

### Your System Resources

#### Available Zones
{", ".join(f"- {zone}" for zone in context.zone_summary.get("zone_names", [])) if context.zone_summary.get("zone_names") else "- No zones configured"}

Use zones to create location-based automations and control multiple devices in the same area.

#### Device Categories Available
{", ".join(f"- {device_type}" for device_type in context.device_summary.get("sample_device_types", [])) if context.device_summary.get("sample_device_types") else "- No device types detected"}

Consider how different device types can work together in your flows.

### Flow Creation Best Practices

#### **Start Simple**
1. Create basic flows first (single trigger, single action)
2. Test thoroughly before adding complexity
3. Add conditions and multiple actions gradually

#### **Use Descriptive Names**
- Good: "Turn on porch light at sunset"
- Bad: "Light flow 1"

#### **Consider Edge Cases**
- What if the device is offline?
- What if multiple triggers happen quickly?
- How to handle conflicting flows?

#### **Test and Iterate**
1. Enable the flow and monitor its behavior
2. Check flow execution logs for issues
3. Adjust timing, conditions, or actions as needed

### Common Flow Templates

#### **Security Flow Template**
```
WHEN: Motion detected in [zone]
AND: Time is between sunset and sunrise
AND: Security mode is enabled
THEN: Turn on [zone] lights to 100%
THEN: Send notification "Motion detected in [zone]"
THEN: Wait 5 minutes
THEN: Turn off [zone] lights
```

#### **Comfort Flow Template**
```
WHEN: Someone arrives home
AND: Time is after 5 PM
AND: Outdoor temperature is below 20°C
THEN: Set living room temperature to 22°C
THEN: Turn on welcome lights
THEN: Play favorite playlist
```

#### **Energy Saving Flow Template**
```
WHEN: No one is home for 30 minutes
AND: Time is between 8 AM and 6 PM
THEN: Turn off all non-essential lights
THEN: Lower thermostat by 3°C
THEN: Turn off entertainment devices
```

#### **Morning Routine Template**
```
WHEN: Time is 7:00 AM
AND: Day is Monday through Friday
AND: Someone is home
THEN: Gradually increase bedroom lights over 10 minutes
THEN: Start coffee maker
THEN: Play morning news
THEN: Set thermostat to comfort temperature
```

### Advanced Flow Techniques

#### **Flow Chaining**
- Use one flow to trigger another
- Create complex sequences with multiple flows
- Implement state machines with flow combinations

#### **Variable Usage**
- Store and use system state information
- Create counters and timers
- Share data between flows

#### **Error Handling**
- Add conditions to check device availability
- Create fallback actions for failed operations
- Use notifications to alert about flow issues

### Testing Your Flow

#### **Before Enabling**
1. Review all triggers, conditions, and actions
2. Check device availability and capabilities
3. Verify timing and logic make sense

#### **After Enabling**
1. Monitor flow execution in HomeyPro logs
2. Test manually if possible
3. Observe behavior over several days
4. Adjust based on real-world performance

### Troubleshooting Flow Issues

#### **Flow Not Triggering**
- Check if trigger conditions are being met
- Verify devices are online and responsive
- Review flow enable/disable status

#### **Flow Triggering Too Often**
- Add more specific conditions
- Implement delays or cooldown periods
- Check for conflicting triggers

#### **Actions Not Working**
- Verify target devices are online
- Check device capabilities and value ranges
- Test actions individually outside the flow

### Getting Help

- **Flow Logs**: Check HomeyPro flow execution logs
- **Community**: Search HomeyPro community for similar flows
- **Documentation**: Review device-specific flow capabilities
- **Testing**: Use manual flow triggers for debugging

---
*Flow creation guidance generated at: {context.timestamp}*
*Based on your system with {context.device_summary.get("total_count", 0)} devices across {context.zone_summary.get("total_count", 0)} zones*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate flow creation assistant prompt: {e}")
        return f"""# HomeyPro Flow Creation Assistant

## Error
Unable to generate contextual flow creation guidance due to system connectivity issues.

## Basic Flow Creation Steps
1. Define your automation goal clearly
2. Choose appropriate trigger (WHEN)
3. Add conditions if needed (AND)
4. Define actions to take (THEN)
5. Test the flow thoroughly
6. Monitor and adjust as needed

Flow Structure:
- WHEN: What starts the flow
- AND: Conditions that must be met (optional)
- THEN: Actions to perform

Please check your HomeyPro connection and try again for detailed flow creation guidance.

Error details: {str(e)}
"""


@mcp.prompt()
async def flow_optimization(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides guidance for improving existing HomeyPro automation flows.

    This prompt helps users optimize their automation flows by analyzing
    system performance indicators and providing best practices for
    flow efficiency and reliability.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for flow optimization guidance
    """
    try:
        logger.debug("Generating flow optimization prompt")
        context = await get_prompt_context()

        # Calculate flow performance indicators
        total_flows = context.flow_summary.get("total_count", 0)
        enabled_flows = context.flow_summary.get("enabled_count", 0)
        disabled_flows = context.flow_summary.get("disabled_count", 0)

        flow_efficiency = (enabled_flows / total_flows * 100) if total_flows > 0 else 0

        prompt_template = f"""# HomeyPro Flow Optimization Guide

## Current Flow Performance Overview
- **Total Flows**: {total_flows}
- **Enabled Flows**: {enabled_flows}
- **Disabled Flows**: {disabled_flows}
- **Flow Efficiency**: {flow_efficiency:.1f}% (enabled vs total)
- **System Devices**: {context.device_summary.get("total_count", 0)} ({context.device_summary.get("online_count", 0)} online)
- **Available Zones**: {context.zone_summary.get("total_count", 0)}

## Flow Optimization Framework

### Performance Analysis Checklist

#### **Flow Execution Efficiency**
1. **Review Flow Frequency**
   - Identify flows that trigger too often
   - Look for flows with very short intervals
   - Check for overlapping or conflicting flows

2. **Analyze Resource Usage**
   - Monitor flows that control many devices simultaneously
   - Identify flows with complex condition chains
   - Review flows with multiple API calls or external services

3. **Check Flow Dependencies**
   - Map flows that trigger other flows
   - Identify circular dependencies or flow loops
   - Review flow chains for unnecessary complexity

### Optimization Strategies

#### **Trigger Optimization**

##### **Time-Based Triggers**
- **Current Best Practice**: Use specific times instead of frequent intervals
- **Optimization**: Combine multiple time-based actions into single flows
- **Example**: Instead of 3 separate "every hour" flows, create one comprehensive hourly flow

##### **Device-Based Triggers**
- **Reduce Sensitivity**: Adjust motion sensor delays to prevent rapid triggering
- **Group Similar Triggers**: Combine multiple device triggers of the same type
- **Use Zone Logic**: Trigger on zone changes rather than individual devices

##### **System-Based Triggers**
- **Presence Detection**: Use geofencing instead of frequent location checks
- **Weather Triggers**: Use significant weather changes, not minor fluctuations
- **App Integration**: Minimize external API calls by caching data

#### **Condition Optimization**

##### **Simplify Logic Chains**
- **Before**: Multiple nested AND/OR conditions
- **After**: Streamlined condition sets with clear logic
- **Tip**: Use variables to store complex calculations

##### **Device State Checking**
- **Batch Checks**: Check multiple device states in single conditions
- **Cache Results**: Store frequently checked states in variables
- **Avoid Redundancy**: Don't check conditions that triggers already verify

##### **Time-Based Conditions**
- **Use Ranges**: "Between 6 PM and 11 PM" instead of multiple time checks
- **Day Logic**: Use day-of-week conditions efficiently
- **Season/Month**: Consider seasonal variations in automation needs

#### **Action Optimization**

##### **Device Control Actions**
- **Group Commands**: Send multiple commands to same device together
- **Zone Actions**: Control entire zones instead of individual devices
- **Stagger Timing**: Add small delays between high-power device activations

##### **Notification Actions**
- **Consolidate Messages**: Combine multiple notifications into summaries
- **Priority Levels**: Use different notification methods for different urgencies
- **Rate Limiting**: Prevent notification spam with cooldown periods

##### **Flow Control Actions**
- **Minimize Flow Chains**: Reduce flows that start other flows
- **Use Variables**: Share data between flows instead of triggering chains
- **Parallel Execution**: Design flows to run independently when possible

### System-Specific Optimizations

#### **Your Device Categories**
{", ".join(f"- {device_type}" for device_type in context.device_summary.get("sample_device_types", [])) if context.device_summary.get("sample_device_types") else "- No device types detected"}

##### **Lighting Optimization**
- Group lights by zone for simultaneous control
- Use scenes instead of individual device commands
- Implement gradual dimming instead of instant changes

##### **Climate Optimization**
- Use temperature ranges instead of exact values
- Implement seasonal scheduling
- Coordinate multiple climate devices to avoid conflicts

##### **Security Optimization**
- Combine multiple sensor inputs for more reliable detection
- Use time-based arming/disarming schedules
- Implement escalating response levels

#### **Your Zone Structure**
{", ".join(f"- {zone}" for zone in context.zone_summary.get("zone_names", [])) if context.zone_summary.get("zone_names") else "- No zones configured"}

##### **Zone-Based Flow Design**
- Create zone-specific flows instead of device-specific ones
- Use zone presence detection for more efficient automation
- Implement zone-to-zone flow coordination

### Performance Monitoring

#### **Flow Execution Metrics**
1. **Execution Time**: Monitor how long flows take to complete
2. **Success Rate**: Track failed vs successful flow executions
3. **Trigger Frequency**: Identify flows that run too often
4. **Resource Impact**: Monitor system load during flow execution

#### **System Health Indicators**
- **Device Response Time**: Slower responses may indicate system overload
- **Memory Usage**: High memory usage can slow flow execution
- **Network Performance**: Poor connectivity affects flow reliability
- **Error Rates**: Increasing errors suggest optimization needs

### Common Optimization Patterns

#### **Before and After Examples**

##### **Inefficient Security Flow**
```
BEFORE:
Flow 1: WHEN motion in living room THEN turn on living room light
Flow 2: WHEN motion in kitchen THEN turn on kitchen light
Flow 3: WHEN motion in hallway THEN turn on hallway light
```

```
AFTER:
Single Flow: WHEN motion in any zone THEN turn on lights in that zone
```

##### **Inefficient Morning Routine**
```
BEFORE:
Flow 1: WHEN 7:00 AM THEN start coffee
Flow 2: WHEN 7:05 AM THEN turn on lights
Flow 3: WHEN 7:10 AM THEN play music
```

```
AFTER:
Single Flow: WHEN 7:00 AM THEN start coffee, wait 5 min, turn on lights, wait 5 min, play music
```

##### **Inefficient Climate Control**
```
BEFORE:
Flow 1: WHEN temperature < 20°C THEN set heater to 22°C
Flow 2: WHEN temperature > 24°C THEN set heater to 20°C
```

```
AFTER:
Single Flow: WHEN temperature changes THEN maintain temperature between 20-24°C
```

### Advanced Optimization Techniques

#### **Variable Usage for Efficiency**
- **State Tracking**: Use variables to remember system states
- **Counters**: Track events to prevent excessive triggering
- **Timers**: Implement custom timing logic with variables
- **Flags**: Use boolean variables for complex condition management

#### **Flow Scheduling**
- **Peak Hours**: Schedule intensive flows during low-usage periods
- **Maintenance Windows**: Group system maintenance flows
- **Load Balancing**: Distribute flow execution across time periods

#### **Error Handling and Resilience**
- **Fallback Actions**: Provide alternative actions when primary ones fail
- **Retry Logic**: Implement smart retry mechanisms for failed actions
- **Graceful Degradation**: Design flows to work with partial system availability

### Optimization Maintenance

#### **Regular Review Schedule**
- **Weekly**: Check flow execution logs for errors or unusual patterns
- **Monthly**: Review flow performance metrics and system health
- **Quarterly**: Comprehensive flow audit and optimization review
- **Annually**: Major flow architecture review and redesign

#### **Performance Testing**
1. **Load Testing**: Test flows under various system load conditions
2. **Stress Testing**: Verify flow behavior with many simultaneous triggers
3. **Failure Testing**: Test flow behavior when devices are offline
4. **Integration Testing**: Verify flows work correctly with system updates

### Troubleshooting Optimization Issues

#### **Flow Performance Problems**
- **Slow Execution**: Check device response times and network connectivity
- **High Resource Usage**: Simplify complex condition chains
- **Frequent Failures**: Add error handling and device availability checks

#### **System Impact Issues**
- **System Slowdown**: Reduce flow frequency and complexity
- **Device Conflicts**: Coordinate flows that control same devices
- **Network Congestion**: Stagger flows that make external API calls

### Best Practices Summary

1. **Consolidate Similar Flows**: Combine flows with similar triggers or actions
2. **Use Appropriate Timing**: Match flow frequency to actual needs
3. **Implement Smart Conditions**: Use efficient logic to reduce unnecessary executions
4. **Monitor Performance**: Regularly review flow execution metrics
5. **Plan for Failures**: Include error handling and fallback mechanisms
6. **Document Changes**: Keep notes on optimization changes and their effects
7. **Test Thoroughly**: Verify optimizations don't break existing functionality

### Getting Help with Optimization

- **Flow Analytics**: Use HomeyPro's built-in flow monitoring tools
- **Community Resources**: Share optimization strategies with other users
- **Professional Support**: Consider expert consultation for complex systems
- **Incremental Changes**: Make small optimizations and measure their impact

---
*Flow optimization guidance generated at: {context.timestamp}*
*Analysis based on {total_flows} flows in your system with {flow_efficiency:.1f}% efficiency rate*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate flow optimization prompt: {e}")
        return f"""# HomeyPro Flow Optimization Guide

## Error
Unable to generate contextual flow optimization guidance due to system connectivity issues.

## Basic Flow Optimization Steps
1. Review flow execution frequency and performance
2. Consolidate similar or overlapping flows
3. Simplify complex condition chains
4. Optimize trigger sensitivity and timing
5. Group device actions for efficiency
6. Monitor system performance impact
7. Implement error handling and fallbacks

Key optimization areas:
- Trigger efficiency (reduce unnecessary executions)
- Action consolidation (group related commands)
- Condition simplification (streamline logic)
- Resource management (balance system load)

Please check your HomeyPro connection and try again for detailed optimization guidance.

Error details: {str(e)}
"""


@mcp.prompt()
async def flow_debugging(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides structured approach for troubleshooting HomeyPro flow issues.

    This prompt helps users systematically debug flow problems by providing
    diagnostic templates and system context for identifying common flow issues
    and their solutions.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for flow debugging guidance
    """
    try:
        logger.debug("Generating flow debugging prompt")
        context = await get_prompt_context()

        # Calculate system health indicators for debugging context
        total_flows = context.flow_summary.get("total_count", 0)
        enabled_flows = context.flow_summary.get("enabled_count", 0)
        total_devices = context.device_summary.get("total_count", 0)
        online_devices = context.device_summary.get("online_count", 0)
        offline_devices = context.device_summary.get("offline_count", 0)

        device_health = (
            (online_devices / total_devices * 100) if total_devices > 0 else 0
        )

        prompt_template = f"""# HomeyPro Flow Debugging Guide

## Current System Status for Debugging
- **Flow Status**: {enabled_flows}/{total_flows} flows enabled
- **Device Health**: {device_health:.1f}% ({online_devices}/{total_devices} devices online)
- **Offline Devices**: {offline_devices} (potential flow impact)
- **System Zones**: {context.zone_summary.get("total_count", 0)} configured
- **Connection Status**: {context.system_info.get("connection_status", "unknown")}

## Flow Debugging Framework

### Step 1: Problem Identification

#### **Common Flow Problems**
1. **Flow Not Triggering**
   - Flow appears inactive despite trigger conditions being met
   - No execution logs or activity indicators

2. **Flow Triggering Unexpectedly**
   - Flow runs when it shouldn't
   - Multiple unexpected executions

3. **Flow Actions Not Working**
   - Flow triggers but actions don't execute
   - Partial action execution

4. **Flow Performance Issues**
   - Slow execution or delays
   - System impact or resource problems

5. **Flow Logic Errors**
   - Incorrect behavior under certain conditions
   - Unexpected results from flow execution

### Step 2: Initial Diagnostic Checks

#### **System Health Verification**
1. **Check HomeyPro Connectivity**
   - Verify HomeyPro is accessible and responsive
   - Test basic system functions (device listing, zone access)
   - Check network connectivity and stability

2. **Device Status Review**
   - Verify all devices involved in the flow are online
   - Check device responsiveness and capability status
   - Test individual device control outside of flows

3. **Flow Status Confirmation**
   - Confirm the flow is enabled
   - Check flow modification timestamps
   - Verify flow hasn't been accidentally disabled

### Step 3: Detailed Flow Analysis

#### **Trigger Analysis**

##### **Time-Based Triggers**
- **Check System Time**: Verify HomeyPro system time is correct
- **Timezone Issues**: Confirm timezone settings match expectations
- **Schedule Conflicts**: Look for overlapping time-based flows
- **Daylight Saving**: Consider DST impacts on scheduling

**Debugging Steps:**
1. Test trigger manually if possible
2. Check system logs for trigger events
3. Verify time conditions are being met
4. Test with simplified time ranges

##### **Device-Based Triggers**
- **Device Connectivity**: Ensure trigger devices are online and responsive
- **Capability Status**: Verify trigger capabilities are working correctly
- **Sensor Sensitivity**: Check if sensor thresholds are appropriate
- **Signal Strength**: For wireless devices, verify good signal quality

**Debugging Steps:**
1. Test device trigger manually (e.g., activate motion sensor)
2. Check device logs for trigger events
3. Verify device capability values are changing as expected
4. Test with different devices of the same type

##### **System-Based Triggers**
- **Presence Detection**: Verify location services and geofencing
- **Weather Data**: Check weather service connectivity and data accuracy
- **App Integration**: Confirm third-party app connections are working
- **Variable Changes**: Verify system variables are updating correctly

**Debugging Steps:**
1. Test system trigger conditions manually
2. Check external service connectivity
3. Verify data sources are providing expected values
4. Test with simplified trigger conditions

#### **Condition Analysis**

##### **Logic Condition Issues**
- **AND/OR Logic**: Verify boolean logic is correct
- **Condition Order**: Check if condition sequence affects evaluation
- **Nested Conditions**: Simplify complex nested logic for testing
- **Variable Conditions**: Verify variables contain expected values

**Debugging Steps:**
1. Temporarily remove conditions to isolate issues
2. Test each condition individually
3. Log condition values during flow execution
4. Simplify complex logic chains

##### **Device State Conditions**
- **State Accuracy**: Verify device states are current and accurate
- **Timing Issues**: Check if device states change between trigger and condition check
- **Capability Values**: Confirm condition thresholds are appropriate
- **Device Availability**: Ensure condition devices are online

**Debugging Steps:**
1. Check device states manually before flow execution
2. Add logging to track device state changes
3. Test conditions with known device states
4. Verify condition logic matches intended behavior

##### **Time-Based Conditions**
- **Time Range Logic**: Verify time ranges are correctly specified
- **Day/Date Logic**: Check day-of-week or date-specific conditions
- **Duration Conditions**: Verify timing calculations are correct
- **Timezone Consistency**: Ensure all time conditions use same timezone

**Debugging Steps:**
1. Test time conditions at known times
2. Log current time values during condition evaluation
3. Test with simplified time ranges
4. Verify system time accuracy

#### **Action Analysis**

##### **Device Control Actions**
- **Device Availability**: Confirm target devices are online and responsive
- **Capability Support**: Verify devices support the requested actions
- **Value Ranges**: Check if action values are within device capability ranges
- **Command Conflicts**: Look for conflicting commands to same device

**Debugging Steps:**
1. Test device actions manually outside of flows
2. Check device response times and reliability
3. Verify action parameters are correct
4. Test actions individually before combining

##### **System Actions**
- **Notification Delivery**: Verify notification services are configured correctly
- **Variable Updates**: Check if system variables are being set correctly
- **Flow Control**: Verify start/stop flow actions are working
- **External Services**: Confirm third-party service integrations

**Debugging Steps:**
1. Test system actions independently
2. Check service configurations and credentials
3. Verify action parameters and formats
4. Monitor system logs for action execution

### Step 4: Advanced Debugging Techniques

#### **Flow Execution Logging**
1. **Enable Detailed Logging**: Turn on comprehensive flow logging
2. **Timestamp Analysis**: Track execution timing and delays
3. **Error Message Review**: Analyze specific error messages and codes
4. **Execution Path Tracking**: Follow flow execution through all steps

#### **Isolation Testing**
1. **Create Test Flows**: Build simplified versions to isolate problems
2. **Component Testing**: Test individual flow components separately
3. **Minimal Reproduction**: Create minimal flow that reproduces the issue
4. **Comparison Testing**: Compare working vs non-working similar flows

#### **System Resource Monitoring**
1. **Memory Usage**: Check if system memory affects flow execution
2. **CPU Load**: Monitor system load during flow execution
3. **Network Performance**: Verify network connectivity doesn't impact flows
4. **Storage Space**: Ensure adequate storage for logs and data

### Step 5: Common Problem Solutions

#### **Flow Not Triggering Solutions**
- **Trigger Sensitivity**: Adjust sensor sensitivity or thresholds
- **Timing Issues**: Add delays or adjust timing conditions
- **Device Pairing**: Re-pair problematic trigger devices
- **Flow Recreation**: Delete and recreate the flow from scratch

#### **Unexpected Triggering Solutions**
- **Condition Refinement**: Add more specific conditions to prevent false triggers
- **Cooldown Periods**: Implement delays between flow executions
- **Trigger Filtering**: Use more precise trigger criteria
- **Flow Scheduling**: Limit flow execution to specific time periods

#### **Action Failure Solutions**
- **Device Reset**: Power cycle or reset target devices
- **Command Sequencing**: Add delays between multiple device commands
- **Error Handling**: Implement fallback actions for failed commands
- **Alternative Methods**: Use different capabilities or approaches

### Step 6: Systematic Debugging Process

#### **Debugging Checklist**
1. **Document the Problem**: Record exact symptoms and conditions
2. **Gather System Info**: Collect relevant system and device status
3. **Review Recent Changes**: Check for recent system or flow modifications
4. **Test Components**: Verify each flow component works independently
5. **Simplify and Test**: Create minimal test cases to isolate issues
6. **Monitor and Log**: Enable logging and monitor flow execution
7. **Implement Solution**: Apply fixes and verify resolution
8. **Document Solution**: Record the fix for future reference

#### **Information to Collect**
- **Flow Configuration**: Complete flow setup including all conditions
- **Device Status**: Status of all devices involved in the flow
- **System Logs**: Relevant log entries around the time of issues
- **Timing Information**: When problems occur and their frequency
- **Environmental Factors**: Any external factors that might affect the flow

### Your System Context for Debugging

#### **Device Categories to Check**
{", ".join(f"- {device_type}" for device_type in context.device_summary.get("sample_device_types", [])) if context.device_summary.get("sample_device_types") else "- No device types detected"}

Focus debugging efforts on flows involving these device types, as they're present in your system.

#### **Zone-Based Debugging**
{", ".join(f"- {zone}" for zone in context.zone_summary.get("zone_names", [])) if context.zone_summary.get("zone_names") else "- No zones configured"}

Consider zone-specific issues when debugging flows that involve multiple zones or zone-based triggers.

### Prevention Strategies

#### **Flow Design Best Practices**
1. **Start Simple**: Begin with basic flows and add complexity gradually
2. **Test Thoroughly**: Test each component before combining
3. **Document Logic**: Keep clear notes on flow purpose and logic
4. **Regular Review**: Periodically review and update flows
5. **Monitor Performance**: Watch for degradation over time

#### **System Maintenance**
1. **Regular Updates**: Keep HomeyPro firmware and apps updated
2. **Device Health**: Monitor device connectivity and battery levels
3. **Network Stability**: Ensure reliable network connectivity
4. **Backup Flows**: Keep backups of working flow configurations

### Getting Help

#### **Resources for Complex Issues**
- **HomeyPro Logs**: Use built-in logging and diagnostic tools
- **Community Forums**: Search for similar issues and solutions
- **Developer Tools**: Use advanced debugging features if available
- **Professional Support**: Contact support for persistent issues

#### **When to Seek Help**
- Issues persist after systematic debugging
- System-wide problems affecting multiple flows
- Hardware or network-related problems
- Complex integration issues with third-party services

---
*Flow debugging guidance generated at: {context.timestamp}*
*System analysis based on {total_flows} flows and {total_devices} devices*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate flow debugging prompt: {e}")
        return f"""# HomeyPro Flow Debugging Guide

## Error
Unable to generate contextual flow debugging guidance due to system connectivity issues.

## Basic Flow Debugging Steps
1. Verify flow is enabled and properly configured
2. Check all involved devices are online and responsive
3. Test trigger conditions manually when possible
4. Review flow execution logs for errors
5. Simplify flow logic to isolate problems
6. Test individual components separately
7. Check for recent system or device changes

Common debugging areas:
- Trigger conditions not being met
- Device connectivity and responsiveness
- Logic condition evaluation
- Action execution and device control
- Timing and scheduling issues

Please check your HomeyPro connection and try again for detailed debugging guidance.

Error details: {str(e)}
"""


@mcp.prompt()
async def zone_organization(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides best practices template for organizing zones and devices in HomeyPro.

    This prompt helps users efficiently organize their zones and devices by
    providing guidance for zone management, device assignment, and optimization
    strategies based on their current zone structure.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for zone organization guidance
    """
    try:
        logger.debug("Generating zone organization prompt")
        context = await get_prompt_context()

        # Calculate zone organization metrics
        total_zones = context.zone_summary.get("total_count", 0)
        zone_names = context.zone_summary.get("zone_names", [])
        total_devices = context.device_summary.get("total_count", 0)
        online_devices = context.device_summary.get("online_count", 0)
        device_types = context.device_summary.get("sample_device_types", [])

        # Calculate average devices per zone (rough estimate)
        avg_devices_per_zone = (total_devices / total_zones) if total_zones > 0 else 0

        prompt_template = f"""# HomeyPro Zone Organization Guide

## Current Zone Structure Analysis
- **Total Zones**: {total_zones}
- **Total Devices**: {total_devices} ({online_devices} online)
- **Average Devices per Zone**: {avg_devices_per_zone:.1f}
- **Device Types Available**: {len(device_types)} types
- **Zone Organization Status**: {
            "Well-structured"
            if total_zones >= 3 and avg_devices_per_zone <= 10
            else "Needs optimization"
        }

## Your Current Zones
{
            chr(10).join(f"- **{zone}**" for zone in zone_names)
            if zone_names
            else "- No zones configured yet"
        }

## Zone Organization Framework

### Understanding Zone Benefits

#### **Automation Efficiency**
- **Group Control**: Control multiple devices in the same area simultaneously
- **Context-Aware Flows**: Create location-specific automation rules
- **Simplified Management**: Organize devices by physical location and purpose
- **Scalability**: Easily add new devices to existing zones

#### **User Experience**
- **Intuitive Navigation**: Find devices quickly by location
- **Logical Grouping**: Match digital organization to physical layout
- **Voice Control**: Use zone names for natural voice commands
- **Mobile App**: Streamlined device access in mobile interface

### Zone Design Principles

#### **Physical Layout Mapping**
1. **Room-Based Zones**: Create zones that match actual rooms
2. **Functional Areas**: Group areas by usage (e.g., "Entertainment Area")
3. **Outdoor Spaces**: Separate indoor and outdoor zones appropriately
4. **Multi-Level Homes**: Use floor-based organization when needed

#### **Zone Naming Best Practices**
- **Clear and Descriptive**: Use names everyone in the household understands
- **Consistent Naming**: Follow a consistent naming convention
- **Avoid Abbreviations**: Use full words for clarity
- **Future-Proof**: Choose names that won't become outdated

**Good Examples:**
- Living Room, Master Bedroom, Kitchen, Front Yard
- Home Office, Guest Bathroom, Garage, Back Patio

**Avoid:**
- LR, BR1, Kit, Yd (too abbreviated)
- Room1, Area2, Zone3 (not descriptive)

### Zone Organization Strategies

#### **For Small Homes/Apartments** (1-3 zones recommended)
```
Suggested Structure:
├── Living Area (living room, dining, kitchen)
├── Bedroom Area (bedrooms, bathrooms)
└── Outdoor (balcony, patio, entrance)
```

**Benefits:**
- Simple navigation
- Easy device management
- Reduced complexity
- Quick automation setup

#### **For Medium Homes** (4-8 zones recommended)
```
Suggested Structure:
├── Living Room
├── Kitchen
├── Master Bedroom
├── Guest Bedroom/Office
├── Bathrooms
├── Garage/Utility
├── Front Yard
└── Back Yard
```

**Benefits:**
- Room-specific control
- Targeted automation
- Balanced organization
- Scalable structure

#### **For Large Homes** (8+ zones recommended)
```
Suggested Structure:
├── Ground Floor
│   ├── Living Room
│   ├── Dining Room
│   ├── Kitchen
│   ├── Guest Bathroom
│   └── Entry/Foyer
├── Upper Floor
│   ├── Master Bedroom
│   ├── Master Bathroom
│   ├── Guest Bedrooms
│   └── Office/Study
├── Basement/Lower Level
│   ├── Recreation Room
│   ├── Utility Room
│   └── Storage Areas
└── Outdoor Areas
    ├── Front Yard
    ├── Back Yard
    └── Garage/Driveway
```

**Benefits:**
- Detailed organization
- Floor-based grouping
- Comprehensive coverage
- Professional management

### Device Assignment Guidelines

#### **Device-to-Zone Mapping**

##### **Lighting Devices**
- **Primary Rule**: Assign lights to the zone where they're physically located
- **Exception**: Hallway lights might belong to "Common Areas" zone
- **Consideration**: Outdoor lights should be in appropriate outdoor zones

##### **Climate Control**
- **Thermostats**: Assign to the zone they primarily control
- **Sensors**: Place in the zone where they measure conditions
- **HVAC Units**: Assign to utility zones or the primary area they serve

##### **Security Devices**
- **Door/Window Sensors**: Assign to the zone of the protected opening
- **Motion Sensors**: Place in the zone where motion is detected
- **Cameras**: Assign to the zone they monitor
- **Alarm Panels**: Usually in a central "Security" or "Entry" zone

##### **Entertainment Devices**
- **TVs/Audio**: Assign to the entertainment zone where they're used
- **Streaming Devices**: Same zone as the display they connect to
- **Speakers**: Zone where the audio is heard (may differ from device location)

#### **Multi-Zone Devices**
Some devices affect multiple zones:
- **Central HVAC**: Create a "HVAC System" zone or assign to "Utility"
- **Whole-House Audio**: Consider a "Audio System" zone
- **Security System**: Use a dedicated "Security" zone
- **Network Equipment**: "Utility" or "Technical" zone

### Zone Optimization Strategies

#### **Current System Analysis**
Based on your {total_zones} zones and {total_devices} devices:

{
            f'''
**Optimization Recommendations:**
- Your system appears well-balanced with {avg_devices_per_zone:.1f} devices per zone
- Consider grouping similar device types within zones for easier management
- Review zone names for clarity and consistency
'''
            if total_zones > 0 and avg_devices_per_zone <= 10
            else f'''
**Optimization Needed:**
- {"Consider creating zones to organize your devices" if total_zones == 0 else f"Consider redistributing devices - {avg_devices_per_zone:.1f} devices per zone may be too many"}
- Start with basic room-based zones
- Group devices by physical location first
'''
        }

#### **Device Type Distribution**
Your available device types: {
            ", ".join(device_types) if device_types else "None detected"
        }

**Suggested Zone Assignments:**
{
            chr(10).join(
                f"- **{device_type}**: Assign to zones based on physical location and primary usage area"
                for device_type in device_types[:5]
            )
            if device_types
            else "- No device types detected for specific recommendations"
        }

#### **Performance Optimization**
- **Zone Size**: Keep zones manageable (5-15 devices per zone ideal)
- **Logical Grouping**: Group devices that are often controlled together
- **Automation Efficiency**: Design zones to support your most common automation scenarios
- **Future Growth**: Leave room for additional devices in each zone

### Zone Management Best Practices

#### **Regular Maintenance**
1. **Monthly Review**: Check if device assignments still make sense
2. **Seasonal Adjustments**: Consider seasonal device usage patterns
3. **New Device Integration**: Plan zone assignment before adding devices
4. **Zone Cleanup**: Remove unused or offline devices from zones

#### **Documentation**
- **Zone Purpose**: Document the intended use of each zone
- **Device List**: Maintain a list of devices in each zone
- **Automation Notes**: Record which flows use which zones
- **Change Log**: Track zone modifications and reasons

#### **User Training**
- **Household Members**: Ensure everyone understands the zone structure
- **Naming Consistency**: Use zone names consistently in conversations
- **Voice Commands**: Train voice assistants with zone names
- **Mobile Access**: Show family members how to navigate zones in apps

### Common Zone Organization Mistakes

#### **Over-Complication**
- **Too Many Zones**: Creating zones for every small area
- **Inconsistent Naming**: Using different naming conventions
- **Logical Confusion**: Zones that don't match physical or functional reality

#### **Under-Organization**
- **Too Few Zones**: Putting all devices in one or two zones
- **Mixed Purposes**: Combining unrelated areas in single zones
- **No Structure**: Random device assignments without logic

#### **Maintenance Issues**
- **Outdated Assignments**: Not updating zones when devices move
- **Orphaned Devices**: Devices not assigned to any zone
- **Duplicate Functions**: Multiple zones serving the same purpose

### Zone-Based Automation Examples

#### **Morning Routine by Zone**
```
Flow: Morning Activation
WHEN: 7:00 AM on weekdays
THEN:
- Turn on Kitchen lights to 80%
- Set Living Room temperature to 22°C
- Turn on Master Bedroom lights to 30%
- Start Coffee Maker in Kitchen zone
```

#### **Security by Zone**
```
Flow: Evening Security
WHEN: 10:00 PM daily
THEN:
- Turn off all lights in Outdoor zones
- Arm motion sensors in Ground Floor zones
- Set Entry zone to security mode
- Enable night lighting in Hallway zones
```

#### **Energy Saving by Zone**
```
Flow: Away Mode
WHEN: No one home for 30 minutes
THEN:
- Turn off all devices in Living Areas
- Lower temperature in all Bedroom zones
- Keep only essential devices in Utility zones
- Maintain security devices in all zones
```

### Implementation Roadmap

#### **Phase 1: Basic Zone Setup** (Week 1)
1. **Identify Main Areas**: List your home's primary functional areas
2. **Create Core Zones**: Set up 3-5 essential zones
3. **Assign Major Devices**: Move devices to appropriate zones
4. **Test Navigation**: Verify zone structure makes sense

#### **Phase 2: Refinement** (Week 2-3)
1. **Add Detailed Zones**: Create additional zones for specific areas
2. **Optimize Device Assignment**: Fine-tune device placements
3. **Update Automation**: Modify flows to use new zone structure
4. **User Training**: Teach household members the new organization

#### **Phase 3: Advanced Organization** (Week 4+)
1. **Automation Integration**: Create zone-based automation flows
2. **Performance Monitoring**: Track how well the organization works
3. **Continuous Improvement**: Adjust based on usage patterns
4. **Documentation**: Maintain zone organization documentation

### Troubleshooting Zone Issues

#### **Navigation Problems**
- **Solution**: Simplify zone names and structure
- **Check**: Ensure zones match how people think about spaces
- **Fix**: Rename or reorganize confusing zones

#### **Automation Conflicts**
- **Solution**: Review flows that affect multiple zones
- **Check**: Look for overlapping zone-based automations
- **Fix**: Coordinate zone-based flows to avoid conflicts

#### **Device Assignment Confusion**
- **Solution**: Create clear device assignment rules
- **Check**: Verify devices are in logical zones
- **Fix**: Move misplaced devices to appropriate zones

### Getting Help with Zone Organization

#### **Planning Resources**
- **Floor Plans**: Use home floor plans to visualize zone structure
- **Usage Patterns**: Observe how you actually use different areas
- **Family Input**: Get input from all household members
- **Professional Advice**: Consider smart home consultation for complex setups

#### **Technical Support**
- **HomeyPro Documentation**: Review zone management features
- **Community Forums**: Learn from other users' zone organizations
- **Best Practices**: Research smart home organization strategies
- **Expert Consultation**: Get professional help for large or complex homes

---
*Zone organization guidance generated at: {context.timestamp}*
*Analysis based on your {total_zones} zones and {total_devices} devices*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate zone organization prompt: {e}")
        return f"""# HomeyPro Zone Organization Guide

## Error
Unable to generate contextual zone organization guidance due to system connectivity issues.

## Basic Zone Organization Principles
1. Create zones that match your home's physical layout
2. Use clear, descriptive names for all zones
3. Assign devices to zones based on their physical location
4. Keep zones manageable (5-15 devices per zone)
5. Group devices that are often controlled together
6. Plan for future device additions
7. Regularly review and optimize zone structure

Common zone types:
- Room-based zones (Living Room, Kitchen, Bedroom)
- Functional zones (Entertainment Area, Security Zone)
- Outdoor zones (Front Yard, Back Patio, Garage)
- Utility zones (HVAC System, Network Equipment)

Please check your HomeyPro connection and try again for detailed zone organization guidance.

Error details: {str(e)}
"""


@mcp.prompt()
async def system_health_check(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    Provides comprehensive system diagnostic template for HomeyPro health assessment.

    This prompt helps users perform systematic health checks of their HomeyPro
    system by providing structured diagnostic guidance and system status analysis.

    Args:
        arguments: Optional parameters (not used in this prompt)

    Returns:
        Structured template for system health check guidance
    """
    try:
        logger.debug("Generating system health check prompt")
        context = await get_prompt_context()

        # Calculate comprehensive system health metrics
        total_devices = context.device_summary.get("total_count", 0)
        online_devices = context.device_summary.get("online_count", 0)
        offline_devices = context.device_summary.get("offline_count", 0)
        total_zones = context.zone_summary.get("total_count", 0)
        total_flows = context.flow_summary.get("total_count", 0)
        enabled_flows = context.flow_summary.get("enabled_count", 0)

        device_health = (
            (online_devices / total_devices * 100) if total_devices > 0 else 0
        )
        flow_efficiency = (enabled_flows / total_flows * 100) if total_flows > 0 else 0

        # Determine overall system health status
        if device_health >= 95 and flow_efficiency >= 80:
            overall_status = "Excellent"
            status_color = "🟢"
        elif device_health >= 85 and flow_efficiency >= 60:
            overall_status = "Good"
            status_color = "🟡"
        elif device_health >= 70 and flow_efficiency >= 40:
            overall_status = "Fair"
            status_color = "🟠"
        else:
            overall_status = "Needs Attention"
            status_color = "🔴"

        prompt_template = f"""# HomeyPro System Health Check

## Overall System Status: {status_color} {overall_status}

### Quick Health Summary
- **System Connection**: {context.system_info.get("connection_status", "unknown").title()}
- **Device Health**: {device_health:.1f}% ({online_devices}/{total_devices} devices online)
- **Flow Efficiency**: {flow_efficiency:.1f}% ({enabled_flows}/{total_flows} flows enabled)
- **Zone Organization**: {total_zones} zones configured
- **System Language**: {context.system_info.get("language", "unknown")}
- **Units System**: {context.system_info.get("units", "unknown")}

## Comprehensive Health Assessment

### 1. Device Health Analysis

#### **Device Connectivity Status**
- **Total Devices**: {total_devices}
- **Online Devices**: {online_devices} ({device_health:.1f}%)
- **Offline Devices**: {offline_devices}
- **Device Types**: {context.device_summary.get("device_type_count", 0)} different types
- **Available Capabilities**: {context.device_summary.get("capability_count", 0)}

#### **Device Health Indicators**
{"🟢 Excellent device connectivity" if device_health >= 95 else "🟡 Good device connectivity" if device_health >= 85 else "🟠 Fair device connectivity - some devices offline" if device_health >= 70 else "🔴 Poor device connectivity - many devices offline"}

### 2. System Configuration Health

#### **System Settings Status**
- **HomeyPro Address**: {context.system_info.get("address", "Not configured")}
- **Language Setting**: {context.system_info.get("language", "Not configured")}
- **Units System**: {context.system_info.get("units", "Not configured")}
- **Metric System**: {"Yes" if context.system_info.get("is_metric", False) else "No"}
- **Location Services**: {"Configured" if context.system_info.get("location_available", False) else "Not configured"}

### 3. Health Check Action Items

#### **Immediate Actions**
{'''- System is healthy - continue regular monitoring''' if overall_status == "Excellent" else f'''- Investigate {offline_devices} offline devices''' if offline_devices > 0 else '''- Review system configuration'''}

#### **Regular Maintenance**
- **Daily**: Monitor device status and flow execution
- **Weekly**: Check system logs for errors
- **Monthly**: Review flow performance and optimization
- **Quarterly**: Comprehensive system health assessment

---
*System health assessment generated at: {context.timestamp}*
*Overall Status: {overall_status}*
"""

        return prompt_template

    except Exception as e:
        logger.error(f"Failed to generate system health check prompt: {e}")
        return f"""# HomeyPro System Health Check

## Error
Unable to generate contextual system health assessment due to connectivity issues.

## Basic System Health Check Steps
1. Verify HomeyPro system connectivity and responsiveness
2. Check device online/offline status and connectivity
3. Review flow configuration and execution status
4. Assess zone organization and device assignments
5. Monitor system performance and response times
6. Check for error messages or warnings in logs
7. Verify system configuration completeness

Please check your HomeyPro connection and try again for detailed health assessment.

Error details: {str(e)}
"""
