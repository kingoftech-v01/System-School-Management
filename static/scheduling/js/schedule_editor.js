/**
 * Schedule Editor - Drag-and-drop timetable editor using FullCalendar.
 */
(function () {
    'use strict';

    var calendarEl = document.getElementById('editor-calendar');
    if (!calendarEl) return;

    // CSRF token helper
    function getCSRFToken() {
        var cookie = document.cookie.split(';').find(function (c) {
            return c.trim().startsWith('csrftoken=');
        });
        return cookie ? cookie.split('=')[1] : '';
    }

    // Filters
    var filterFiliere = document.getElementById('filter-filiere');
    var filterProfessor = document.getElementById('filter-professor');
    var filterRoom = document.getElementById('filter-room');

    function getFilterParams() {
        var params = {};
        if (filterFiliere && filterFiliere.value) params.filiere_id = filterFiliere.value;
        if (filterProfessor && filterProfessor.value) params.professor_id = filterProfessor.value;
        if (filterRoom && filterRoom.value) params.room_id = filterRoom.value;
        return params;
    }

    // Initialize FullCalendar
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridWeek,timeGridDay'
        },
        slotMinTime: '07:00:00',
        slotMaxTime: '21:00:00',
        slotDuration: '01:00:00',
        allDaySlot: false,
        editable: true,
        droppable: true,
        selectable: true,
        weekends: true,
        firstDay: 1,
        height: 'auto',
        eventSources: [{
            url: '/api/v1/scheduling/entries/calendar_feed/',
            extraParams: getFilterParams
        }],

        // Drag external event onto calendar
        drop: function (info) {
            var courseId = info.draggedEl.getAttribute('data-course-id');
            if (!courseId) return;

            // Prompt for details or open create form
            window.location.href = '/scheduling/entries/create/?course_id=' + courseId;
        },

        // Drag existing event to new time
        eventDrop: function (info) {
            var entryId = info.event.extendedProps.entry_id;
            if (!entryId) {
                info.revert();
                return;
            }

            var data = {
                day_of_week: info.event.start.getDay() === 0 ? 6 : info.event.start.getDay() - 1,
                start_time: info.event.start.toTimeString().substring(0, 5),
                end_time: info.event.end ? info.event.end.toTimeString().substring(0, 5) : null
            };

            fetch('/api/v1/scheduling/entries/' + entryId + '/move/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(data)
            }).then(function (response) {
                if (!response.ok) {
                    info.revert();
                    if (typeof toastr !== 'undefined') {
                        toastr.error('Failed to move entry. There may be a conflict.');
                    }
                } else if (typeof toastr !== 'undefined') {
                    toastr.success('Entry moved successfully.');
                }
            }).catch(function () {
                info.revert();
            });
        },

        // Resize event
        eventResize: function (info) {
            // Reverting resize since time slots are fixed
            info.revert();
        },

        // Click on event to edit
        eventClick: function (info) {
            var props = info.event.extendedProps;
            var entryId = props.entry_id;
            if (!entryId) return;

            document.getElementById('modal-entry-id').value = entryId;
            document.getElementById('modal-course').value = info.event.title;

            if (props.professor_id) {
                var profSelect = document.getElementById('modal-professor');
                if (profSelect) profSelect.value = props.professor_id;
            }
            if (props.room_id) {
                var roomSelect = document.getElementById('modal-room');
                if (roomSelect) roomSelect.value = props.room_id;
            }

            var modal = new bootstrap.Modal(document.getElementById('editEntryModal'));
            modal.show();
        }
    });

    calendar.render();

    // Make external events draggable
    var externalEvents = document.getElementById('external-events');
    if (externalEvents && typeof FullCalendar.Draggable !== 'undefined') {
        new FullCalendar.Draggable(externalEvents, {
            itemSelector: '.fc-event',
            eventData: function (el) {
                return {
                    title: el.getAttribute('data-course-title') || el.innerText,
                    duration: '02:00'
                };
            }
        });
    }

    // Filter change handlers
    [filterFiliere, filterProfessor, filterRoom].forEach(function (el) {
        if (el) {
            el.addEventListener('change', function () {
                calendar.refetchEvents();
            });
        }
    });

    // Save entry changes from modal
    var btnSave = document.getElementById('btn-save-entry');
    if (btnSave) {
        btnSave.addEventListener('click', function () {
            var entryId = document.getElementById('modal-entry-id').value;
            var professorId = document.getElementById('modal-professor').value;
            var roomId = document.getElementById('modal-room').value;

            fetch('/api/v1/scheduling/entries/' + entryId + '/', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    professor: professorId,
                    room: roomId
                })
            }).then(function (response) {
                if (response.ok) {
                    calendar.refetchEvents();
                    bootstrap.Modal.getInstance(document.getElementById('editEntryModal')).hide();
                    if (typeof toastr !== 'undefined') toastr.success('Entry updated.');
                } else if (typeof toastr !== 'undefined') {
                    toastr.error('Failed to update entry.');
                }
            });
        });
    }

    // Delete entry from modal
    var btnDelete = document.getElementById('btn-delete-entry');
    if (btnDelete) {
        btnDelete.addEventListener('click', function () {
            var entryId = document.getElementById('modal-entry-id').value;
            if (!confirm('Are you sure you want to delete this entry?')) return;

            fetch('/api/v1/scheduling/entries/' + entryId + '/', {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCSRFToken() }
            }).then(function (response) {
                if (response.ok) {
                    calendar.refetchEvents();
                    bootstrap.Modal.getInstance(document.getElementById('editEntryModal')).hide();
                    if (typeof toastr !== 'undefined') toastr.success('Entry deleted.');
                }
            });
        });
    }
})();
