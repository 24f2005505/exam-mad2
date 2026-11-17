// template is in templates/examiner/evaluation.html
const ExaminerEvaluation = {
    template: '#examiner-evaluation',
    data() {
        return {
           pending: [],
              done: [],
			booking: null,   // booking being evaluated
            rubrics: [],
            scores: {},      // rubric id -> marks
            	remarks: ''
      }
    },
    computed: {
        total() {
            // same formula as flask: sum of (marks x weightage)
            let total = 0
            	for (const rubric of this.rubrics) {
                	total += (Number(this.scores[rubric.id]) || 0) * rubric.weightage
	        }
            return Math.round(total * 100) / 100
         }
    },
    created() {
        this.load()
	},
	methods: {
      async load() {
            try {
                  const data = await api('/api/examiner/evaluation')
                this.pending = data.pending
              this.done = data.done
            } catch (e) {
                this.$root.flash(e.message)
            }
        },
       async open(item) {
            	this.$root.clear()
		    try {
                const data = await api('/api/examiner/booking/' + item.id + '/evaluate')
                this.booking = data.booking
                this.rubrics = data.rubrics
               // fill in old marks when editing an evaluation
                const old = data.booking.evaluation
                this.scores = old ? { ...old.rubric_scores } : {}
                this.remarks = old ? old.remarks : ''
	            window.scrollTo(0, 0)
            } catch (e) {
                this.$root.flash(e.message)
            }
         },
      async submit() {
               this.$root.clear()
			try {
                const data = await api('/api/examiner/booking/' + this.booking.id + '/evaluate', 'POST', { scores: this.scores, remarks: this.remarks })
              this.$root.flash(data.message)
                this.booking = null
                this.load()
            } catch (e) {
                this.$root.flash(e.message)
           }
	    }
    }
}
