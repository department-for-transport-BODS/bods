class HttpClient {
  get(url) {
    return fetch(url, {
      mode: "cors",
      credentials: "same-origin",
      cache: "no-cache",
    }).then(this.checkStatus);
  }

  post(url, body) {
    return fetch(url, {
      method: "POST",
      body: body,
      mode: "cors",
      credentials: "omit",
    }).then(this.checkStatus);
  }

  checkStatus(response) {
    if (response.status >= 200 && response.status < 300) {
      return response;
    } else {
      var error = new Error(response.statusText);
      error.response = response;
      throw error;
    }
  }
}

export { HttpClient };
