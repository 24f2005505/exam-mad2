// template is in templates/admin/course.html
function emptyCourseForm() {
   return { course_code: '', course_name: '', description: '', status: 'active' }
}

const AdminCourse = {
    template: '#admin-course',
    	data() {
        return {
            courses: [],
            query: '',
            editingId: null,   // id of the course being edited (null = adding a new one)
            form: emptyCourseForm()
      }
    },
    created() {
        this.load()
    },
    methods: {
        async load() {
            try {
                  const data = await api('/api/admin/course?query=' + encodeURIComponent(this.query))
                this.courses = data.courses
            } catch (e) {
                this.$root.flash(e.message)
            }
        },
         resetForm() {
            this.editingId = null
            this.form = emptyCourseForm()
       },
         edit(course) {
            this.editingId = course.id
            this.form = { course_code: course.course_code, course_name: course.course_name, description: course.description, status: course.status }
            window.scrollTo(0, 0)
        },
           async save() {
            this.$root.clear()
            try {
                let data
                if (this.editingId) {
                  data = await api('/api/admin/course/' + this.editingId, 'PUT', this.form)
	            } else {
                    data = await api('/api/admin/course', 'POST', this.form)
                   }
                this.$root.flash(data.message)
                this.resetForm()
                   this.load()
            } catch (e) {
              this.$root.flash(e.message)
           }
        },
        async remove(course) {
            if (!confirm('Delete the course ' + course.course_code + '?')) return
               this.$root.clear()
            try {
                const data = await api('/api/admin/course/' + course.id, 'DELETE')
                this.$root.flash(data.message)
                 this.load()
               } catch (e) {
                	this.$root.flash(e.message)
            }
        }
    }
}
