function toggleClass(element, toggledClass) {
    const offset = element.className.indexOf(toggledClass);
    if (offset == -1) {
        element.className = element.className.trim() + " " + toggledClass;
    } else {
        element.className = (
            element.className.substring(0, offset) +
            element.className.substring(offset + toggledClass.length)
        ).trim();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const admonitions = document.querySelectorAll(".admonition.foldable");
    for (let i = 0 ; i < admonitions.length ; ++i) {
        const adm = admonitions[i];
        const title = adm.querySelector(".admonition-title");
        title.addEventListener('click', function() {
            toggleClass(adm, "open");
        });
    }
});
