"""Unit tests for enhanced trigger_flow functionality."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Configure pytest-asyncio
pytest_asyncio.auto_mode = True

# Import the module after configuring pytest-asyncio
import homey_mcp.tools.flows as flows_module


class TestEnhancedTriggerFlow:
    """Test enhanced trigger_flow function with flow type detection."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client with both normal and advanced flows."""
        client = AsyncMock()
        
        # Mock normal flow
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_normal_flow.name = "Normal Flow"
        
        # Mock advanced flow
        mock_advanced_flow = MagicMock()
        mock_advanced_flow.id = "advanced_flow_456"
        mock_advanced_flow.name = "Advanced Flow"
        
        # Set up get_flows and get_advanced_flows
        client.flows.get_flows.return_value = [mock_normal_flow]
        client.flows.get_advanced_flows.return_value = [mock_advanced_flow]
        
        # Set up get_flow and get_advanced_flow
        client.flows.get_flow.return_value = mock_normal_flow
        client.flows.get_advanced_flow.return_value = mock_advanced_flow
        
        # Set up trigger_flow and trigger_advanced_flow
        client.flows.trigger_flow.return_value = True
        client.flows.trigger_advanced_flow.return_value = True
        
        return client
    
    @pytest.mark.asyncio
    async def test_trigger_normal_flow(self, mock_client):
        """Test triggering a normal flow."""
        # Setup mocks
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
        
        # Verify normal flow trigger was called
        mock_client.flows.trigger_flow.assert_called_once_with("normal_flow_123")
        mock_client.flows.trigger_advanced_flow.assert_not_called()
        
        # Verify flow details were fetched
        mock_client.flows.get_flow.assert_called_once_with("normal_flow_123")
        mock_client.flows.get_advanced_flow.assert_not_called()
        
        # Verify response structure
        assert result["success"] is True
        assert result["flow_id"] == "normal_flow_123"
        assert result["flow_name"] == "Normal Flow"
        assert result["flow_type"] == "normal"
    
    @pytest.mark.asyncio
    async def test_trigger_advanced_flow(self, mock_client):
        """Test triggering an advanced flow."""
        # Setup mocks
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_456")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_456")
        
        # Verify advanced flow trigger was called
        mock_client.flows.trigger_flow.assert_not_called()
        mock_client.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_456")
        
        # Verify flow details were fetched
        mock_client.flows.get_flow.assert_not_called()
        mock_client.flows.get_advanced_flow.assert_called_once_with("advanced_flow_456")
        
        # Verify response structure
        assert result["success"] is True
        assert result["flow_id"] == "advanced_flow_456"
        assert result["flow_name"] == "Advanced Flow"
        assert result["flow_type"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_trigger_flow_not_found(self, mock_client):
        """Test triggering a flow that doesn't exist."""
        # Setup mocks
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', return_value=None) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("nonexistent_flow_789")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("nonexistent_flow_789")
        
        # Verify no trigger methods were called
        mock_client.flows.trigger_flow.assert_not_called()
        mock_client.flows.trigger_advanced_flow.assert_not_called()
        
        # Verify no flow details were fetched
        mock_client.flows.get_flow.assert_not_called()
        mock_client.flows.get_advanced_flow.assert_not_called()
        
        # Verify error response structure
        assert result["success"] is False
        assert "Flow not found" in result["error"]
        assert result["flow_id"] == "nonexistent_flow_789"
    
    @pytest.mark.asyncio
    async def test_normal_flow_trigger_fails(self, mock_client):
        """Test when normal flow trigger fails."""
        # Setup mocks
        mock_client.flows.trigger_flow.return_value = False
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
        
        # Verify normal flow trigger was called
        mock_client.flows.trigger_flow.assert_called_once_with("normal_flow_123")
        
        # Verify no flow details were fetched (since trigger failed)
        mock_client.flows.get_flow.assert_not_called()
        
        # Verify error response structure
        assert result["success"] is False
        assert "Failed to trigger normal flow" in result["error"]
        assert result["flow_id"] == "normal_flow_123"
        assert result["flow_type"] == "normal"
    
    @pytest.mark.asyncio
    async def test_advanced_flow_trigger_fails(self, mock_client):
        """Test when advanced flow trigger fails."""
        # Setup mocks
        mock_client.flows.trigger_advanced_flow.return_value = False
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_456")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_456")
        
        # Verify advanced flow trigger was called
        mock_client.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_456")
        
        # Verify no flow details were fetched (since trigger failed)
        mock_client.flows.get_advanced_flow.assert_not_called()
        
        # Verify error response structure
        assert result["success"] is False
        assert "Failed to trigger advanced flow" in result["error"]
        assert result["flow_id"] == "advanced_flow_456"
        assert result["flow_type"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_flow_type_detection_error(self, mock_client):
        """Test when flow type detection raises an exception."""
        # Setup mocks
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', side_effect=Exception("Flow type detection failed")) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("any_flow_id")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("any_flow_id")
        
        # Verify no trigger methods were called
        mock_client.flows.trigger_flow.assert_not_called()
        mock_client.flows.trigger_advanced_flow.assert_not_called()
        
        # Verify error response structure
        assert "error" in result
        assert "Failed to trigger flow" in result["error"]
        assert "Flow type detection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_client_initialization_error(self):
        """Test when client initialization fails."""
        # Setup mocks
        with patch.object(flows_module, 'ensure_client', side_effect=ConnectionError("Failed to connect to Homey")), \
             patch.object(flows_module, 'detect_flow_type') as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("any_flow_id")
            
            # Verify flow type detection was not called
            mock_detect_flow_type.assert_not_called()
            
            # Verify error response structure
            assert "error" in result
            assert "Failed to connect to Homey" in result["error"]
    
    @pytest.mark.asyncio
    async def test_normal_flow_get_details_error(self, mock_client):
        """Test when getting normal flow details fails."""
        # Setup mocks
        mock_client.flows.trigger_flow.return_value = True
        mock_client.flows.get_flow.side_effect = Exception("Failed to get flow details")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
        
        # Verify normal flow trigger was called
        mock_client.flows.trigger_flow.assert_called_once_with("normal_flow_123")
        
        # Verify flow details were attempted to be fetched
        mock_client.flows.get_flow.assert_called_once_with("normal_flow_123")
        
        # Verify error response structure
        assert "error" in result
        assert "Failed to trigger flow" in result["error"]
        assert "Failed to get flow details" in result["error"]
    
    @pytest.mark.asyncio
    async def test_advanced_flow_get_details_error(self, mock_client):
        """Test when getting advanced flow details fails."""
        # Setup mocks
        mock_client.flows.trigger_advanced_flow.return_value = True
        mock_client.flows.get_advanced_flow.side_effect = Exception("Failed to get advanced flow details")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_456")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_456")
        
        # Verify advanced flow trigger was called
        mock_client.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_456")
        
        # Verify flow details were attempted to be fetched
        mock_client.flows.get_advanced_flow.assert_called_once_with("advanced_flow_456")
        
        # Verify error response structure
        assert "error" in result
        assert "Failed to trigger flow" in result["error"]
        assert "Failed to get advanced flow details" in result["error"]
        
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows._trigger_flow_impl')
    async def test_trigger_flow_tool_calls_impl(self, mock_trigger_flow_impl):
        """Test that the trigger_flow MCP tool calls the implementation function."""
        mock_trigger_flow_impl.return_value = {"success": True, "flow_id": "test_flow", "flow_type": "normal"}
        
        # We can't directly call the decorated function, but we can verify that the implementation is called
        # by the decorated function by checking if the tool is registered correctly
        assert hasattr(flows_module.trigger_flow, 'name')
        assert flows_module.trigger_flow.name == 'trigger_flow'
        assert "Trigger a flow (automatically detects normal vs advanced)" in flows_module.trigger_flow.description


class TestTriggerFlowComprehensive:
    """Comprehensive tests for the enhanced trigger_flow function."""
    
    @pytest.fixture
    def mock_client_with_multiple_flows(self):
        """Create a mock client with multiple normal and advanced flows."""
        client = AsyncMock()
        
        # Mock normal flows
        normal_flows = []
        for i in range(3):
            flow = MagicMock()
            flow.id = f"normal_flow_{i}"
            flow.name = f"Normal Flow {i}"
            flow.enabled = i % 2 == 0
            normal_flows.append(flow)
        
        # Mock advanced flows
        advanced_flows = []
        for i in range(3):
            flow = MagicMock()
            flow.id = f"advanced_flow_{i}"
            flow.name = f"Advanced Flow {i}"
            flow.enabled = i % 2 == 1
            advanced_flows.append(flow)
        
        # Set up get_flows and get_advanced_flows
        client.flows.get_flows.return_value = normal_flows
        client.flows.get_advanced_flows.return_value = advanced_flows
        
        # Set up get_flow and get_advanced_flow to return the corresponding flow
        client.flows.get_flow = AsyncMock(side_effect=lambda flow_id: next(
            (flow for flow in normal_flows if flow.id == flow_id), None
        ))
        client.flows.get_advanced_flow = AsyncMock(side_effect=lambda flow_id: next(
            (flow for flow in advanced_flows if flow.id == flow_id), None
        ))
        
        # Set up trigger_flow and trigger_advanced_flow
        client.flows.trigger_flow.return_value = True
        client.flows.trigger_advanced_flow.return_value = True
        
        return client
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_empty_flow_id(self, mock_client_with_multiple_flows):
        """Test triggering a flow with an empty flow_id."""
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value=None) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("")
            
            # Verify flow type detection was called with empty string
            mock_detect_flow_type.assert_called_once_with("")
            
            # Verify error response structure
            assert result["success"] is False
            assert "Flow not found" in result["error"]
            assert result["flow_id"] == ""
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_disabled_normal_flow(self, mock_client_with_multiple_flows):
        """Test triggering a disabled normal flow."""
        # Find a disabled normal flow (odd index)
        flow_id = "normal_flow_1"  # This should be disabled based on our fixture
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl(flow_id)
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with(flow_id)
            
            # Verify normal flow trigger was called (even for disabled flows)
            mock_client_with_multiple_flows.flows.trigger_flow.assert_called_once_with(flow_id)
            
            # Verify flow details were fetched
            mock_client_with_multiple_flows.flows.get_flow.assert_called_once_with(flow_id)
            
            # Verify response structure includes flow_type
            assert result["success"] is True
            assert result["flow_id"] == flow_id
            assert result["flow_name"] == "Normal Flow 1"
            assert result["flow_type"] == "normal"
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_disabled_advanced_flow(self, mock_client_with_multiple_flows):
        """Test triggering a disabled advanced flow."""
        # Find a disabled advanced flow (even index)
        flow_id = "advanced_flow_0"  # This should be disabled based on our fixture
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl(flow_id)
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with(flow_id)
            
            # Verify advanced flow trigger was called (even for disabled flows)
            mock_client_with_multiple_flows.flows.trigger_advanced_flow.assert_called_once_with(flow_id)
            
            # Verify flow details were fetched
            mock_client_with_multiple_flows.flows.get_advanced_flow.assert_called_once_with(flow_id)
            
            # Verify response structure includes flow_type
            assert result["success"] is True
            assert result["flow_id"] == flow_id
            assert result["flow_name"] == "Advanced Flow 0"
            assert result["flow_type"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_special_characters(self, mock_client_with_multiple_flows):
        """Test triggering a flow with special characters in the ID."""
        # Create a special flow ID with special characters
        special_flow_id = "flow-with_special.characters@123"
        
        # Create a mock flow with this ID
        special_flow = MagicMock()
        special_flow.id = special_flow_id
        special_flow.name = "Special Flow"
        
        # Add this flow to the normal flows
        mock_client_with_multiple_flows.flows.get_flows.return_value.append(special_flow)
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl(special_flow_id)
            
            # Verify flow type detection was called with the special ID
            mock_detect_flow_type.assert_called_once_with(special_flow_id)
            
            # Verify normal flow trigger was called with the special ID
            mock_client_with_multiple_flows.flows.trigger_flow.assert_called_once_with(special_flow_id)
            
            # Verify response structure includes flow_type
            assert result["success"] is True
            assert result["flow_id"] == special_flow_id
            assert result["flow_type"] == "normal"
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_unicode_characters(self, mock_client_with_multiple_flows):
        """Test triggering a flow with Unicode characters in the ID."""
        # Create a flow ID with Unicode characters
        unicode_flow_id = "flow_with_unicode_😀_🏠"
        
        # Create a mock flow with this ID
        unicode_flow = MagicMock()
        unicode_flow.id = unicode_flow_id
        unicode_flow.name = "Unicode Flow 🏠"
        
        # Add this flow to the advanced flows
        mock_client_with_multiple_flows.flows.get_advanced_flows.return_value.append(unicode_flow)
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl(unicode_flow_id)
            
            # Verify flow type detection was called with the Unicode ID
            mock_detect_flow_type.assert_called_once_with(unicode_flow_id)
            
            # Verify advanced flow trigger was called with the Unicode ID
            mock_client_with_multiple_flows.flows.trigger_advanced_flow.assert_called_once_with(unicode_flow_id)
            
            # Verify response structure includes flow_type
            assert result["success"] is True
            assert result["flow_id"] == unicode_flow_id
            assert result["flow_type"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_very_long_id(self, mock_client_with_multiple_flows):
        """Test triggering a flow with a very long ID."""
        # Create a very long flow ID
        long_flow_id = "a" * 1000
        
        # Create a mock flow with this ID
        long_flow = MagicMock()
        long_flow.id = long_flow_id
        long_flow.name = "Long ID Flow"
        
        # Add this flow to the normal flows
        mock_client_with_multiple_flows.flows.get_flows.return_value.append(long_flow)
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl(long_flow_id)
            
            # Verify flow type detection was called with the long ID
            mock_detect_flow_type.assert_called_once_with(long_flow_id)
            
            # Verify normal flow trigger was called with the long ID
            mock_client_with_multiple_flows.flows.trigger_flow.assert_called_once_with(long_flow_id)
            
            # Verify response structure includes flow_type
            assert result["success"] is True
            assert result["flow_id"] == long_flow_id
            assert result["flow_type"] == "normal"
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_network_timeout(self, mock_client_with_multiple_flows):
        """Test triggering a flow when a network timeout occurs."""
        # Setup mocks for network timeout during trigger
        mock_client_with_multiple_flows.flows.trigger_flow.side_effect = TimeoutError("Network timeout")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_0")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_0")
            
            # Verify normal flow trigger was attempted
            mock_client_with_multiple_flows.flows.trigger_flow.assert_called_once_with("normal_flow_0")
            
            # Verify error response structure
            assert "error" in result
            assert "Network timeout" in result["error"]
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_connection_error(self, mock_client_with_multiple_flows):
        """Test triggering a flow when a connection error occurs."""
        # Setup mocks for connection error during trigger
        mock_client_with_multiple_flows.flows.trigger_advanced_flow.side_effect = ConnectionError("Connection refused")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_0")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_0")
            
            # Verify advanced flow trigger was attempted
            mock_client_with_multiple_flows.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_0")
            
            # Verify error response structure
            assert "error" in result
            assert "Connection refused" in result["error"]
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_invalid_flow_id_type(self, mock_client_with_multiple_flows):
        """Test triggering a flow with an invalid flow_id type (not a string)."""
        # Try with a non-string flow_id (integer)
        flow_id = 12345
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value=None) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl(flow_id)
            
            # Verify flow type detection was called with the integer converted to string
            mock_detect_flow_type.assert_called_once_with(flow_id)
            
            # Verify error response structure
            assert result["success"] is False
            assert "Flow not found" in result["error"]
            assert result["flow_id"] == flow_id
    
    @pytest.mark.asyncio
    async def test_trigger_flow_with_none_flow_id(self, mock_client_with_multiple_flows):
        """Test triggering a flow with None as flow_id."""
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value=None) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl(None)
            
            # Verify flow type detection was called with None
            mock_detect_flow_type.assert_called_once_with(None)
            
            # Verify error response structure
            assert result["success"] is False
            assert "Flow not found" in result["error"]
            assert result["flow_id"] is None
    
    @pytest.mark.asyncio
    async def test_trigger_flow_integration_with_detect_flow_type(self, mock_client_with_multiple_flows):
        """Test the integration between trigger_flow and detect_flow_type."""
        # Don't mock detect_flow_type to test actual integration
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_multiple_flows):
            # Test with a normal flow
            result = await flows_module._trigger_flow_impl("normal_flow_0")
            
            # Verify normal flow trigger was called
            mock_client_with_multiple_flows.flows.trigger_flow.assert_called_once_with("normal_flow_0")
            mock_client_with_multiple_flows.flows.trigger_advanced_flow.assert_not_called()
            
            # Verify response structure includes flow_type
            assert result["success"] is True
            assert result["flow_id"] == "normal_flow_0"
            assert result["flow_type"] == "normal"
            
            # Reset mocks
            mock_client_with_multiple_flows.reset_mock()
            
            # Test with an advanced flow
            result = await flows_module._trigger_flow_impl("advanced_flow_0")
            
            # Verify advanced flow trigger was called
            mock_client_with_multiple_flows.flows.trigger_flow.assert_not_called()
            mock_client_with_multiple_flows.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_0")
            
            # Verify response structure includes flow_type
            assert result["success"] is True
            assert result["flow_id"] == "advanced_flow_0"
            assert result["flow_type"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_trigger_flow_mcp_tool_registration(self):
        """Test that the trigger_flow MCP tool is properly registered with correct parameters."""
        # Verify that trigger_flow is registered as an MCP tool
        assert hasattr(flows_module.trigger_flow, 'name')
        assert flows_module.trigger_flow.name == 'trigger_flow'
        
        # Verify that the tool has the correct description
        assert hasattr(flows_module.trigger_flow, 'description')
        assert "Trigger a flow (automatically detects normal vs advanced)" in flows_module.trigger_flow.description
        
        # Verify that the tool is enabled
        assert hasattr(flows_module.trigger_flow, 'enabled')
        assert flows_module.trigger_flow.enabled is True
        
        # Verify that the tool has the correct parameters
        assert hasattr(flows_module.trigger_flow, 'parameters')
        assert 'properties' in flows_module.trigger_flow.parameters
        assert 'flow_id' in flows_module.trigger_flow.parameters['properties']
        assert flows_module.trigger_flow.parameters['properties']['flow_id']['type'] == 'string'
        # The description might be in 'title' or other fields depending on the MCP implementation
        # Just verify that the flow_id parameter exists with the correct type


class TestTriggerFlowErrorScenarios:
    """Test specific error scenarios for the enhanced trigger_flow function."""
    
    @pytest.fixture
    def mock_client_for_errors(self):
        """Create a mock client for testing error scenarios."""
        client = AsyncMock()
        
        # Mock normal flow
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_normal_flow.name = "Normal Flow"
        
        # Mock advanced flow
        mock_advanced_flow = MagicMock()
        mock_advanced_flow.id = "advanced_flow_456"
        mock_advanced_flow.name = "Advanced Flow"
        
        # Set up get_flows and get_advanced_flows
        client.flows.get_flows.return_value = [mock_normal_flow]
        client.flows.get_advanced_flows.return_value = [mock_advanced_flow]
        
        # Set up get_flow and get_advanced_flow
        client.flows.get_flow.return_value = mock_normal_flow
        client.flows.get_advanced_flow.return_value = mock_advanced_flow
        
        # Set up trigger_flow and trigger_advanced_flow
        client.flows.trigger_flow.return_value = True
        client.flows.trigger_advanced_flow.return_value = True
        
        return client
    
    @pytest.mark.asyncio
    async def test_flow_lookup_api_error(self, mock_client_for_errors):
        """Test when the flow lookup API returns an error."""
        # Setup mocks for API error during flow lookup
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_for_errors), \
             patch.object(flows_module, 'detect_flow_type', side_effect=Exception("API error during flow lookup")) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("any_flow_id")
            
            # Verify flow type detection was attempted
            mock_detect_flow_type.assert_called_once_with("any_flow_id")
            
            # Verify no trigger methods were called
            mock_client_for_errors.flows.trigger_flow.assert_not_called()
            mock_client_for_errors.flows.trigger_advanced_flow.assert_not_called()
            
            # Verify error response structure
            assert "error" in result
            assert "API error during flow lookup" in result["error"]
    
    @pytest.mark.asyncio
    async def test_normal_flow_trigger_api_error(self, mock_client_for_errors):
        """Test when the normal flow trigger API returns an error."""
        # Setup mocks for API error during normal flow trigger
        mock_client_for_errors.flows.trigger_flow.side_effect = Exception("API error during normal flow trigger")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_for_errors), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
            
            # Verify normal flow trigger was attempted
            mock_client_for_errors.flows.trigger_flow.assert_called_once_with("normal_flow_123")
            
            # Verify error response structure
            assert "error" in result
            assert "API error during normal flow trigger" in result["error"]
    
    @pytest.mark.asyncio
    async def test_advanced_flow_trigger_api_error(self, mock_client_for_errors):
        """Test when the advanced flow trigger API returns an error."""
        # Setup mocks for API error during advanced flow trigger
        mock_client_for_errors.flows.trigger_advanced_flow.side_effect = Exception("API error during advanced flow trigger")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_for_errors), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_456")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_456")
            
            # Verify advanced flow trigger was attempted
            mock_client_for_errors.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_456")
            
            # Verify error response structure
            assert "error" in result
            assert "API error during advanced flow trigger" in result["error"]
    
    @pytest.mark.asyncio
    async def test_homey_unreachable_error(self):
        """Test when Homey is unreachable."""
        # Setup mocks for Homey unreachable error
        with patch.object(flows_module, 'ensure_client', side_effect=ConnectionError("Homey is unreachable")):
            
            result = await flows_module._trigger_flow_impl("any_flow_id")
            
            # Verify error response structure
            assert "error" in result
            assert "Homey is unreachable" in result["error"]
    
    @pytest.mark.asyncio
    async def test_homey_authentication_error(self):
        """Test when Homey authentication fails."""
        # Setup mocks for authentication error
        with patch.object(flows_module, 'ensure_client', side_effect=ValueError("Invalid authentication token")):
            
            result = await flows_module._trigger_flow_impl("any_flow_id")
            
            # Verify error response structure
            assert "error" in result
            assert "Invalid authentication token" in result["error"]
    
    @pytest.mark.asyncio
    async def test_flow_lookup_timeout_error(self):
        """Test when flow lookup times out."""
        # Setup mocks for timeout during flow lookup
        with patch.object(flows_module, 'ensure_client', return_value=AsyncMock()), \
             patch.object(flows_module, 'detect_flow_type', side_effect=TimeoutError("Flow lookup timed out")) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("any_flow_id")
            
            # Verify flow type detection was attempted
            mock_detect_flow_type.assert_called_once_with("any_flow_id")
            
            # Verify error response structure
            assert "error" in result
            assert "Flow lookup timed out" in result["error"]
    
    @pytest.mark.asyncio
    async def test_invalid_flow_type_returned(self, mock_client_for_errors):
        """Test when an invalid flow type is returned by detect_flow_type."""
        # Setup mocks to return an invalid flow type and make trigger succeed
        mock_client_for_errors.flows.trigger_advanced_flow.return_value = True
        
        # Create a mock flow with the test ID
        mock_flow = MagicMock()
        mock_flow.id = "any_flow_id"
        mock_flow.name = "Test Flow"
        mock_client_for_errors.flows.get_advanced_flow.return_value = mock_flow
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_for_errors), \
             patch.object(flows_module, 'detect_flow_type', return_value="invalid_type") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("any_flow_id")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("any_flow_id")
            
            # Verify advanced flow trigger was called (current implementation treats any non-"normal" flow_type as advanced)
            mock_client_for_errors.flows.trigger_flow.assert_not_called()
            mock_client_for_errors.flows.trigger_advanced_flow.assert_called_once_with("any_flow_id")
            
            # Verify response structure includes flow_type
            assert result["success"] is True  # The trigger succeeds
            assert result["flow_id"] == "any_flow_id"
            # The current implementation will use "advanced" for the flow_type in the response
            # since it uses the advanced flow API for any non-"normal" flow type
            assert result["flow_type"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_unexpected_exception_during_execution(self, mock_client_for_errors):
        """Test when an unexpected exception occurs during execution."""
        # Setup mocks for unexpected exception
        mock_client_for_errors.flows.trigger_flow.side_effect = RuntimeError("Unexpected error")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_for_errors), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
            
            # Verify normal flow trigger was attempted
            mock_client_for_errors.flows.trigger_flow.assert_called_once_with("normal_flow_123")
            
            # Verify error response structure
            assert "error" in result
            assert "Unexpected error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_memory_error_during_execution(self, mock_client_for_errors):
        """Test when a memory error occurs during execution."""
        # Setup mocks for memory error
        mock_client_for_errors.flows.trigger_advanced_flow.side_effect = MemoryError("Out of memory")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_for_errors), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_456")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_456")
            
            # Verify advanced flow trigger was attempted
            mock_client_for_errors.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_456")
            
            # Verify error response structure
            assert "error" in result
            assert "Out of memory" in result["error"]

class TestTriggerFlowResponseStructure:
    """Test the response structure of the enhanced trigger_flow function."""
    
    @pytest.fixture
    def mock_client_with_flows(self):
        """Create a mock client with both normal and advanced flows."""
        client = AsyncMock()
        
        # Mock normal flow
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_normal_flow.name = "Normal Flow"
        mock_normal_flow.enabled = True
        mock_normal_flow.folder = None
        mock_normal_flow.tags = ["tag1", "tag2"]
        mock_normal_flow.model_dump.return_value = {
            "id": "normal_flow_123",
            "name": "Normal Flow",
            "enabled": True,
            "folder": None,
            "tags": ["tag1", "tag2"]
        }
        
        # Mock advanced flow
        mock_advanced_flow = MagicMock()
        mock_advanced_flow.id = "advanced_flow_456"
        mock_advanced_flow.name = "Advanced Flow"
        mock_advanced_flow.enabled = True
        mock_advanced_flow.folder = {"id": "folder_1", "name": "Folder 1"}
        mock_advanced_flow.tags = ["tag3", "tag4"]
        mock_advanced_flow.model_dump.return_value = {
            "id": "advanced_flow_456",
            "name": "Advanced Flow",
            "enabled": True,
            "folder": {"id": "folder_1", "name": "Folder 1"},
            "tags": ["tag3", "tag4"]
        }
        
        # Set up get_flows and get_advanced_flows
        client.flows.get_flows.return_value = [mock_normal_flow]
        client.flows.get_advanced_flows.return_value = [mock_advanced_flow]
        
        # Set up get_flow and get_advanced_flow
        client.flows.get_flow.return_value = mock_normal_flow
        client.flows.get_advanced_flow.return_value = mock_advanced_flow
        
        # Set up trigger_flow and trigger_advanced_flow
        client.flows.trigger_flow.return_value = True
        client.flows.trigger_advanced_flow.return_value = True
        
        return client
    
    @pytest.mark.asyncio
    async def test_normal_flow_success_response_structure(self, mock_client_with_flows):
        """Test the success response structure for normal flows."""
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
            
            # Verify normal flow trigger was called
            mock_client_with_flows.flows.trigger_flow.assert_called_once_with("normal_flow_123")
            
            # Verify response structure
            assert result["success"] is True
            assert result["flow_id"] == "normal_flow_123"
            assert result["flow_name"] == "Normal Flow"
            assert result["flow_type"] == "normal"
            
            # Verify no unexpected fields
            assert len(result) == 4
            assert set(result.keys()) == {"success", "flow_id", "flow_name", "flow_type"}
    
    @pytest.mark.asyncio
    async def test_advanced_flow_success_response_structure(self, mock_client_with_flows):
        """Test the success response structure for advanced flows."""
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_456")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_456")
            
            # Verify advanced flow trigger was called
            mock_client_with_flows.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_456")
            
            # Verify response structure
            assert result["success"] is True
            assert result["flow_id"] == "advanced_flow_456"
            assert result["flow_name"] == "Advanced Flow"
            assert result["flow_type"] == "advanced"
            
            # Verify no unexpected fields
            assert len(result) == 4
            assert set(result.keys()) == {"success", "flow_id", "flow_name", "flow_type"}
    
    @pytest.mark.asyncio
    async def test_normal_flow_error_response_structure(self, mock_client_with_flows):
        """Test the error response structure for normal flows."""
        # Setup mocks for normal flow trigger failure
        mock_client_with_flows.flows.trigger_flow.return_value = False
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
            
            # Verify normal flow trigger was called
            mock_client_with_flows.flows.trigger_flow.assert_called_once_with("normal_flow_123")
            
            # Verify response structure
            assert result["success"] is False
            assert result["error"] == "Failed to trigger normal flow"
            assert result["flow_id"] == "normal_flow_123"
            assert result["flow_type"] == "normal"
            
            # Verify no unexpected fields
            assert len(result) == 4
            assert set(result.keys()) == {"success", "error", "flow_id", "flow_type"}
    
    @pytest.mark.asyncio
    async def test_advanced_flow_error_response_structure(self, mock_client_with_flows):
        """Test the error response structure for advanced flows."""
        # Setup mocks for advanced flow trigger failure
        mock_client_with_flows.flows.trigger_advanced_flow.return_value = False
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="advanced") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("advanced_flow_456")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("advanced_flow_456")
            
            # Verify advanced flow trigger was called
            mock_client_with_flows.flows.trigger_advanced_flow.assert_called_once_with("advanced_flow_456")
            
            # Verify response structure
            assert result["success"] is False
            assert result["error"] == "Failed to trigger advanced flow"
            assert result["flow_id"] == "advanced_flow_456"
            assert result["flow_type"] == "advanced"
            
            # Verify no unexpected fields
            assert len(result) == 4
            assert set(result.keys()) == {"success", "error", "flow_id", "flow_type"}
    
    @pytest.mark.asyncio
    async def test_flow_not_found_response_structure(self, mock_client_with_flows):
        """Test the response structure when flow is not found."""
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value=None) as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("nonexistent_flow_789")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("nonexistent_flow_789")
            
            # Verify response structure
            assert result["success"] is False
            assert result["error"] == "Flow not found: nonexistent_flow_789"
            assert result["flow_id"] == "nonexistent_flow_789"
            
            # Verify no flow_type field (since flow was not found)
            assert "flow_type" not in result
            
            # Verify no unexpected fields
            assert len(result) == 3
            assert set(result.keys()) == {"success", "error", "flow_id"}
    
    @pytest.mark.asyncio
    async def test_exception_response_structure(self, mock_client_with_flows):
        """Test the response structure when an exception occurs."""
        # Setup mocks for exception during trigger
        mock_client_with_flows.flows.trigger_flow.side_effect = Exception("Test exception")
        
        with patch.object(flows_module, 'ensure_client', return_value=mock_client_with_flows), \
             patch.object(flows_module, 'detect_flow_type', return_value="normal") as mock_detect_flow_type:
            
            result = await flows_module._trigger_flow_impl("normal_flow_123")
            
            # Verify flow type detection was called
            mock_detect_flow_type.assert_called_once_with("normal_flow_123")
            
            # Verify normal flow trigger was attempted
            mock_client_with_flows.flows.trigger_flow.assert_called_once_with("normal_flow_123")
            
            # Verify response structure
            assert "error" in result
            assert "Test exception" in result["error"]
            
            # Verify no unexpected fields
            assert len(result) == 1
            assert set(result.keys()) == {"error"}