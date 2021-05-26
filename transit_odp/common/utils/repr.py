def nice_repr(instance):
    class_name = instance.__class__.__name__
    attrs = ", ".join(
        f"{key}={value!r}"
        for key, value in instance.__dict__.items()
        if not key.startswith("_")
    )
    return f"{class_name}({attrs})"
