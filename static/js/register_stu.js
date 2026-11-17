// template is in templates/register_stu.html
const RegisterStu = {
    template: '#register-stu',
    data() {
          return {
	        form: {
                fname: '', lname: '', username: '', email: '',
                password: '', con_password: '', gender: '',
	            university_name: '', major: '', gpa: ''
            }
        	}
       },
      methods: {
		async register() {
            this.$root.clear()
            	try {
               const data = await api('/api/register_student', 'POST', this.form)
                this.$root.go('login')
                this.$root.flash(data.message)
            } catch (e) {
                this.$root.flash(e.message)
            }
        }
   }
}
