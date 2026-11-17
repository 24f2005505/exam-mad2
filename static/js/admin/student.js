// template is in templates/admin/student.html
const AdminStudent = {
    template: '#admin-student',
    data() {
        return {
			students: [],
          query: ''
        }
   },
    created() {
          this.load()
    },
    methods: {
        async load() {
             try {
                const data = await api('/api/admin/student?query=' + encodeURIComponent(this.query))
                this.students = data.students
           } catch (e) {
			    this.$root.flash(e.message)
            }
        },
        async toggleBan(student) {
            this.$root.clear()
            try {
                	const data = await api('/api/admin/student/' + student.id + '/ban', 'POST', { ban: !student.banned })
                 this.$root.flash(data.message)
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
            }
        }
       }
}
