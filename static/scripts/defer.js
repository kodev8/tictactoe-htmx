handleCustomInputs();


// =========================================================
var textareas= document.querySelectorAll('textarea')

// Function to resize the textarea based on its content
function resizeTextarea(event) {
event.target.style.minHeight = 'auto'
event.target.style.minHeight = `${event.target.scrollHeight}px`;
}

// Listen for input events (typing)
textareas.forEach(textarea => textarea.addEventListener('input', resizeTextarea));

function handleTextAreas() {
  var textareas= document.querySelectorAll('textarea')

// Function to resize the textarea based on its content
function resizeTextarea(event) {
event.target.style.minHeight = 'auto'
event.target.style.minHeight = `${event.target.scrollHeight}px`;
}

// Listen for input events (typing)
textareas.forEach(textarea => textarea.addEventListener('input', resizeTextarea));
}