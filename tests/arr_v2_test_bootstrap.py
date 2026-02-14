import inspect


def _invoke_test_method(instance, method_name, fixture_values):
    method = getattr(instance, method_name)
    signature = inspect.signature(method)
    kwargs = {}
    for parameter in signature.parameters.values():
        if parameter.name == 'self':
            continue
        if parameter.name not in fixture_values:
            raise KeyError(f'Missing fixture value for "{parameter.name}" while invoking "{method_name}"')
        kwargs[parameter.name] = fixture_values[parameter.name]
    method(**kwargs)


def ensure_prior_methods(instance, ordered_methods, completed_methods, current_method, fixture_values):
    if current_method not in ordered_methods:
        return
    current_index = ordered_methods.index(current_method)
    for method_name in ordered_methods[:current_index]:
        if method_name in completed_methods:
            continue
        _invoke_test_method(instance, method_name, fixture_values)
        completed_methods.add(method_name)


def ensure_all_methods(instance, ordered_methods, completed_methods, fixture_values):
    for method_name in ordered_methods:
        if method_name in completed_methods:
            continue
        _invoke_test_method(instance, method_name, fixture_values)
        completed_methods.add(method_name)
