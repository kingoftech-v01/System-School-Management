/**
 * Scheduling Calendar - FullCalendar Integration
 * Handles calendar rendering, event sources, and user interactions.
 */
document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    var userRole = calendarEl.dataset.role || 'student';
    var isEditor = ['direction', 'admin', 'secretary'].indexOf(userRole) !== -1;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        initialDate: new Date(),
        locale: 'fr',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },

        // Time grid settings
        slotMinTime: '07:00:00',
        slotMaxTime: '21:00:00',
        slotDuration: '00:30:00',
        allDaySlot: true,
        nowIndicator: true,
        navLinks: true,
        weekNumbers: true,
        firstDay: 1, // Monday

        // Interaction
        editable: isEditor,
        selectable: isEditor,
        selectMirror: true,
        dayMaxEvents: true,

        // Event source: fetches from our API
        eventSources: [
            {
                url: '/api/v1/scheduling/entries/calendar_feed/',
                method: 'GET',
                extraParams: function() {
                    var params = {
                        include_events: 'true',
                        include_exceptions: 'true',
                    };
                    var filiereEl = document.getElementById('filter-filiere');
                    var profEl = document.getElementById('filter-professor');
                    var roomEl = document.getElementById('filter-room');

                    if (filiereEl && filiereEl.value) params.filiere_id = filiereEl.value;
                    if (profEl && profEl.value) params.professor_id = profEl.value;
                    if (roomEl && roomEl.value) params.room_id = roomEl.value;

                    return params;
                },
                failure: function() {
                    if (typeof toastr !== 'undefined') {
                        toastr.error('Failed to load schedule data.');
                    }
                }
            }
        ],

        // Event click -> show detail modal
        eventClick: function(info) {
            info.jsEvent.preventDefault();
            showEventDetailModal(info.event);
        },

        // Drag-and-drop (direction only)
        eventDrop: function(info) {
            if (!isEditor) {
                info.revert();
                return;
            }
            var props = info.event.extendedProps;
            if (props.type === 'event') {
                info.revert();
                return;
            }
            // TODO: POST to move endpoint
            if (typeof toastr !== 'undefined') {
                toastr.info('Schedule entry moved. (Save pending)');
            }
        },

        // Loading indicator
        loading: function(isLoading) {
            var spinner = document.getElementById('calendar-spinner');
            if (spinner) {
                spinner.style.display = isLoading ? 'block' : 'none';
            }
        }
    });

    calendar.render();
    window.scheduleCalendar = calendar;

    // Filter change handlers
    document.querySelectorAll('.schedule-filter').forEach(function(el) {
        el.addEventListener('change', function() {
            calendar.refetchEvents();
        });
    });
});

/**
 * Show event detail in a Bootstrap modal.
 */
function showEventDetailModal(event) {
    var props = event.extendedProps || {};
    var modal = document.getElementById('eventDetailModal');
    if (!modal) return;

    var titleEl = document.getElementById('eventDetailTitle');
    var bodyEl = document.getElementById('eventDetailBody');

    titleEl.textContent = event.title;

    var html = '<table class="table table-sm">';

    if (props.type === 'class') {
        html += '<tr><td><strong>Course</strong></td><td>' + (props.courseName || '') + ' (' + (props.courseCode || '') + ')</td></tr>';
        html += '<tr><td><strong>Professor</strong></td><td>' + (props.professorName || '') + '</td></tr>';
        html += '<tr><td><strong>Room</strong></td><td>' + (props.roomName || 'TBD') + '</td></tr>';
        html += '<tr><td><strong>Filiere</strong></td><td>' + (props.filiereName || '') + '</td></tr>';
        if (props.groupName) {
            html += '<tr><td><strong>Group</strong></td><td>' + props.groupName + '</td></tr>';
        }
        html += '<tr><td><strong>Time</strong></td><td>' + formatTime(event.start) + ' - ' + formatTime(event.end) + '</td></tr>';

        var statusBadge = '<span class="badge bg-success">Active</span>';
        if (props.status === 'cancelled') statusBadge = '<span class="badge bg-danger">Cancelled</span>';
        else if (props.status === 'substituted') statusBadge = '<span class="badge bg-warning">Substituted</span>';
        else if (props.status === 'room_changed') statusBadge = '<span class="badge bg-info">Room Changed</span>';
        html += '<tr><td><strong>Status</strong></td><td>' + statusBadge + '</td></tr>';

        if (props.reason) {
            html += '<tr><td><strong>Reason</strong></td><td>' + props.reason + '</td></tr>';
        }
    } else if (props.type === 'event') {
        html += '<tr><td><strong>Type</strong></td><td>' + (props.eventType || '') + '</td></tr>';
        html += '<tr><td><strong>Location</strong></td><td>' + (props.location || '') + '</td></tr>';
        html += '<tr><td><strong>Time</strong></td><td>' + formatTime(event.start) + ' - ' + formatTime(event.end) + '</td></tr>';
        if (props.description) {
            html += '<tr><td><strong>Description</strong></td><td>' + props.description + '</td></tr>';
        }
    }

    html += '</table>';
    bodyEl.innerHTML = html;

    var bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function formatTime(dt) {
    if (!dt) return '';
    return dt.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
