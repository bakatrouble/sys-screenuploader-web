$(document).on('click', '.modal-dismiss', function (e) {
    e.preventDefault();
    $.magnificPopup.close();
});

$(document).on('click', '.clickable-row', function() {
    Turbolinks.visit($(this).data('href'));
});

$(document).on('turbolinks:before-cache', function() {
    $('form').trigger('reset')
});
