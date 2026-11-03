// Search toggling works without the retired S3 jQuery/custom.js bundle.
document.addEventListener('DOMContentLoaded', function () {
  var button = document.querySelector('.open-btn1');
  if (button) button.addEventListener('click', function (event) {
    event.preventDefault();
    var expanded = button.parentElement.classList.toggle('search-expanded');
    button.setAttribute('aria-expanded', String(expanded));
    if (expanded) document.getElementById('search-text').focus();
  });
});
