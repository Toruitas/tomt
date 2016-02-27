from flask import current_app

categories_list = current_app._get_current_object().config['CATEGORIES']

@current_app.context_processor
def inject_categories():
    print("I'm doing things!")
    return dict(categories_list=categories_list)

######### unused, done in the __init__ file