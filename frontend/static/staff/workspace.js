document.addEventListener('DOMContentLoaded', function () {
  var navigation = document.querySelector('.workspace-nav');
  var path = window.location.pathname;
  var current = null;
  if (navigation) {
    navigation.querySelectorAll('nav>a').forEach(function (link) {
      var target = link.getAttribute('href');
      if (path === target || (target !== '/staff' && path.indexOf(target + '/') === 0)) {
        if (!current || target.length > current.getAttribute('href').length) current = link;
      }
    });
    if (current) { current.classList.add('active'); current.setAttribute('aria-current', 'page'); }
    var toggle = navigation.querySelector('.mobile-nav-toggle');
    toggle.addEventListener('click', function () {
      var expanded = navigation.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(expanded));
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && navigation.classList.contains('is-open')) {
        navigation.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus();
      }
    });
  }
  var main = document.querySelector('.section-wrapper');
  if (main) { main.id = 'main-content'; main.setAttribute('tabindex', '-1'); }
  var login = document.querySelector('#login_form');
  if (login) {
    var email = login.querySelector('input[name=email]');
    var password = login.querySelector('input[name=password]');
    if (email) { email.setAttribute('autocomplete', 'username'); email.setAttribute('placeholder', 'you@company.com'); }
    if (password) {
      password.setAttribute('autocomplete', 'current-password'); password.setAttribute('placeholder', 'Enter your password');
      var wrap = document.createElement('div'); wrap.className = 'password-control';
      password.parentNode.insertBefore(wrap, password); wrap.appendChild(password);
      var reveal = document.createElement('button'); reveal.type = 'button'; reveal.className = 'password-toggle'; reveal.textContent = 'Show'; reveal.setAttribute('aria-label', 'Show password'); reveal.setAttribute('aria-pressed', 'false');
      reveal.addEventListener('click', function () {
        var show = password.type === 'password'; password.type = show ? 'text' : 'password';
        reveal.textContent = show ? 'Hide' : 'Show'; reveal.setAttribute('aria-label', show ? 'Hide password' : 'Show password'); reveal.setAttribute('aria-pressed', String(show));
      }); wrap.appendChild(reveal);
    }
  }
});
// Keep destructive card actions deliberate without changing their existing routes.
document.addEventListener('click', function (event) {
  var button = event.target.closest('.listing-button button');
  if (button && /delete/.test(button.getAttribute('onclick') || '')) {
    if (!window.confirm('Delete this item? This action cannot be undone.')) {
      event.preventDefault(); event.stopImmediatePropagation();
    }
  }
}, true);
