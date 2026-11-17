// template is in templates/admin/dashboard.html
const AdminDashboard = {
    template: '#admin-dashboard',
    components: { AdminCourse, AdminExamination, AdminExaminer, 
        AdminStudent, AdminSlot, AdminBooking, AdminReport },
    data() 
      
    {
        return {page: 'dashboard',// which item of the admin menu is open
            stats: {},
		    menu: [
        { page: 'dashboard', name: 'Dashboard' },
        { page:'course', name: 'Courses' },
        { page:'examination', name:'Examinations' },
        { page: 'examiner', name: 'Examiners' },
        { page: 'student', name: 'Students' },
        { page:'slot', name: 'Examination Slots' },
        { page: 'booking', name: 'Bookings' },
        { page:'report', name:'Reports' }]}
            
    },

	created() {this.loadStats()},
	
    methods: {
        open(page) {
		    this.$root.clear()
            this.page = page
            if (page === 'dashboard') this.loadStats()
        },
        async loadStats() {
           try {
                this.stats = await api('/api/admin/dashboard')
            } catch (e) {this.$root.flash(e.message)
            }}}}
