(function ($) {
    const name = 'cookielaw_accepted'

    if (document.cookie.indexOf(name) >= 0) {
        $('#cookielaw').hide()
    }
    $("#cookielaw_accept").click(() => {
        document.cookie = `${name}=1; expires=Fri, 31 Dec 9999 23:59:59 GMT; path=/; Secure`;
        $('#cookielaw').hide()
    })
}(jQuery));
