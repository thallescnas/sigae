function pegarCookieCsrf() {
  const cookies = document.cookie.split(";");
  for (let item of cookies) {
    const cookie = item.trim();
    if (cookie.startsWith("csrftoken=")) {
      return decodeURIComponent(cookie.substring("csrftoken=".length));
    }
  }
  return "";
}

