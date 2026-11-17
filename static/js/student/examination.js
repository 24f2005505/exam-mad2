// template is in templates/student/examination.html
const StudentExamination = {
    template: '#student-examination',
	data() {
        return {
          examinations: [],
            courses: [],
            query: '',
          type: '',
            courseId: '',
            slotExam: null,  // examination whose slots are shown
            slots: []
        }
    },
       created() {
        this.load()
    },
    methods: {
        async load() {
            try {
                const url = '/api/student/examination?query=' + encodeURIComponent(this.query) + '&type=' + this.type + '&course_id=' + this.courseId
                const data = await api(url)
                this.examinations = data.examinations
                this.courses = data.courses
                if (this.slotExam) {
                    this.slotExam = this.examinations.find(exam => exam.id === this.slotExam.id) || null
                }
            } catch (e) {
                 this.$root.flash(e.message)
           }
        },
        hasBooking(exam) {
            return exam.my_booking === 'booked' || exam.my_booking === 'completed'
        },
		async showSlots(exam) {
            try {
                const data = await api('/api/student/examination/' + exam.id + '/slots')
              this.slotExam = exam
                this.slots = data.slots
                  window.scrollTo(0, 0)
            } catch (e) {
               this.$root.flash(e.message)
            }
        },
        async book(slot) {
          if (!confirm('Book the slot on ' + slot.date + ' at ' + slot.start_time + '?')) return
               this.$root.clear()
            try {
                const data = await api('/api/student/book', 'POST', { slot_id: slot.id })
                this.$root.flash(data.message)
                await this.load()
                   if (this.slotExam) this.showSlots(this.slotExam)
          } catch (e) {
			    this.$root.flash(e.message)
            }
        }
   }
}
