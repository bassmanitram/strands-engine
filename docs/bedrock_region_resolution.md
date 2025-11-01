# AWS Region Resolution for Bedrock Adapter

## Overview

The Bedrock adapter now includes automatic AWS region resolution that follows AWS SDK conventions. This ensures that the `region_name` parameter is properly set when creating `BedrockModel` instances.

## Resolution Hierarchy

The region is resolved using the following priority order (highest to lowest):

1. **Existing `region_name` in `model_config`** (highest priority)
   - If already set, it is never overridden
   - This preserves explicit configuration

2. **`AWS_REGION` environment variable**
   - Standard AWS environment variable
   - Takes precedence over other sources

3. **`AWS_DEFAULT_REGION` environment variable**
   - Fallback environment variable
   - Used if `AWS_REGION` is not set

4. **AWS Profile Configuration (`AWS_PROFILE`)**
   - Reads `~/.aws/config` file
   - Supports profile inheritance via `source_profile`
   - Handles circular references safely

5. **None** (lowest priority)
   - If no region is found, `region_name` is not set
   - Allows boto3 to use its own default resolution

## Usage Examples

### Example 1: Explicit Region in Config
```python
from strands_agent_factory.adapters.bedrock import BedrockAdapter

adapter = BedrockAdapter()
config = {
    "model_id": "anthropic.claude-3-sonnet",
    "region_name": "eu-west-1"  # This will be used
}
model = adapter.load_model(model_config=config)
```

### Example 2: Environment Variable
```python
import os
os.environ['AWS_REGION'] = 'us-east-1'

adapter = BedrockAdapter()
config = {"model_id": "anthropic.claude-3-sonnet"}
model = adapter.load_model(model_config=config)
# Uses region: us-east-1
```

### Example 3: AWS Profile
```bash
# ~/.aws/config
[profile production]
region = ap-southeast-1

[profile dev]
source_profile = production
```

```python
import os
os.environ['AWS_PROFILE'] = 'dev'

adapter = BedrockAdapter()
config = {"model_id": "anthropic.claude-3-sonnet"}
model = adapter.load_model(model_config=config)
# Uses region: ap-southeast-1 (from production profile)
```

## Profile Inheritance

The adapter supports AWS profile inheritance through the `source_profile` mechanism:

```ini
# ~/.aws/config
[profile dev]
source_profile = staging

[profile staging]
source_profile = prod

[profile prod]
region = us-west-2
```

When using profile `dev`, the adapter will:
1. Check `dev` for `region`
2. If not found, check `source_profile` → `staging`
3. Check `staging` for `region`
4. If not found, check `source_profile` → `prod`
5. Find `region` in `prod` → return `us-west-2`

### Circular Reference Protection

The adapter detects and handles circular profile references:

```ini
[profile dev]
source_profile = staging

[profile staging]
source_profile = dev  # Circular reference!
```

In this case, the adapter will:
- Detect the circular reference
- Log a debug message
- Return `None` (no region found)

## Error Handling

The region resolution is designed to be defensive and never crash:

| Scenario | Behavior |
|----------|----------|
| Config file not found | Return `None`, log debug message |
| Malformed config file | Return `None`, log debug message |
| Profile not found | Return `None`, log debug message |
| Circular references | Return `None`, log debug message |
| Permission errors | Return `None`, log debug message |
| Unicode in config | Handled correctly |

## Implementation Details

### Functions

#### `_resolve_region_name(model_config: Dict[str, Any]) -> Optional[str]`
Main function that implements the resolution hierarchy.

**Parameters:**
- `model_config`: Model configuration dictionary

**Returns:**
- Resolved region name, or `None` if not found

**Example:**
```python
from strands_agent_factory.adapters.bedrock import _resolve_region_name

region = _resolve_region_name({})
print(region)  # e.g., 'us-east-1' from AWS_REGION
```

#### `_resolve_region_from_profile(profile_name: str, visited: Optional[Set[str]] = None) -> Optional[str]`
Resolves region from AWS config file with profile inheritance.

**Parameters:**
- `profile_name`: AWS profile name to look up
- `visited`: Set of visited profiles (for circular reference detection)

**Returns:**
- Region name if found, `None` otherwise

**Example:**
```python
from strands_agent_factory.adapters.bedrock import _resolve_region_from_profile

region = _resolve_region_from_profile("production")
print(region)  # e.g., 'eu-west-1'
```

## Testing

The implementation includes comprehensive tests covering:

### Resolution Priority (7 tests)
- Existing region_name preservation
- Environment variable precedence
- Config vs environment priority

### Profile Resolution (11 tests)
- Simple profile lookup
- Default profile handling
- Profile inheritance chains
- Circular reference detection
- Missing profiles/files
- Malformed config files

### Integration Tests (8 tests)
- `BedrockAdapter.load_model()` integration
- Interaction with `boto_client_config`
- Model name parameter handling

### Edge Cases (9 tests)
- Empty profile names
- Whitespace in names
- Comments in config files
- Unicode characters
- Special region formats (us-gov-*)
- Permission errors
- Multiple profiles with same region

**Total: 35 comprehensive tests, all passing**

## Performance Considerations

- Config file is only read if `AWS_PROFILE` is set
- Config parsing uses Python's built-in `configparser`
- Circular reference detection uses set for O(1) lookups
- No unnecessary file I/O

## Logging

The implementation provides debug logging at key points:

```python
logger.debug(f"Using existing region_name from config: {existing}")
logger.debug(f"Resolved region_name from AWS_REGION: {region}")
logger.debug(f"Resolved region_name from AWS_DEFAULT_REGION: {region}")
logger.debug(f"Attempting to resolve region from AWS_PROFILE: {profile}")
logger.debug(f"Resolved region_name from profile '{profile}': {region}")
logger.debug(f"Found region '{region}' in profile '{profile_name}'")
logger.debug(f"Following source_profile: {profile_name} -> {source_profile}")
logger.debug(f"Circular profile reference detected: {profile_name}")
logger.debug(f"Profile section not found: {section_name}")
logger.debug(f"AWS config file not found: {config_path}")
logger.debug(f"Failed to parse AWS config for profile '{profile_name}': {e}")
logger.debug("No region_name resolved, will use boto3 defaults")
```

## Compatibility

- **Python**: 3.8+
- **AWS SDK**: Compatible with boto3 region resolution conventions
- **Config Format**: Standard AWS config file format (`~/.aws/config`)
- **Profile Names**: Supports any valid AWS profile name including:
  - Names with spaces
  - Names with unicode characters
  - Default profile
  - GovCloud regions

## Migration Notes

If you have existing code that explicitly sets `region_name`:

**Before:**
```python
config = {
    "model_id": "anthropic.claude-3-sonnet",
    "region_name": "us-east-1"
}
```

**After:**
```python
# Option 1: Keep explicit (still works, not overridden)
config = {
    "model_id": "anthropic.claude-3-sonnet",
    "region_name": "us-east-1"  # Still respected
}

# Option 2: Use environment variable
os.environ['AWS_REGION'] = 'us-east-1'
config = {
    "model_id": "anthropic.claude-3-sonnet"
}

# Option 3: Use AWS profile
os.environ['AWS_PROFILE'] = 'production'
config = {
    "model_id": "anthropic.claude-3-sonnet"
}
```

All three approaches work correctly and are fully supported.
