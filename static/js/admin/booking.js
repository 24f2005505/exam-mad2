// template is in templates/admin/booking.html
const AdminBooking = {
    template: '#admin-booking',
    data() {
       return {
              bookings: [],
            query: '',
             moving: null,      // booking being rescheduled
            slotOptions: [],   // other slots of the same examination with free seats
               newSlotId: ''
          }
    },
    created() {
          this.load()
    },
    methods: {
        async load() {
            try {
                const data = await api('/api/admin/booking?query=' + encodeURIComponent(this.query))
                this.bookings = data.bookings
	        } catch (e) {
               this.$root.flash(e.message)
            }
        },
        async openMove(booking) {
            this.moving = booking
            this.newSlotId = ''
            try {
                  const data = await api('/api/admin/slot?examination_id=' + booking.examination_id)
                 this.slotOptions = data.slots.filter(slot => slot.id !== booking.slot_id && slot.status === 'available' && slot.available_seats > 0)
			} catch (e) {
                this.$root.flash(e.message)
            }
            window.scrollTo(0, 0)
        },
        async reschedule() {
            this.$root.clear()
            try {
                 const data = await api('/api/admin/booking/' + this.moving.id + '/reschedule', 'POST', { slot_id: this.newSlotId })
              this.$root.flash(data.message)
                 this.moving = null
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
        }
  }
}
