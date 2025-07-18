"""Unit tests for flow functionality."""

import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Configure pytest-asyncio
pytest_asyncio.auto_mode = True

import homey_mcp.tools.flows as flows_module


class TestDetectFlowType:
    """Test detect_flow_type function."""
    
    @pytest.fixture
    def mock_client_with_normal_flow(self):
        """Create a mock client with a normal flow."""
        client = AsyncMock()
        
        # Mock normal flow
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_normal_flow.name = "Normal Flow"
        
        # Mock advanced flow (different ID)
        mock_advanced_flow = MagicMock()
        mock_advanced_flow.id = "advanced_flow_456"
        mock_advanced_flow.name = "Advanced Flow"
        
        client.flows.get_flows.return_value = [mock_normal_flow]
        client.flows.get_advanced_flows.return_value = [mock_advanced_flow]
        
        return client
    
    @pytest.fixture
    def mock_client_with_advanced_flow(self):
        """Create a mock client with an advanced flow."""
        client = AsyncMock()
        
        # Mock normal flow (different ID)
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_normal_flow.name = "Normal Flow"
        
        # Mock advanced flow
        mock_advanced_flow = MagicMock()
        mock_advanced_flow.id = "advanced_flow_456"
        mock_advanced_flow.name = "Advanced Flow"
        
        client.flows.get_flows.return_value = [mock_normal_flow]
        client.flows.get_advanced_flows.return_value = [mock_advanced_flow]
        
        return client
    
    @pytest.fixture
    def mock_client_with_no_flows(self):
        """Create a mock client with no flows."""
        client = AsyncMock()
        client.flows.get_flows.return_value = []
        client.flows.get_advanced_flows.return_value = []
        return client
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_normal_flow(self, mock_ensure_client, mock_client_with_normal_flow):
        """Test detecting a normal flow type."""
        mock_ensure_client.return_value = mock_client_with_normal_flow
        
        result = await flows_module.detect_flow_type("normal_flow_123")
        
        assert result == "normal"
        mock_ensure_client.assert_called_once()
        mock_client_with_normal_flow.flows.get_flows.assert_called_once()
        # Should not call get_advanced_flows since flow was found in normal flows
        mock_client_with_normal_flow.flows.get_advanced_flows.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_advanced_flow(self, mock_ensure_client, mock_client_with_advanced_flow):
        """Test detecting an advanced flow type."""
        mock_ensure_client.return_value = mock_client_with_advanced_flow
        
        result = await flows_module.detect_flow_type("advanced_flow_456")
        
        assert result == "advanced"
        mock_ensure_client.assert_called_once()
        mock_client_with_advanced_flow.flows.get_flows.assert_called_once()
        mock_client_with_advanced_flow.flows.get_advanced_flows.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_flow_not_found(self, mock_ensure_client, mock_client_with_no_flows):
        """Test detecting flow type when flow is not found in either type."""
        mock_ensure_client.return_value = mock_client_with_no_flows
        
        result = await flows_module.detect_flow_type("nonexistent_flow_789")
        
        assert result is None
        mock_ensure_client.assert_called_once()
        mock_client_with_no_flows.flows.get_flows.assert_called_once()
        mock_client_with_no_flows.flows.get_advanced_flows.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_normal_flows_api_fails(self, mock_ensure_client):
        """Test detecting flow type when normal flows API fails but advanced flows succeeds."""
        mock_client = AsyncMock()
        mock_client.flows.get_flows.side_effect = Exception("Normal flows API failed")
        
        # Mock advanced flow
        mock_advanced_flow = MagicMock()
        mock_advanced_flow.id = "advanced_flow_456"
        mock_client.flows.get_advanced_flows.return_value = [mock_advanced_flow]
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module.detect_flow_type("advanced_flow_456")
        
        assert result == "advanced"
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_advanced_flows_api_fails(self, mock_ensure_client):
        """Test detecting flow type when advanced flows API fails but normal flows succeeds."""
        mock_client = AsyncMock()
        
        # Mock normal flow
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_client.flows.get_flows.return_value = [mock_normal_flow]
        
        mock_client.flows.get_advanced_flows.side_effect = Exception("Advanced flows API failed")
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module.detect_flow_type("normal_flow_123")
        
        assert result == "normal"
        mock_client.flows.get_flows.assert_called_once()
        # Advanced flows should not be called since flow was found in normal flows
        mock_client.flows.get_advanced_flows.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_advanced_flows_api_fails_flow_not_in_normal(self, mock_ensure_client):
        """Test detecting flow type when advanced flows API fails and flow not found in normal flows."""
        mock_client = AsyncMock()
        
        # Mock normal flow (different ID)
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_client.flows.get_flows.return_value = [mock_normal_flow]
        
        mock_client.flows.get_advanced_flows.side_effect = Exception("Advanced flows API failed")
        
        mock_ensure_client.return_value = mock_client
        
        # Should raise exception since both APIs effectively failed for the requested flow
        with pytest.raises(Exception) as exc_info:
            await flows_module.detect_flow_type("advanced_flow_456")
        
        assert "Failed to check both normal and advanced flows" in str(exc_info.value)
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_both_apis_fail(self, mock_ensure_client):
        """Test detecting flow type when both APIs fail."""
        mock_client = AsyncMock()
        mock_client.flows.get_flows.side_effect = Exception("Normal flows API failed")
        mock_client.flows.get_advanced_flows.side_effect = Exception("Advanced flows API failed")
        
        mock_ensure_client.return_value = mock_client
        
        with pytest.raises(Exception) as exc_info:
            await flows_module.detect_flow_type("any_flow_id")
        
        assert "Failed to check both normal and advanced flows" in str(exc_info.value)
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_ensure_client_fails(self, mock_ensure_client):
        """Test detecting flow type when client initialization fails."""
        mock_ensure_client.side_effect = ConnectionError("Failed to connect to Homey")
        
        with pytest.raises(Exception) as exc_info:
            await flows_module.detect_flow_type("any_flow_id")
        
        assert "Error detecting flow type for flow_id any_flow_id" in str(exc_info.value)
        mock_ensure_client.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_multiple_normal_flows(self, mock_ensure_client):
        """Test detecting flow type with multiple normal flows."""
        mock_client = AsyncMock()
        
        # Mock multiple normal flows
        mock_normal_flow1 = MagicMock()
        mock_normal_flow1.id = "normal_flow_123"
        mock_normal_flow2 = MagicMock()
        mock_normal_flow2.id = "normal_flow_456"
        mock_normal_flow3 = MagicMock()
        mock_normal_flow3.id = "normal_flow_789"
        
        mock_client.flows.get_flows.return_value = [mock_normal_flow1, mock_normal_flow2, mock_normal_flow3]
        mock_client.flows.get_advanced_flows.return_value = []
        
        mock_ensure_client.return_value = mock_client
        
        # Test finding the second flow
        result = await flows_module.detect_flow_type("normal_flow_456")
        
        assert result == "normal"
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_multiple_advanced_flows(self, mock_ensure_client):
        """Test detecting flow type with multiple advanced flows."""
        mock_client = AsyncMock()
        
        # Mock normal flows (different IDs)
        mock_normal_flow = MagicMock()
        mock_normal_flow.id = "normal_flow_123"
        mock_client.flows.get_flows.return_value = [mock_normal_flow]
        
        # Mock multiple advanced flows
        mock_advanced_flow1 = MagicMock()
        mock_advanced_flow1.id = "advanced_flow_456"
        mock_advanced_flow2 = MagicMock()
        mock_advanced_flow2.id = "advanced_flow_789"
        mock_advanced_flow3 = MagicMock()
        mock_advanced_flow3.id = "advanced_flow_101"
        
        mock_client.flows.get_advanced_flows.return_value = [mock_advanced_flow1, mock_advanced_flow2, mock_advanced_flow3]
        
        mock_ensure_client.return_value = mock_client
        
        # Test finding the third advanced flow
        result = await flows_module.detect_flow_type("advanced_flow_101")
        
        assert result == "advanced"
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_empty_flow_id(self, mock_ensure_client, mock_client_with_no_flows):
        """Test detecting flow type with empty flow_id."""
        mock_ensure_client.return_value = mock_client_with_no_flows
        
        result = await flows_module.detect_flow_type("")
        
        assert result is None
        mock_ensure_client.assert_called_once()
        mock_client_with_no_flows.flows.get_flows.assert_called_once()
        mock_client_with_no_flows.flows.get_advanced_flows.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_none_flow_id(self, mock_ensure_client, mock_client_with_no_flows):
        """Test detecting flow type with None flow_id."""
        mock_ensure_client.return_value = mock_client_with_no_flows
        
        result = await flows_module.detect_flow_type(None)
        
        assert result is None
        mock_ensure_client.assert_called_once()
        mock_client_with_no_flows.flows.get_flows.assert_called_once()
        mock_client_with_no_flows.flows.get_advanced_flows.assert_called_once()


class TestDetectFlowTypeIntegration:
    """Integration tests for detect_flow_type function."""
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_handles_all_connection_errors(self, mock_ensure_client):
        """Test that detect_flow_type handles various connection errors gracefully."""
        connection_errors = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out"),
            ValueError("Invalid response"),
            RuntimeError("Runtime error"),
        ]
        
        for error in connection_errors:
            mock_ensure_client.side_effect = error
            
            with pytest.raises(Exception) as exc_info:
                await flows_module.detect_flow_type("test_flow_id")
            
            assert "Error detecting flow type for flow_id test_flow_id" in str(exc_info.value)
            mock_ensure_client.assert_called()
            mock_ensure_client.reset_mock()
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_detect_flow_type_logs_warnings_for_partial_failures(self, mock_ensure_client, caplog):
        """Test that detect_flow_type logs appropriate warnings for partial API failures."""
        mock_client = AsyncMock()
        
        # Normal flows API fails
        mock_client.flows.get_flows.side_effect = Exception("Normal flows API failed")
        
        # Advanced flows API succeeds
        mock_advanced_flow = MagicMock()
        mock_advanced_flow.id = "advanced_flow_456"
        mock_client.flows.get_advanced_flows.return_value = [mock_advanced_flow]
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module.detect_flow_type("advanced_flow_456")
        
        assert result == "advanced"
        # Check that warning was logged for normal flows failure
        assert "Error checking normal flows for flow_id advanced_flow_456" in caplog.text


class TestListFlows:
    """Test enhanced list_flows function."""
    
    @pytest.fixture
    def mock_client_with_flows(self):
        """Create a mock client with both normal and advanced flows."""
        client = AsyncMock()
        
        # Mock normal flows
        mock_normal_flow1 = MagicMock()
        mock_normal_flow1.id = "normal_flow_123"
        mock_normal_flow1.name = "Normal Flow 1"
        mock_normal_flow1.model_dump.return_value = {"id": "normal_flow_123", "name": "Normal Flow 1"}
        
        mock_normal_flow2 = MagicMock()
        mock_normal_flow2.id = "normal_flow_456"
        mock_normal_flow2.name = "Normal Flow 2"
        mock_normal_flow2.model_dump.return_value = {"id": "normal_flow_456", "name": "Normal Flow 2"}
        
        # Mock advanced flows
        mock_advanced_flow1 = MagicMock()
        mock_advanced_flow1.id = "advanced_flow_789"
        mock_advanced_flow1.name = "Advanced Flow 1"
        mock_advanced_flow1.model_dump.return_value = {"id": "advanced_flow_789", "name": "Advanced Flow 1"}
        
        mock_advanced_flow2 = MagicMock()
        mock_advanced_flow2.id = "advanced_flow_101"
        mock_advanced_flow2.name = "Advanced Flow 2"
        mock_advanced_flow2.model_dump.return_value = {"id": "advanced_flow_101", "name": "Advanced Flow 2"}
        
        client.flows.get_flows.return_value = [mock_normal_flow1, mock_normal_flow2]
        client.flows.get_advanced_flows.return_value = [mock_advanced_flow1, mock_advanced_flow2]
        
        return client
    
    @pytest.fixture
    def mock_client_with_no_flows(self):
        """Create a mock client with no flows."""
        client = AsyncMock()
        client.flows.get_flows.return_value = []
        client.flows.get_advanced_flows.return_value = []
        return client
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_combines_both_types(self, mock_ensure_client, mock_client_with_flows):
        """Test that list_flows combines both normal and advanced flows."""
        mock_ensure_client.return_value = mock_client_with_flows
        
        result = await flows_module._list_flows_impl()
        
        # Verify both APIs were called
        mock_client_with_flows.flows.get_flows.assert_called_once()
        mock_client_with_flows.flows.get_advanced_flows.assert_called_once()
        
        # Verify result structure
        assert "flows" in result
        assert "pagination" in result
        
        # Verify flow count (2 normal + 2 advanced = 4 total)
        assert result["pagination"]["total_count"] == 4
        assert len(result["flows"]) == 4
        
        # Verify flow_type field was added to each flow
        flow_types = [flow["flow_type"] for flow in result["flows"]]
        assert flow_types.count("normal") == 2
        assert flow_types.count("advanced") == 2
        
        # Verify specific flow IDs are present
        flow_ids = [flow["id"] for flow in result["flows"]]
        assert "normal_flow_123" in flow_ids
        assert "normal_flow_456" in flow_ids
        assert "advanced_flow_789" in flow_ids
        assert "advanced_flow_101" in flow_ids
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_with_pagination(self, mock_ensure_client, mock_client_with_flows):
        """Test that list_flows correctly paginates combined results."""
        mock_ensure_client.return_value = mock_client_with_flows
        
        # Request first page with 2 items
        cursor = '{"offset": 0, "page_size": 2}'
        result = await flows_module._list_flows_impl(cursor)
        
        # Verify pagination
        assert result["pagination"]["total_count"] == 4
        assert result["pagination"]["page_size"] == 2
        assert result["pagination"]["offset"] == 0
        assert result["pagination"]["has_next"] == True
        assert result["pagination"]["next_cursor"] is not None
        
        # Verify only 2 flows returned
        assert len(result["flows"]) == 2
        
        # Request second page
        cursor = result["pagination"]["next_cursor"]
        result = await flows_module._list_flows_impl(cursor)
        
        # Verify second page pagination
        assert result["pagination"]["total_count"] == 4
        assert result["pagination"]["page_size"] == 2
        assert result["pagination"]["offset"] == 2
        assert result["pagination"]["has_next"] == False
        assert result["pagination"]["next_cursor"] is None
        
        # Verify remaining 2 flows returned
        assert len(result["flows"]) == 2
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_normal_flows_api_fails(self, mock_ensure_client):
        """Test that list_flows continues with advanced flows if normal flows API fails."""
        mock_client = AsyncMock()
        mock_client.flows.get_flows.side_effect = Exception("Normal flows API failed")
        
        # Mock advanced flows
        mock_advanced_flow1 = MagicMock()
        mock_advanced_flow1.id = "advanced_flow_789"
        mock_advanced_flow1.name = "Advanced Flow 1"
        mock_advanced_flow1.model_dump.return_value = {"id": "advanced_flow_789", "name": "Advanced Flow 1"}
        
        mock_advanced_flow2 = MagicMock()
        mock_advanced_flow2.id = "advanced_flow_101"
        mock_advanced_flow2.name = "Advanced Flow 2"
        mock_advanced_flow2.model_dump.return_value = {"id": "advanced_flow_101", "name": "Advanced Flow 2"}
        
        mock_client.flows.get_advanced_flows.return_value = [mock_advanced_flow1, mock_advanced_flow2]
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module._list_flows_impl()
        
        # Verify both APIs were called
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_called_once()
        
        # Verify only advanced flows are returned
        assert len(result["flows"]) == 2
        assert all(flow["flow_type"] == "advanced" for flow in result["flows"])
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_advanced_flows_api_fails(self, mock_ensure_client):
        """Test that list_flows continues with normal flows if advanced flows API fails."""
        mock_client = AsyncMock()
        
        # Mock normal flows
        mock_normal_flow1 = MagicMock()
        mock_normal_flow1.id = "normal_flow_123"
        mock_normal_flow1.name = "Normal Flow 1"
        mock_normal_flow1.model_dump.return_value = {"id": "normal_flow_123", "name": "Normal Flow 1"}
        
        mock_normal_flow2 = MagicMock()
        mock_normal_flow2.id = "normal_flow_456"
        mock_normal_flow2.name = "Normal Flow 2"
        mock_normal_flow2.model_dump.return_value = {"id": "normal_flow_456", "name": "Normal Flow 2"}
        
        mock_client.flows.get_flows.return_value = [mock_normal_flow1, mock_normal_flow2]
        mock_client.flows.get_advanced_flows.side_effect = Exception("Advanced flows API failed")
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module._list_flows_impl()
        
        # Verify both APIs were called
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_called_once()
        
        # Verify only normal flows are returned
        assert len(result["flows"]) == 2
        assert all(flow["flow_type"] == "normal" for flow in result["flows"])
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_both_apis_fail(self, mock_ensure_client):
        """Test that list_flows returns error when both APIs fail."""
        mock_client = AsyncMock()
        mock_client.flows.get_flows.side_effect = Exception("Normal flows API failed")
        mock_client.flows.get_advanced_flows.side_effect = Exception("Advanced flows API failed")
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module._list_flows_impl()
        
        # Verify both APIs were called
        mock_client.flows.get_flows.assert_called_once()
        mock_client.flows.get_advanced_flows.assert_called_once()
        
        # Verify error response
        assert "error" in result
        assert "Failed to fetch both normal and advanced flows" in result["error"]
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_empty_results(self, mock_ensure_client, mock_client_with_no_flows):
        """Test that list_flows handles empty results correctly."""
        mock_ensure_client.return_value = mock_client_with_no_flows
        
        result = await flows_module._list_flows_impl()
        
        # Verify both APIs were called
        mock_client_with_no_flows.flows.get_flows.assert_called_once()
        mock_client_with_no_flows.flows.get_advanced_flows.assert_called_once()
        
        # Verify empty result structure
        assert "flows" in result
        assert "pagination" in result
        assert result["pagination"]["total_count"] == 0
        assert len(result["flows"]) == 0
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_pagination_error(self, mock_ensure_client, mock_client_with_flows):
        """Test that list_flows handles pagination errors correctly."""
        mock_ensure_client.return_value = mock_client_with_flows
        
        # Invalid cursor
        result = await flows_module._list_flows_impl("invalid_cursor")
        
        # Verify error response
        assert "error" in result
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_mcp_tool_registration(self, mock_ensure_client):
        """Test that the list_flows MCP tool is properly registered."""
        # Verify that list_flows is registered as an MCP tool
        assert hasattr(flows_module.list_flows, 'name')
        assert flows_module.list_flows.name == 'list_flows'
        
        # Verify that the tool has the correct description
        assert hasattr(flows_module.list_flows, 'description')
        assert "List all flows (both normal and advanced)" in flows_module.list_flows.description
        
        # Verify that the tool is enabled
        assert hasattr(flows_module.list_flows, 'enabled')
        assert flows_module.list_flows.enabled is True
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_flow_type_field(self, mock_ensure_client):
        """Test that flow_type field is correctly added to all flows."""
        mock_client = AsyncMock()
        
        # Create flows with different properties to ensure flow_type is added correctly
        normal_flows = []
        for i in range(3):
            flow = MagicMock()
            flow.id = f"normal_flow_{i}"
            flow.name = f"Normal Flow {i}"
            flow.enabled = i % 2 == 0
            flow.model_dump.return_value = {
                "id": f"normal_flow_{i}",
                "name": f"Normal Flow {i}",
                "enabled": i % 2 == 0,
                "tags": [f"tag{i}"],
                "folder": None if i % 2 == 0 else {"id": f"folder_{i}", "name": f"Folder {i}"}
            }
            normal_flows.append(flow)
        
        advanced_flows = []
        for i in range(3):
            flow = MagicMock()
            flow.id = f"advanced_flow_{i}"
            flow.name = f"Advanced Flow {i}"
            flow.enabled = i % 2 == 1
            flow.model_dump.return_value = {
                "id": f"advanced_flow_{i}",
                "name": f"Advanced Flow {i}",
                "enabled": i % 2 == 1,
                "tags": [f"tag{i}"],
                "folder": {"id": f"folder_{i}", "name": f"Folder {i}"} if i % 2 == 0 else None
            }
            advanced_flows.append(flow)
        
        mock_client.flows.get_flows.return_value = normal_flows
        mock_client.flows.get_advanced_flows.return_value = advanced_flows
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module._list_flows_impl()
        
        # Verify flow_type field was added to each flow
        for flow in result["flows"]:
            if flow["id"].startswith("normal_flow_"):
                assert flow["flow_type"] == "normal"
            elif flow["id"].startswith("advanced_flow_"):
                assert flow["flow_type"] == "advanced"
            else:
                assert False, f"Unexpected flow ID: {flow['id']}"
            
            # Verify original properties are preserved
            assert "name" in flow
            assert "enabled" in flow
            assert "tags" in flow
            assert "folder" in flow
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_different_page_sizes(self, mock_ensure_client, mock_client_with_flows):
        """Test that list_flows correctly handles different page sizes."""
        mock_ensure_client.return_value = mock_client_with_flows
        
        # Test with page size of 1
        cursor = '{"offset": 0, "page_size": 1}'
        result = await flows_module._list_flows_impl(cursor)
        
        assert result["pagination"]["page_size"] == 1
        assert len(result["flows"]) == 1
        assert result["pagination"]["has_next"] == True
        
        # Test with page size of 3
        cursor = '{"offset": 0, "page_size": 3}'
        result = await flows_module._list_flows_impl(cursor)
        
        assert result["pagination"]["page_size"] == 3
        assert len(result["flows"]) == 3
        assert result["pagination"]["has_next"] == True
        
        # Test with page size of 4 (exactly matches total count)
        cursor = '{"offset": 0, "page_size": 4}'
        result = await flows_module._list_flows_impl(cursor)
        
        assert result["pagination"]["page_size"] == 4
        assert len(result["flows"]) == 4
        assert result["pagination"]["has_next"] == False
        
        # Test with page size larger than total count
        cursor = '{"offset": 0, "page_size": 10}'
        result = await flows_module._list_flows_impl(cursor)
        
        assert result["pagination"]["page_size"] == 10
        assert len(result["flows"]) == 4
        assert result["pagination"]["has_next"] == False
    
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_client_initialization_error(self, mock_ensure_client):
        """Test that list_flows handles client initialization errors correctly."""
        mock_ensure_client.side_effect = ConnectionError("Failed to connect to Homey")
        
        result = await flows_module._list_flows_impl()
        
        assert "error" in result
        assert "Failed to list flows" in result["error"]
        assert "Failed to connect to Homey" in result["error"]
        
    @pytest.mark.asyncio
    @patch('homey_mcp.tools.flows.ensure_client')
    async def test_list_flows_preserves_all_flow_properties(self, mock_ensure_client):
        """Test that list_flows preserves all original flow properties while adding flow_type."""
        mock_client = AsyncMock()
        
        # Create a normal flow with complex properties
        normal_flow = MagicMock()
        normal_flow.id = "normal_flow_123"
        normal_flow.name = "Normal Flow"
        normal_flow.enabled = True
        normal_flow.model_dump.return_value = {
            "id": "normal_flow_123",
            "name": "Normal Flow",
            "enabled": True,
            "tags": ["tag1", "tag2"],
            "folder": {"id": "folder_1", "name": "Folder 1"},
            "trigger": {"type": "device", "id": "device_1"},
            "conditions": [{"type": "time", "value": "12:00"}],
            "actions": [{"type": "device", "id": "device_2", "action": "toggle"}],
            "created": "2023-01-01T12:00:00Z",
            "modified": "2023-01-02T12:00:00Z"
        }
        
        # Create an advanced flow with different complex properties
        advanced_flow = MagicMock()
        advanced_flow.id = "advanced_flow_456"
        advanced_flow.name = "Advanced Flow"
        advanced_flow.enabled = False
        advanced_flow.model_dump.return_value = {
            "id": "advanced_flow_456",
            "name": "Advanced Flow",
            "enabled": False,
            "tags": ["tag3"],
            "folder": None,
            "cards": [
                {"type": "trigger", "id": "trigger_1", "args": {"device": "device_3"}},
                {"type": "condition", "id": "condition_1", "args": {"value": 10}},
                {"type": "action", "id": "action_1", "args": {"device": "device_4"}}
            ],
            "broken": False,
            "created": "2023-02-01T12:00:00Z",
            "modified": "2023-02-02T12:00:00Z"
        }
        
        mock_client.flows.get_flows.return_value = [normal_flow]
        mock_client.flows.get_advanced_flows.return_value = [advanced_flow]
        
        mock_ensure_client.return_value = mock_client
        
        result = await flows_module._list_flows_impl()
        
        # Verify both flows are returned
        assert len(result["flows"]) == 2
        
        # Find normal and advanced flows in the result
        normal_flow_result = next((f for f in result["flows"] if f["id"] == "normal_flow_123"), None)
        advanced_flow_result = next((f for f in result["flows"] if f["id"] == "advanced_flow_456"), None)
        
        # Verify normal flow properties are preserved
        assert normal_flow_result is not None
        assert normal_flow_result["flow_type"] == "normal"
        assert normal_flow_result["name"] == "Normal Flow"
        assert normal_flow_result["enabled"] is True
        assert normal_flow_result["tags"] == ["tag1", "tag2"]
        assert normal_flow_result["folder"] == {"id": "folder_1", "name": "Folder 1"}
        assert normal_flow_result["trigger"]["type"] == "device"
        assert len(normal_flow_result["conditions"]) == 1
        assert len(normal_flow_result["actions"]) == 1
        assert "created" in normal_flow_result
        assert "modified" in normal_flow_result
        
        # Verify advanced flow properties are preserved
        assert advanced_flow_result is not None
        assert advanced_flow_result["flow_type"] == "advanced"
        assert advanced_flow_result["name"] == "Advanced Flow"
        assert advanced_flow_result["enabled"] is False
        assert advanced_flow_result["tags"] == ["tag3"]
        assert advanced_flow_result["folder"] is None
        assert len(advanced_flow_result["cards"]) == 3
        assert advanced_flow_result["broken"] is False
        assert "created" in advanced_flow_result
        assert "modified" in advanced_flow_result