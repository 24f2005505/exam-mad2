// template is in templates/admin/examination.html
function emptyExaminationForm() {
    	return {
        course_id: '', examination_name: '', examination_type: 'viva', duration: 30, maximum_marks: 100,
        slot_creation_start: '', slot_creation_end: '', slot_booking_start: '', slot_booking_end: '', instructions: ''
	}
}

const AdminExamination = {
    template: '#admin-examination',
    components: { AdminRubric },
    data() {
        return {
            examinations: [],
            courses: [],
			examiners: [],
            statuses: ['draft', 'slot_creation', 'booking_open', 'closed', 'completed'],
               query: '',
            editingId: null,
            form: emptyExaminationForm(),
			assignExam: null,   // examination whose examiners are being assigned
               assignIds: [],
            rubricExam: null    // examination whose rubric is open
      }
    },
    created() {
        this.load()
        this.loadOptions()
	},
	methods: {
        async load() {
          try {
                const data = await api('/api/admin/examination?query=' + encodeURIComponent(this.query))
                this.examinations = data.examinations
            } catch (e) {
		        this.$root.flash(e.message)
            }
        },
        async loadOptions() {
            // courses for the select box and examiners for assigning
            try {
                this.courses = (await api('/api/admin/course')).courses
              this.examiners = (await api('/api/admin/examiner')).examiners
           } catch (e) {
                this.$root.flash(e.message)
            	}
        },
        resetForm() {
            this.editingId = null
            	this.form = emptyExaminationForm()
        },
        edit(exam) {
            this.editingId = exam.id
               this.form = {
                course_id: exam.course_id, examination_name: exam.examination_name, examination_type: exam.examination_type,
              duration: exam.duration, maximum_marks: exam.maximum_marks,
                   slot_creation_start: exam.slot_creation_start, slot_creation_end: exam.slot_creation_end,
                slot_booking_start: exam.slot_booking_start, slot_booking_end: exam.slot_booking_end,
                instructions: exam.instructions
          }
            	window.scrollTo(0, 0)
        },
        async save() {
            this.$root.clear()
            try {
               let data
                if (this.editingId) {
                    data = await api('/api/admin/examination/' + this.editingId, 'PUT', this.form)
				} else {
                     data = await api('/api/admin/examination', 'POST', this.form)
                }
                	this.$root.flash(data.message)
                this.resetForm()
                this.load()
            } catch (e) {
              this.$root.flash(e.message)
	        }
        },
          async remove(exam) {
           if (!confirm('Delete ' + exam.examination_name + '? Its rubric and slots will be deleted too.')) return
              this.$root.clear()
            try {
                const data = await api('/api/admin/examination/' + exam.id, 'DELETE')
                this.$root.flash(data.message)
                this.load()
	        } catch (e) {
               this.$root.flash(e.message)
            }
           },
        async changeStatus(exam, status) {
            this.$root.clear()
            try {
                 const data = await api('/api/admin/examination/' + exam.id + '/status', 'POST', { status: status })
                this.$root.flash(data.message)
            } catch (e) {
                this.$root.flash(e.message)
            }
            this.load()
        },
        openAssign(exam) {
            this.assignExam = exam
	        this.assignIds = exam.examiners.map(examiner => examiner.id)
            this.loadOptions()
            window.scrollTo(0, 0)
        },
        async saveAssign() {
            this.$root.clear()
            try {
                   const data = await api('/api/admin/examination/' + this.assignExam.id + '/examiners', 'POST', { examiner_ids: this.assignIds })
                this.$root.flash(data.message)
                this.assignExam = null
                this.load()
          } catch (e) {
                this.$root.flash(e.message)
           }
        },
        async togglePublish(exam) {
           this.$root.clear()
              try {
                const data = await api('/api/admin/examination/' + exam.id + '/publish', 'POST', { publish: !exam.results_published })
                this.$root.flash(data.message)
                this.load()
	        } catch (e) {
                this.$root.flash(e.message)
            }
          }
    }
}
