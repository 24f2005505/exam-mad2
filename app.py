from make_app import init_app
from make_form import make_form
from make_login import make_login
import make_admin_dashboard
import make_student_dashboard
import make_examiner_dashboard
from make_homepage import make_homepage
app = init_app()

make_homepage(app)
## from vue forms saves data and handles everything
make_form(app)
make_login(app)
make_admin_dashboard.make_dashboard(app)
make_student_dashboard.make_dashboard(app)
make_examiner_dashboard.make_dashboard(app)


if __name__ == '__main__':
    app.run(debug=True)
