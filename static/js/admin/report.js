// template is in templates/admin/report.html, charts are made with chart.js
let reportCharts = []  // kept outside vue data so vue does not make the charts reactive

const AdminReport = {
    template: '#admin-report',
       data() {
        return {
          examinations: [],
            examiners: []
        }
    },
   async created() {
        try {
          const data = await api('/api/admin/report')
            this.examinations = data.examinations
               this.examiners = data.examiners
             this.$nextTick(this.drawCharts)  // wait for the canvas to be on the page
        } catch (e) {
            this.$root.flash(e.message)
           }
    },
    unmounted() {
        reportCharts.forEach(chart => chart.destroy())
        reportCharts = []
    },
   methods: {
        drawCharts() {
            reportCharts.forEach(chart => chart.destroy())
            reportCharts = [
                new Chart(this.$refs.bookingChart, {
                    type: 'bar',
                    data: {
                        labels: this.examinations.map(exam => exam.examination_name),
                        datasets: [
                            { label: 'Bookings', data: this.examinations.map(exam => exam.total_bookings) },
                            { label: 'Evaluated', data: this.examinations.map(exam => exam.evaluated) }
                        ]
                    },
                    options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
                }),
                new Chart(this.$refs.examinerChart, {
                  type: 'bar',
                    data: {
                       labels: this.examiners.map(examiner => examiner.name),
                        datasets: [
                            { label: 'Evaluations done', data: this.examiners.map(examiner => examiner.evaluations_done) },
                          { label: 'Pending', data: this.examiners.map(examiner => examiner.pending_evaluations) }
                        ]
			        },
					options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
                })
            ]
        }
    }
}
