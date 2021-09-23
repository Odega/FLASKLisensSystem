function deleteNote(noteId){
    fetch('/delete-note', {
        method: 'POST',
        body: JSON.stringify({ noteId: noteId})
    }).then((_res) => {
        window.location.href = "/notes";
    })
}
function deleteSchoolNote(noteId, skoleNavn,orgNr, kommune){
    fetch('/delete-school-note', {
        method: 'POST',
        body: JSON.stringify({ noteId: noteId})
    }).then((_res) => {
        window.location.href = "/skole/"+skoleNavn+"?orgNr="+orgNr+"&kommune="+kommune;
    })
}