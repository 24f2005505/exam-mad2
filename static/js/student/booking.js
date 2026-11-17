// template is in templates/student/booking.html
const StudentBooking = {
    template: '#student-booking',
       data() {
        return {
            bookings: []
           }
    },
	created() {
        this.load()
    },
     methods: {
           async load() {
		    try {
                const data = await api('/api/student/booking')
                this.bookings = data.bookings
           } catch (e) {
               this.$root.flash(e.message)
            }
        },
        async cancel(booking) {
            if (!confirm('Cancel your booking for ' + booking.examination_name + '?')) return
            this.$root.clear()
           try {
                const data = await api('/api/student/booking/' + booking.id + '/cancel', 'POST')
                this.$root.flash(data.message)
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
          }
        }
    }
}
