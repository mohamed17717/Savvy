class goto {
  static dashboard() {
    window.location.href = "/dashboard";
  }

  static login() {
    window.location.href = "/auth";
  }
}

class auth {
  static getToken() {
    let token = localStorage.getItem("token");
    let expiry = localStorage.getItem("expiry");

    if (token && expiry) {
      if (new Date().getTime() > expiry) {
        localStorage.removeItem("token");
        localStorage.removeItem("expiry");
        token = null;
        expiry = null;
      }
    }

    return token;
  }

  static setToken({ token, expiry }) {
    if (!token) return;

    localStorage.setItem("token", token);
    localStorage.setItem("expiry", expiry);
  }

  static removeToken() {
    localStorage.removeItem("token");
    localStorage.removeItem("expiry");
  }
}

class Backend {
  constructor(headers = {}) {
    // this.BASE_URL = "http://localhost";
    this.BASE_URL = "https://itab.ltd";
    this.headers = headers;

    let token = auth.getToken();
    if (token) {
      this.headers["Authorization"] = `Token ${token}`;
    }
  }
  request(path, method, data) {
    if (!path.startsWith("/")) throw new Error("Path must start with /");
    if (!path.startsWith("/api"))
      path = "/api" + path;

    let url = this.BASE_URL + path;

    const requestSetup = {
      method: method,
      headers: {
        "Content-Type": "application/json",
        ...this.headers,
      },
      credentials: "include",
    };
    if (data) {
      requestSetup.body = JSON.stringify(data);
    }

    return fetch(url, requestSetup)
      .then((response) => {
        if (response.status === 401) {
          logout()
          throw new Error('Token expired');
        }
        if (!response.ok) throw new Error(response.statusText);
        if (response.status === 204) return null;
        return response.json();
      })
      .then((data) => data)
      .catch((error) => {
        errorToast(error.message);
      });
  }

  get(url) {
    return this.request(url, "GET", null);
  }

  post(url, data) {
    if (!url.endsWith("/")) url += "/";
    return this.request(url, "POST", data);
  }

  patch(url, data) {
    if (!url.endsWith("/")) url += "/";
    return this.request(url, "PATCH", data);
  }

  delete(url, data) {
    if (!url.endsWith("/")) url += "/";
    return this.request(url, "DELETE", data);
  }

  getFormData(form) {
    const formData = new FormData(form);
    const values = [...formData.entries()];
    const data = {};
    for (const [key, value] of values) {
      data[key] = value;
    }
    return data;
  }
}

function errorToast(message) {
  const toast = document.createElement("div");
  toast.innerHTML = toastModal.innerHTML.replace(/\$\{message\}/, message);

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 5000);
}

function submitAuthForm($event) {
  $event.preventDefault();

  const backend = new Backend();

  const form = $event.target;
  const data = backend.getFormData(form);
  const url = form.getAttribute("action");

  return backend.post(url, data).then((data) => {
    auth.setToken(data);
    goto.dashboard();
  });
}

function get(path) {
  // TODO: remove this function
  const backend = new Backend();
  return backend.get(path);
}

function tagsList() {
  const path = "/bm/tag/list/";

  return get(path).then((data) => {
    const weights = data.map((item) => item.weight);
    const stepsCount = data.length;
    const maxWeight = Math.max(...weights);
    const minWeight = 0; //Math.min(...weights)
    const weightStep = (maxWeight - minWeight) / stepsCount;
    const maxRem = 2.5;
    const minRem = 0.5;
    const remStep = maxRem / stepsCount;

    for (let item of data) {
      newWeight = (item.weight / weightStep) * remStep + minRem;
      item.weight = parseFloat(newWeight.toFixed(2));
    }

    return data.sort(() => Math.random() - 0.5);
  });
}

function bookmarkList(searchQuery, listType = "all") {
  let path = {
    all: "/bm/bookmark/list/",
    favorite: "/bm/bookmark/favorite-list/",
    archive: "/bm/bookmark/archived-list/",
    trash: "/bm/bookmark/deleted-list/",
    history: "/bm/bookmark/history-list/",
    collections: "/bm/bookmark/list/",
  }[listType];

  if (searchQuery?.size > 0) {
    path += `?${searchQuery.toString()}`;
  }

  return get(path);
}

function bookmarkFilterWebsiteChoices(searchQuery) {
  let path = "/bm/filter/choices/website/";

  if (searchQuery) {
    let searchQueryClone = new URLSearchParams(searchQuery?.toString());

    searchQueryClone?.delete("websites");
    searchQueryClone?.delete("exclude_websites");

    if (searchQueryClone?.size > 0) {
      path += `?${searchQueryClone.toString()}`;
    }
  }

  return get(path);
}

function graphRoots(searchQuery) {
  let path = "/bm/graph/";

  if (searchQuery) {
    let searchQueryClone = new URLSearchParams(searchQuery?.toString());

    searchQueryClone?.delete("node");

    if (searchQueryClone?.size > 0) {
      path += `?${searchQueryClone.toString()}`;
    }
  }

  return get(path);
}

function graphChildren(parentId, searchQuery) {
  let path = `/bm/graph/${parentId}`;

  if (searchQuery) {
    let searchQueryClone = new URLSearchParams(searchQuery?.toString());

    searchQueryClone?.delete("node");

    if (searchQueryClone?.size > 0) {
      path += `?${searchQueryClone.toString()}`;
    }
  }

  return get(path);
}

function bookmarkFilterTopicChoices(searchQuery) {
  let path = "/bm/filter/choices/topic/";

  if (searchQuery) {
    let searchQueryClone = new URLSearchParams(searchQuery?.toString());

    searchQueryClone?.delete("topics");
    searchQueryClone?.delete("exclude_topics");

    if (searchQueryClone?.size > 0) {
      path += `?${searchQueryClone.toString()}`;
    }
  }

  return get(path);
}

function logout() {
  const path = "/users/logout/";
  return get(path).finally(() => {
    auth.removeToken();
    goto.login();
  });
}

function getCard(bookmarkId) {
  return document.querySelector(`[data-card-id="${bookmarkId}"]`);
}

function favoriteBookmark(bookmarkId, favorite) {
  const path = `/bm/bookmark/${bookmarkId}/`;
  const backend = new Backend();
  const data = { favorite };

  return backend.patch(path, data);
}

function archiveBookmark(bookmarkId) {
  const path = `/bm/bookmark/${bookmarkId}/`;
  const backend = new Backend();
  const data = { hidden: true };

  return backend.patch(path, data);
}

function deleteBookmark(bookmarkId) {
  const path = `/bm/bookmark/${bookmarkId}/`;
  const backend = new Backend();

  return backend.delete(path);
}

function deleteArchivedBookmark(bookmarkId) {
  const path = `/bm/bookmark/${bookmarkId}/archived-delete/`;
  const backend = new Backend();

  return backend.delete(path);
}

function permenantDeleteBookmark(bookmarkId) {
  const path = `/bm/bookmark/${bookmarkId}/permanent-delete/`;
  const backend = new Backend();

  return backend.delete(path);
}

function restoreBookmark(bookmarkId) {
  const path = `/bm/bookmark/${bookmarkId}/restore/`;
  return get(path);
}

function rcToggleStatus(rc, done) {
  const path = `/bm/bookmark/${rc}/`;

  const backend = new Backend();
  const data = {
    user_status: done ? 2 : 1,
  };

  return backend.patch(path, data);
}

function rcDelete(rc) {
  const path = `/bm/bookmark/${rc}/`;
  const backend = new Backend();
  return backend.delete(path);
}

function validateSize(input) {
  const fileSize = input.files[0].size / 1024 / 1024; // in MiB
  if (fileSize > 5) {
    errorToast("File size exceeds 5 MiB");
    input.value = "";
    return false;
  }
}

function submitBookmarkFile(form) {
  const headers = {
    Authorization: `Token ${auth.getToken()}`,
  };
  const data = new FormData(form);

  return axios.post('https://itab.ltd/api/bm/file/create/', data, {
    headers: headers,
    onUploadProgress: (progressEvent) => {
      const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      console.log(`Upload progress: ${progress}%`);
      form.querySelector('button.btn-disabled').innerText = `Uploading: ${progress}%`
    },
    withCredentials: true,
  })
  .then((response) => {
    return response.data;
  })
  .catch((error) => {
    if (error.response && error.response.status === 401) {
      logout();
      errorToast('Token expired');
      return false;
    }
    errorToast(error.message);
    return false;
  });
}


function urlToPath(url) {
  if(!url) return url
  const urlParts = new URL(url);
  return urlParts.pathname + urlParts.search;
}
