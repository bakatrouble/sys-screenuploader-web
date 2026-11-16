$(document).on('click', '.modal-dismiss', function (e) {
    e.preventDefault();
    $.magnificPopup.close();
});

$(document).on('click', '.clickable-row', function() {
    window.location = $(this).data('href');
});
