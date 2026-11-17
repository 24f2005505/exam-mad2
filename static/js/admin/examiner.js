// template is in templates/admin/examiner.html
function emptyExaminerForm() {
    return {
		fname: '', lname: '', username: '', email: '',
        password: '', department: '', contact_details: '', status: 'active'
    	}
}

const AdminExaminer = {
      template: '#admin-examiner',
    data() {
      return {
            examiners: [],
			query: '',
            editingId: null,
            form: emptyExaminerForm()
        	}
    },
    created() {
        this.load()
    },
    methods: {
       async load() {
            try {
                 const data = await api('/api/admin/examiner?query=' + encodeURIComponent(this.query))
                this.examiners = data.examiners
            } catch (e) {
		        this.$root.flash(e.message)
            }
         },
	    resetForm() {
            this.editingId = null
		    this.form = emptyExaminerForm()
        },
        edit(examiner) {
            this.editingId = examiner.id
              this.form = {
                 fname: examiner.fname, lname: examiner.lname, email: examiner.email,
                department: examiner.department, contact_details: examiner.contact_details, status: examiner.status
            }
            window.scrollTo(0, 0)
        },
        async save() {
            this.$root.clear()
            try {
                let data
                if (this.editingId) {
                    data = await api('/api/admin/examiner/' + this.editingId, 'PUT', this.form)
                   } else {
			        data = await api('/api/admin/examiner', 'POST', this.form)
                	}
                this.$root.flash(data.message)
                 this.resetForm()
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
        },
        async toggleStatus(examiner) {
	        this.$root.clear()
		    const form = {
              fname: examiner.fname, lname: examiner.lname, email: examiner.email,
                department: examiner.department, contact_details: examiner.contact_details,
                 status: examiner.status === 'active' ? 'inactive' : 'active'
            }
            try {
                const data = await api('/api/admin/examiner/' + examiner.id, 'PUT', form)
                this.$root.flash(data.message)
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
           }
    }
}
