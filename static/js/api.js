// small helpers used by every component

// calls the flask api, returns the json, throws an error with flask's message if something went wrong
async function api(url, method = 'GET', body = null) {
    const options = { method: method, headers: {} }
    if (body !== null) {
        options.headers['Content-Type'] = 'application/json'
        options.body = JSON.stringify(body)
	}
    let response
    try {
         response = await fetch(url, options)
    } catch (e) {
        throw new Error('Could not connect to the Flask server.')
    }
    let data
    try {
        data = await response.json()
    } catch (e) {
        throw new Error('Server error, check the Flask terminal.')
   }
    if (!response.ok) {
      throw new Error(data.error || 'Something went wrong.')
    }
    	return data
}

// slot_creation -> Slot Creation
function label(text) {
  if (text === null || text === undefined) return ''
      return String(text).split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

// 2026-11-11T10:00 -> 2026-11-11 10:00
function dt(text) {
   return text ? text.replace('T', ' ') : ''
}
