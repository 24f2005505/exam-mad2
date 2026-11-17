// template is in templates/examiner/examination.html
function emptySlotForm() {
    return { date: '', start_time: '', end_time: '', max_student_capacity: 1, meeting_link: '' }
}

const ExaminerExamination = {
    template: '#examiner-examination',
    data() {
           return {
            examinations: [],
            slotExam: null,  // examination we are creating a slot for
            form: emptySlotForm()
        }
    },
    created() {
        this.load()
    },
    methods: {
        async load() {
            try {
                  const data = await api('/api/examiner/examination')
                 this.examinations = data.examinations
             } catch (e) {
                 this.$root.flash(e.message)
           }
         },
        openCreate(exam) {
			this.slotExam = exam
            this.form = emptySlotForm()
             this.form.date = exam.slot_booking_start.slice(0, 10)  // slots are after booking starts
            window.scrollTo(0, 0)
        },
         async createSlot() {
            this.$root.clear()
            try {
                const data = await api('/api/examiner/slot', 'POST', { ...this.form, examination_id: this.slotExam.id })
                this.$root.flash(data.message)
                this.form = emptySlotForm()
                this.form.date = this.slotExam.slot_booking_start.slice(0, 10)
                this.load()
	        } catch (e) {
                this.$root.flash(e.message)
            }
        }
   }
}
