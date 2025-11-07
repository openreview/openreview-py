"""Decorators for requiring user confirmation on sensitive operations."""

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Union


def require_confirmation(
    func: Optional[Callable] = None,
    *,
    custom_message: Optional[Callable[[Dict[str, Any]], str]] = None
) -> Union[Callable, Callable[[Callable], Callable]]:
    """
    Decorator that requires user confirmation before executing sensitive operations.
    
    Automatically detects operation type (delete/post/clear) from function name and
    extracts relevant information from function arguments to generate confirmation messages.
    
    Args:
        func: The function to decorate (when used without parentheses)
        custom_message: Optional custom message formatter function that takes a dict of
            extracted parameters and returns a formatted message string
    
    The decorator respects a `dry_run` parameter if present in the function signature.
    When `dry_run=True`, confirmation is skipped.
    
    Example:
        @require_confirmation
        def delete_edges(self, invitation: str, label: Optional[str] = None):
            # ... implementation
        
        # Will prompt: "Deleting edges from {invitation} with label={label}. Type 'yes' to confirm: "
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Check for dry_run parameter
            sig = inspect.signature(f)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            dry_run = bound_args.arguments.get('dry_run', False)
            if dry_run:
                return f(*args, **kwargs)
            
            # Extract operation type from function name
            func_name = f.__name__
            operation_type = _detect_operation_type(func_name)
            
            # Extract relevant parameters
            extracted_params = _extract_parameters(bound_args.arguments, func_name)
            
            # Generate confirmation message
            if custom_message:
                message = custom_message(extracted_params)
            else:
                message = _generate_message(operation_type, extracted_params, func_name)
            
            # Prompt for confirmation
            response = input(f"{message} Type 'yes' to confirm: ").strip().lower()
            if response != 'yes':
                print("Operation cancelled.")
                return None
            
            # Execute the function
            return f(*args, **kwargs)
        
        return wrapper
    
    # Support both @require_confirmation and @require_confirmation()
    if func is None:
        return decorator
    else:
        return decorator(func)


def _detect_operation_type(func_name: str) -> str:
    """Detect operation type from function name."""
    func_lower = func_name.lower()
    
    if any(pattern in func_lower for pattern in ['delete', 'remove', 'clear', 'reset']):
        return 'delete'
    elif any(pattern in func_lower for pattern in ['post', 'create', 'add', 'commit']):
        return 'post'
    else:
        return 'modify'  # fallback for unknown operations


def _extract_parameters(arguments: Dict[str, Any], func_name: str) -> Dict[str, Any]:
    """Extract relevant parameters from function arguments for message generation."""
    extracted = {}
    
    # Extract invitation
    if 'invitation' in arguments:
        invitation = arguments['invitation']
        if invitation:
            extracted['invitation'] = invitation
    
    # Extract edges (could be a list)
    if 'edges' in arguments:
        edges = arguments['edges']
        if edges is not None:
            if isinstance(edges, (list, tuple)):
                extracted['edge_count'] = len(edges)
                extracted['edge_type'] = 'edges'
                # Try to extract invitation from first edge if it's a dict/list of dicts
                if edges and isinstance(edges[0], dict) and 'invitation' in edges[0]:
                    extracted['invitation'] = edges[0].get('invitation')
            else:
                extracted['edges'] = edges
    
    # Extract label
    if 'label' in arguments:
        label = arguments['label']
        if label:
            extracted['label'] = label
    
    # Extract head and tail (for filtering)
    filters = []
    if 'head' in arguments and arguments['head']:
        filters.append(f"head={arguments['head']}")
    if 'tail' in arguments and arguments['tail']:
        filters.append(f"tail={arguments['tail']}")
    if filters:
        extracted['filters'] = filters
    
    # Extract committee_group_id (common in assignment operations)
    if 'committee_group_id' in arguments:
        committee = arguments['committee_group_id']
        if committee:
            extracted['committee'] = committee
    
    # Extract from_label and to_label (for carry-over operations)
    if 'from_label' in arguments:
        extracted['from_label'] = arguments['from_label']
    if 'to_label' in arguments:
        extracted['to_label'] = arguments['to_label']
    
    return extracted


def _generate_message(
    operation_type: str,
    extracted_params: Dict[str, Any],
    func_name: str
) -> str:
    """Generate a human-readable confirmation message."""
    parts = []
    
    # Operation verb
    if operation_type == 'delete':
        verb = "Deleting"
    elif operation_type == 'post':
        verb = "Posting"
    else:
        verb = "Modifying"
    
    # Count and type
    if 'edge_count' in extracted_params:
        count = extracted_params['edge_count']
        edge_type = extracted_params.get('edge_type', 'edges')
        parts.append(f"{verb} {count} {edge_type}")
    elif operation_type == 'delete':
        parts.append(f"{verb} edges")
    elif operation_type == 'post':
        parts.append(f"{verb} edges")
    else:
        parts.append(f"{verb} data")
    
    # Invitation
    if 'invitation' in extracted_params:
        parts.append(f"from {extracted_params['invitation']}")
    elif operation_type == 'post' and 'invitation' not in extracted_params:
        parts.append("(invitation will be determined from edge data)")
    
    # Filters
    if 'filters' in extracted_params:
        parts.append(f"with {', '.join(extracted_params['filters'])}")
    
    # Label
    if 'label' in extracted_params:
        parts.append(f"label={extracted_params['label']}")
    
    # Committee
    if 'committee' in extracted_params:
        parts.append(f"for committee {extracted_params['committee']}")
    
    # From/to labels (for carry-over operations)
    if 'from_label' in extracted_params and 'to_label' in extracted_params:
        parts.append(
            f"from label '{extracted_params['from_label']}' "
            f"to label '{extracted_params['to_label']}'"
        )
    
    message = " ".join(parts) + "."
    return message

