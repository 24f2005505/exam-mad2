// template is in templates/login.html
const Login = {
    template: '#login',
     emits: ['logged-in'],
    data() {
		return {
			form: { username: '', password: '' }
         }
  },
    methods: {
          async login() {
            this.$root.clear()
            try {
                const data = await api('/api/login', 'POST', this.form)
                this.$root.flash(data.message)
                	this.$emit('logged-in', data.user)
	        } catch (e) {
                this.$root.flash(e.message)
          }
        }
    }
}
