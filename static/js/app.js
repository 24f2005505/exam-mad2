// main vue app, uses templates/base.html as its template
const app = Vue.createApp({
   template: '#base',
   components: { Login, RegisterStu, AdminDashboard, StudentDashboard, ExaminerDashboard },
    data() {
           return {
           user: null,      // logged in user (null if not logged in)
            loading: true,
			page: 'login',   // login or register, when not logged in
            messages: [],    // like flask flash messages
            viewKey: 0       // changing this resets the dashboard to its first page
        }
    },
    async created() {
        // ask flask who is logged in (session cookie)
        try {
            const data = await api('/api/me')
            this.user = data.user
           } catch (e) {
            this.flash(e.message)
		}
        this.loading = false
    	},
    methods: {
        flash(msg) {
           this.messages.push(msg)
            window.scrollTo(0, 0)
		},
        	clear() {
             this.messages = []
           },
        go(page) {
            this.clear()
            this.page = page
	        this.viewKey++
        },
		setUser(user) {
            this.user = user
        },
         async logout() {
            	try {
                 await api('/api/logout', 'POST')
               } catch (e) {}
            this.user = null
	        this.go('login')
            this.flash('Logged out successfully!')
        }
	}
})

// label() and dt() from api.js can be used in every template
app.config.globalProperties.label = label
app.config.globalProperties.dt = dt

app.mount('#app')
