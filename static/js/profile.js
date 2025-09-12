// This is here to allow linking to tabs ie: `/account/#password`
// will load the password tab via a like (from mobile or web) etc


const loadTab = () => {
    const hash = window.location.hash;
    if (hash) {
        $('#optionTabs .nav-link').removeClass('active');
        $('#tabOptions .tab-pane').removeClass('active show');

        const tab = $(hash + '-tab')
        tab.addClass('active');
        tab.addClass('active');

        const pane = $(tab.attr('data-bs-target'))
        pane.addClass('active show')
    }
}

$('#optionTabs .nav-link').click(function (e) {
    window.location.hash = $(this).attr('href');
    e.preventDefault();
});

document.addEventListener('DOMContentLoaded', loadTab)
window.addEventListener('hashchange', loadTab);
