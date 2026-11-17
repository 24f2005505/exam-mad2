// template is in templates/examiner/dashboard.html
const ExaminerDashboard = {
    template: '#examiner-dashboard',
    components: { ExaminerExamination, ExaminerSlot, ExaminerEvaluation },
    data() {
        return {
            page: 'dashboard',  // which item of the examiner menu is open
           stats: {},
            examinations: [],
            menu: [
               { page: 'dashboard', name: 'Dashboard' },
                { page: 'examination', name: 'My Examinations' },
                	{ page: 'slot', name: 'My Slots' },
                { page: 'evaluation', name: 'Evaluations' }
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
                const data = await api('/api/examiner/dashboard')
                this.stats = data.stats
                this.examinations = data.examinations
			} catch (e) {
                this.$root.flash(e.message)
            }
        }
     }
}
