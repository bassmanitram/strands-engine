"""
Consolidated tool factory for strands_agent_factory.

Orchestrates tool discovery, loading, and specification creation by delegating
to specialized modules for each tool type.
"""

from pathlib import Path
from typing import List, Optional

from loguru import logger

from strands_agent_factory.messaging.content import load_structured_file
from strands_agent_factory.tools.python import import_python_item

from ..core.types import EnhancedToolSpec, PathLike, ToolConfig
from .a2a import create_a2a_tool_spec
from .mcp import create_mcp_tool_spec
from .types import (
    CONFIG_FIELD_DISABLED,
    CONFIG_FIELD_ERROR,
    CONFIG_FIELD_FUNCTIONS,
    CONFIG_FIELD_ID,
    CONFIG_FIELD_MODULE_PATH,
    CONFIG_FIELD_PACKAGE_PATH,
    CONFIG_FIELD_SOURCE_FILE,
    CONFIG_FIELD_TYPE,
    DEFAULT_PYTHON_TOOL_ID,
    DEFAULT_TOOL_ID,
    ERROR_MSG_NO_TOOLS_LOADED,
    ERROR_MSG_PYTHON_CONFIG_MISSING_FIELDS,
    ERROR_MSG_TOOL_DISABLED,
    ERROR_MSG_UNEXPECTED_ERROR,
    ERROR_MSG_UNKNOWN_TOOL_TYPE,
    MCP_TOOL_TYPES,
    TOOL_TYPE_A2A,
    TOOL_TYPE_PYTHON,
    ToolSpecData,
)
from .utils import (
    create_failed_config,
    extract_tool_names,
    get_config_value,
    validate_required_fields,
)


class ToolFactory:
    """
    Centralized factory for tool discovery, loading, and specification creation.

    ToolFactory coordinates the complete tool specification management lifecycle for
    strands_agent_factory, from configuration file discovery through tool specification
    creation. Delegates to specialized modules for each tool type.
    """

    def __init__(self, file_paths: List[PathLike]) -> None:
        """
        Initialize ToolFactory with configuration file paths.

        Args:
            file_paths: List of paths to tool configuration files
        """
        if logger.level("TRACE").no >= logger._core.min_level:
            logger.trace(
                "ToolFactory.__init__ called with {} file paths",
                len(file_paths) if file_paths else 0,
            )

        # Load configurations at construction time
        self._tool_configs: List[ToolConfig] = (
            self._load_tool_configs(file_paths) if file_paths else []
        )

        if logger.level("TRACE").no >= logger._core.min_level:
            logger.trace(
                "ToolFactory.__init__ completed with {} tool configs created",
                len(self._tool_configs),
            )

    def create_tool_specs(self) -> List[EnhancedToolSpec]:
        """
        Create tool specifications from loaded configurations.

        Returns:
            List[EnhancedToolSpec]: List of enhanced tool specification dictionaries with context
        """
        if logger.level("TRACE").no >= logger._core.min_level:
            logger.trace(
                "create_tool_specs called with {} tool configs", len(self._tool_configs)
            )

        if not self._tool_configs:
            logger.debug("create_tool_specs returning empty results (no configs)")
            return []

        creation_results: List[EnhancedToolSpec] = []

        for tool_config in self._tool_configs:
            enhanced_spec = self._enhance_tool_spec(tool_config)
            creation_results.append(enhanced_spec)

        logger.debug(
            "create_tool_specs returning {} enhanced specs", len(creation_results)
        )
        return creation_results

    def _enhance_tool_spec(self, tool_config: ToolConfig) -> EnhancedToolSpec:
        """Enhance a single tool config with loaded tool data."""
        # Start with the original config for context
        enhanced_spec: EnhancedToolSpec = dict(tool_config)  # type: ignore

        # Handle disabled tools
        if get_config_value(tool_config, CONFIG_FIELD_DISABLED, False):
            tool_id = get_config_value(tool_config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)
            logger.info("Skipping disabled tool: {}", tool_id)
            enhanced_spec[CONFIG_FIELD_ERROR] = ERROR_MSG_TOOL_DISABLED
            return enhanced_spec

        # Handle tools with existing errors
        existing_error = get_config_value(tool_config, CONFIG_FIELD_ERROR, None)
        if existing_error:
            tool_id = get_config_value(tool_config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)
            logger.info(
                "Skipping tool found to be in error: {} - {}", tool_id, existing_error
            )
            return enhanced_spec

        # Process valid tools
        tool_id = get_config_value(tool_config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)
        logger.debug("Creating tool spec for config: {}", tool_id)

        # Create the tool spec and enhance the original config with it
        tool_spec_data = self.create_tool_from_config(tool_config)

        # Merge the tool spec data into the enhanced spec
        if CONFIG_FIELD_ERROR in tool_spec_data:
            enhanced_spec[CONFIG_FIELD_ERROR] = tool_spec_data[CONFIG_FIELD_ERROR]
        else:
            # Merge successful tool spec data
            if "tools" in tool_spec_data:
                enhanced_spec["tools"] = tool_spec_data["tools"]
            if "client" in tool_spec_data:
                enhanced_spec["client"] = tool_spec_data["client"]

            # Extract tool names from loaded tools
            if enhanced_spec.get("tools"):
                enhanced_spec["tool_names"] = extract_tool_names(enhanced_spec["tools"])
            elif enhanced_spec.get("client"):
                # For MCP tools, tool_names will be populated later during agent initialization
                enhanced_spec["tool_names"] = []

        return enhanced_spec

    def create_tool_from_config(self, config: ToolConfig) -> ToolSpecData:
        """
        Create tool specification from a single configuration dictionary.

        Dispatches to specialized handlers based on tool type.

        Args:
            config: Tool configuration dictionary

        Returns:
            ToolSpecData: Tool specification data to merge into enhanced spec
        """
        tool_type = get_config_value(config, CONFIG_FIELD_TYPE)
        tool_id = get_config_value(config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)

        logger.trace(
            "create_tool_from_config called for type='{}', id='{}'", tool_type, tool_id
        )

        # Dispatch to tool type handlers
        if tool_type == TOOL_TYPE_PYTHON:
            return self._create_python_tool_spec(config)
        elif tool_type in MCP_TOOL_TYPES:
            return create_mcp_tool_spec(config)
        elif tool_type == TOOL_TYPE_A2A:
            return create_a2a_tool_spec(config)
        else:
            logger.warning(
                "Tool '{}' has unknown type '{}'. Skipping.", tool_id, tool_type
            )
            return ToolSpecData(error=ERROR_MSG_UNKNOWN_TOOL_TYPE.format(tool_type))

    def _create_python_tool_spec(self, config: ToolConfig) -> ToolSpecData:
        """Create Python tool specification directly."""
        tool_id = get_config_value(config, CONFIG_FIELD_ID, DEFAULT_PYTHON_TOOL_ID)
        logger.trace("_create_python_tool_spec called for tool_id='{}'", tool_id)

        try:
            # Validate required configuration
            validation_error = validate_required_fields(
                config,
                [
                    CONFIG_FIELD_ID,
                    CONFIG_FIELD_MODULE_PATH,
                    CONFIG_FIELD_FUNCTIONS,
                    CONFIG_FIELD_SOURCE_FILE,
                ],
            )
            if validation_error:
                logger.error(
                    "Python tool '{}' configuration invalid: {}",
                    tool_id,
                    validation_error,
                )
                return ToolSpecData(error=ERROR_MSG_PYTHON_CONFIG_MISSING_FIELDS)

            # Extract configuration
            module_path = get_config_value(config, CONFIG_FIELD_MODULE_PATH)
            func_names = get_config_value(config, CONFIG_FIELD_FUNCTIONS, [])
            package_path = get_config_value(config, CONFIG_FIELD_PACKAGE_PATH)
            src_file = get_config_value(config, CONFIG_FIELD_SOURCE_FILE)

            logger.debug(
                "Python tool spec: id={}, module_path={}, functions={}",
                tool_id,
                module_path,
                func_names,
            )

            # Load tools
            loaded_tools = self._load_python_functions(
                tool_id, module_path, func_names, package_path, src_file
            )

            if not loaded_tools:
                error_msg = ERROR_MSG_NO_TOOLS_LOADED.format(module_path)
                if func_names:
                    error_msg += " for functions: {}".format(func_names)
                logger.error(error_msg)
                return ToolSpecData(error=error_msg)

            logger.info(
                "Successfully loaded {} tools from Python module: {}",
                len(loaded_tools),
                tool_id,
            )
            return ToolSpecData(tools=loaded_tools, client=None)

        except Exception as e:
            tool_type = get_config_value(config, CONFIG_FIELD_TYPE, DEFAULT_TOOL_ID)
            formatted_msg = ERROR_MSG_UNEXPECTED_ERROR.format(tool_type, tool_id, e)
            logger.warning(formatted_msg)
            return ToolSpecData(error=formatted_msg)

    def _load_python_functions(
        self,
        tool_id: str,
        module_path: str,
        func_names: List[str],
        package_path: Optional[str],
        src_file: str,
    ) -> List:
        """Load Python functions from module."""
        # Resolve base path for package_path resolution
        base_path: Optional[Path] = None
        if package_path and src_file:
            base_path = Path(src_file).parent
            logger.debug("Using base path from source file: {}", base_path)

        loaded_tools: List = []

        # Look for the specific function names requested in the config
        for func_spec in func_names:
            if not isinstance(func_spec, str):
                logger.warning(
                    "Function spec '{}' is not a string in tool config '{}'. Skipping.",
                    func_spec,
                    tool_id,
                )
                continue

            try:
                logger.debug(
                    "Attempting to load function '{}' from module '{}' (package_path '{}')",
                    func_spec,
                    module_path,
                    package_path,
                )
                tool = import_python_item(
                    module_path, func_spec, package_path, base_path
                )
                loaded_tools.append(tool)

                # Clean up the tool name to remove path prefixes
                clean_function_name = func_spec.split(".")[-1]
                logger.debug(
                    "Successfully loaded callable '{}' as '{}' from module '{}'",
                    func_spec,
                    clean_function_name,
                    module_path,
                )

            except (ImportError, AttributeError, FileNotFoundError) as e:
                logger.warning(
                    "Error loading function '{}' from module '{}' (package_path '{}'): {}",
                    func_spec,
                    module_path,
                    package_path,
                    e,
                )
                continue

        return loaded_tools

    def _load_tool_configs(self, file_paths: List[PathLike]) -> List[ToolConfig]:
        """
        Load tool configurations from configuration files.

        Args:
            file_paths: List of file paths to configuration files

        Returns:
            List[ToolConfig]: Successfully loaded configs with error info for failed ones
        """
        if logger.level("TRACE").no >= logger._core.min_level:
            logger.trace(
                "_load_tool_configs called with {} file paths", len(file_paths)
            )

        path_list = file_paths or []
        loaded_configs: List[ToolConfig] = []
        good = 0
        bad = 0

        if logger.level("DEBUG").no >= logger._core.min_level:
            logger.debug("Loading {} tool configuration files...", len(path_list))

        for file_path in path_list:
            try:
                file_path = Path(file_path)
                config_data = load_structured_file(file_path)

                # Add source file reference for debugging
                config_data[CONFIG_FIELD_SOURCE_FILE] = str(file_path)

                # Configuration validation is performed during creation
                loaded_configs.append(config_data)  # type: ignore
                logger.info(
                    "Loaded tool config '{}' from {}",
                    get_config_value(config_data, CONFIG_FIELD_ID, DEFAULT_TOOL_ID),
                    file_path,
                )
                good += 1
            except Exception as e:
                failed_config = create_failed_config(file_path, e)
                loaded_configs.append(failed_config)
                bad += 1
                # Warn this exception - no stack tracing needed
                logger.warning("Error loading tool config '{}': {}", file_path, e)

        logger.debug(
            "Tool discovery complete: {} successful, {} failed from {} files",
            good,
            bad,
            len(path_list),
        )
        return loaded_configs
