function showHideConfirm(field) {
    if (!field.is(":visible")) {
        if (window.confirm("View HIPPA Data?")) {
            field.toggle()
        }
    } else {
        field.toggle()
    }
}

window.onload = function () {
    (function ($) {
        const email_field = django.jQuery('#id_email')
        const email_button = $('<input type="button" value="HIPPA" />').on('click', () => {
            showHideConfirm(email_field)
        });
        email_button.prependTo(email_field.parent());

        const first_name_field = django.jQuery('#id_first_name')
        const first_name_button = $('<input type="button" value="HIPPA" />').on('click', () => {
            showHideConfirm(first_name_field)
        });
        first_name_button.prependTo(first_name_field.parent());

        const last_name_field = django.jQuery('#id_last_name')
        const last_name_button = $('<input type="button" value="HIPPA" />').on('click', () => {
            showHideConfirm(last_name_field)
        });
        last_name_button.prependTo(last_name_field.parent());

        email_field.hide();
        first_name_field.hide();
        last_name_field.hide();
    })(django.jQuery);
}
