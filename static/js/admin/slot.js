// template is in templates/admin/slot.html
const AdminSlot = {
    template: '#admin-slot',
    data() {
        return {
            slots: [],
             examinations: [],
            examiners: [],
            examFilter: '',
            	editingSlot: null,  // slot being rescheduled
            form: {}
        }
    },
    async created() {
        this.load()
           try {
            this.examinations = (await api('/api/admin/examination')).examinations
            this.examiners = (await api('/api/admin/examiner')).examiners.filter(examiner => examiner.status === 'active')
        } catch (e) {
            this.$root.flash(e.message)
	    }
    },
    methods: {
        	async load() {
            try {
                 const data = await api('/api/admin/slot?examination_id=' + this.examFilter)
                this.slots = data.slots
              } catch (e) {
                this.$root.flash(e.message)
	        }
        },
	    edit(slot) {
            this.editingSlot = slot
            this.form = {
                 date: slot.date, start_time: slot.start_time, end_time: slot.end_time, examiner_id: slot.examiner_id,
                   max_student_capacity: slot.max_student_capacity, meeting_link: slot.meeting_link
            }
            window.scrollTo(0, 0)
           },
        async save() {
          this.$root.clear()
              try {
                const data = await api('/api/admin/slot/' + this.editingSlot.id, 'PUT', this.form)
                	this.$root.flash(data.message)
                this.editingSlot = null
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
        },
      async cancel(slot) {
			if (!confirm('Cancel this slot? All its bookings will be cancelled.')) return
            this.$root.clear()
		    try {
                const data = await api('/api/admin/slot/' + slot.id + '/cancel', 'POST')
                this.$root.flash(data.message)
                 this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
        }
   }
}
