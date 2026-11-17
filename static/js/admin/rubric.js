// template is in templates/admin/rubric.html
// used inside the examination page, gets the examination as a prop
function emptyRubricForm() {
	return { criterion_name: '', maximum_marks: 10, weightage: 1, description: '' }
}

const AdminRubric = {
    template: '#admin-rubric',
    	props: ['examination'],
   emits: ['close'],
    data() {
        return {
           rubrics: [],
		    total: 0,
            maximumMarks: 0,
            editingId: null,
            form: emptyRubricForm()
       }
    },
    created() {
        this.load()
	},
    watch: {
        // another examination's rubric was opened
        'examination.id'() {
           this.resetForm()
	        this.load()
	    }
    },
    methods: {
        async load() {
            try {
                   const data = await api('/api/admin/examination/' + this.examination.id + '/rubric')
				this.rubrics = data.rubrics
                this.total = data.total
              this.maximumMarks = data.maximum_marks
            } catch (e) {
                this.$root.flash(e.message)
               }
       },
           resetForm() {
            this.editingId = null
            this.form = emptyRubricForm()
        },
         edit(rubric) {
            this.editingId = rubric.id
               this.form = { criterion_name: rubric.criterion_name, maximum_marks: rubric.maximum_marks, weightage: rubric.weightage, description: rubric.description }
          },
        async save() {
            	this.$root.clear()
            try {
                let data
                  if (this.editingId) {
                       data = await api('/api/admin/rubric/' + this.editingId, 'PUT', this.form)
                } else {
                    data = await api('/api/admin/examination/' + this.examination.id + '/rubric', 'POST', this.form)
	            }
                 this.$root.flash(data.message)
                this.resetForm()
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
        },
        async remove(rubric) {
            if (!confirm('Delete the criterion ' + rubric.criterion_name + '?')) return
		    this.$root.clear()
	        try {
               const data = await api('/api/admin/rubric/' + rubric.id, 'DELETE')
                this.$root.flash(data.message)
                this.load()
            } catch (e) {
	            this.$root.flash(e.message)
	        }
        }
    }
}
