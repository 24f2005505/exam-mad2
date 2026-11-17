// template is in templates/student/dashboard.html
const StudentDashboard = {
    template: '#student-dashboard',
     components: { StudentExamination, StudentBooking, StudentProfile },
    data() {
       return {
		    page: 'dashboard',  // which item of the student menu is open
            stats: {},
            upcoming: [],
            results: [],
            exporting: false,
            downloadUrl: '',
            menu: [
                 { page: 'dashboard', name: 'Dashboard' },
                   { page: 'examination', name: 'Examinations' },
                   { page: 'booking', name: 'My Bookings / History' },
                  { page: 'profile', name: 'My Profile' }
            ]
		}
    },
    created() {
        this.loadStats()
    },
    methods: {
        open(page) {
            this.$root.clear()
            this.page = page
            if (page === 'dashboard') this.loadStats()
        },
        async loadStats() {
              try {
                const data = await api('/api/student/dashboard')
                this.stats = data.stats
                this.upcoming = data.upcoming
                this.results = data.results
               } catch (e) {
                this.$root.flash(e.message)
            }
        },
        async exportCsv() {
            // starts the celery job, then checks every 2 seconds if the file is ready
            this.$root.clear()
		    this.downloadUrl = ''
             let taskId
               try {
              const data = await api('/api/student/export', 'POST')
                taskId = data.task_id
                this.$root.flash(data.message)
            } catch (e) {
                this.$root.flash(e.message)
                	return
            }
            this.exporting = true
            for (let i = 0; i < 30; i++) {
                await new Promise(resolve => setTimeout(resolve, 2000))
		        try {
                       const status = await api('/api/student/export/' + taskId)
                    	if (status.ready) {
                        this.downloadUrl = '/api/student/export/' + taskId + '/download'
                      this.$root.clear()
                        this.$root.flash('Your examination history CSV is ready. Click Download CSV.')
                        alert('Your examination history CSV is ready!')
                        break
                  }
                } catch (e) {
                    	this.$root.flash(e.message)
                     break
               }
            	}
            if (!this.downloadUrl) this.$root.flash('Export is taking too long, is the Celery worker running?')
           this.exporting = false
           }
    }
}
