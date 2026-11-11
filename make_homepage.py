from flask import render_template


def make_homepage(app):
    ## jinja is only used for this entry point, everything else is vue
    @app.route('/index')
    @app.route('/')
    def index():
        return render_template('index.html')
