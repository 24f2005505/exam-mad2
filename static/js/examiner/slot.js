// template is in templates/examiner/slot.html
const ExaminerSlot = {
      template: '#examiner-slot',
    data() {
        return {
              slots: [],
            editingSlot: null,   // slot being edited
            form: {},
           studentsSlot: null,  // slot whose students are shown
	        students: []
        }
       },
    created() {
		this.load()
  },
    methods: {
        async load() {
            try {
                const data = await api('/api/examiner/slot')
                this.slots = data.slots
            } catch (e) {
                this.$root.flash(e.message)
          }
           },
        edit(slot) {
            this.editingSlot = slot
		    this.form = {
                 date: slot.date, start_time: slot.start_time, end_time: slot.end_time,
                max_student_capacity: slot.max_student_capacity, meeting_link: slot.meeting_link
            }
              window.scrollTo(0, 0)
        },
      async save() {
            this.$root.clear()
          try {
                const data = await api('/api/examiner/slot/' + this.editingSlot.id, 'PUT', this.form)
                this.$root.flash(data.message)
	            this.editingSlot = null
                  this.load()
            } catch (e) {
                this.$root.flash(e.message)
            	}
        },
        async remove(slot) {
            if (!confirm('Remove this slot?')) return
           this.$root.clear()
            try {
              const data = await api('/api/examiner/slot/' + slot.id, 'DELETE')
                this.$root.flash(data.message)
              this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
        	},
        async complete(slot) {
            this.$root.clear()
            try {
                const data = await api('/api/examiner/slot/' + slot.id + '/complete', 'POST')
                this.$root.flash(data.message)
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
	    },
        async showStudents(slot) {
             try {
               const data = await api('/api/examiner/slot/' + slot.id + '/students')
                this.studentsSlot = slot
                this.students = data.bookings
                	window.scrollTo(0, 0)
            } catch (e) {
                this.$root.flash(e.message)
          }
	    }
    	}
}
