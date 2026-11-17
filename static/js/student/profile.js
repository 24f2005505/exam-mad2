// template is in templates/student/profile.html
const StudentProfile = {
    template: '#student-profile',
    data() {
           return {
            username: '',
            form: { fname: '', lname: '', email: '', university: '', major: '', gpa: '', password: '', con_password: '' }
        }
    },
    created() {
        this.load()
    },
    methods: {
        fill(profile) {
            this.username = profile.username
            this.form = {
                fname: profile.fname, lname: profile.lname, email: profile.email,
                university: profile.university, major: profile.major, gpa: profile.gpa,
                 password: '', con_password: ''
            }
         },
        async load() {
	        try {
                const data = await api('/api/student/profile')
                this.fill(data.profile)
            } catch (e) {
                this.$root.flash(e.message)
          }
      },
        async save() {
		    this.$root.clear()
            try {
				const data = await api('/api/student/profile', 'PUT', this.form)
                this.$root.flash(data.message)
                this.fill(data.profile)
				this.$root.user.fname = data.profile.fname  // update the "Welcome" name in the navbar
            } catch (e) {
                this.$root.flash(e.message)
            }
        }
    }
}
