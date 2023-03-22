
def setup(app):
    # Begin and end a reference to another code block
    app.add_config_value("lit_begin_ref", "{{", 'html', [str])
    app.add_config_value("lit_end_ref", "}}", 'html', [str])

    # Turn this to False if you want to define your own style (js and css files)
    app.add_config_value("lit_use_default_style", True, 'html', [bool])
