def process(client, edit, invitation):
    funcs = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_revision/validate_final_author_list.py}}", funcs)
    funcs['validate_final_author_list'](client, edit)
