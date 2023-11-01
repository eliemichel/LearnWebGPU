$(document).ready(function() {
    $(".admonition.diff > *").hide();
    $(".admonition.diff .admonition-title").show();
    $(".admonition.diff .admonition-title").click(function() {
        $(this).parent().children().not(".admonition-title").toggle(400);
        $(this).parent().children(".admonition-title").toggleClass("open");
    })
});
