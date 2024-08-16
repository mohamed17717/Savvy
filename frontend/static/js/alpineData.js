class xProgressToastModal {
  constructor() {
    this.progress = {
      percent: 50,
      message: "loading is in progress",
    };
  }

  init() {
    // let eventSource = new EventSource("http://localhost/fast/progress", {
    let eventSource = new EventSource("https://itab.ltd/fast/progress", {
      withCredentials: true,
    });

    eventSource.onopen = () => {
      document.querySelector("#progressToastModal")?.show();

      eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data);
        const data = JSON.parse(message.data);
        this.progress.percent = data.progress;
        this.progress.message = data.message;
        if (this.progress.percent === 100) {
          eventSource.close();
          document.querySelector("#progressToastModal")?.remove();
          // TODO inject cookie or local storage that its completed don't show it now
          // and when upload change this value to wait

          // setTimeout(() => {
          //   window.location.reload();
          // }, 2000);
        }
      };
    };
  }
}

class xUploadBookmarksModal {
  constructor() {
    this.progress = { percent: 0, message: "" };
    this.uploading = false;
  }
}

class xDashboardDetails {
  constructor() {
    this.bookmarks = [];
    this.totalBookmarks = 0;
    this.nextPage = null;
    this.view = "grid"; // TODO save latest view user choosed
    this.loadingNewBookmarks = false;
    this.loadingBookmarks = false;
    this.openFilterButtons = false;
    this.defaultIcon =
      "https://res.cloudinary.com/daily-now/image/upload/t_logo,f_auto/v1655817725/logos/community";

    this.searchQuery = new URLSearchParams(window.location.search);
    if (this.searchQuery.has("metaData")) {
      this.metaData = JSON.parse(this.searchQuery.get("metaData"));
    } else {
      this.metaData = {};
    }

    this.sideBarActive = this.searchQuery.get("sidebar") || "all"; // 'all'; // TODO save latest view user choosed

    this.appliedFilters = this.appliedFiltersToHumanArray();

    this.graphStarted = false;
    this.initialized = false;
  }

  appliedFiltersToHumanArray() {
    const filters = [];
    this.searchQuery.entries().forEach(([key, value]) => {
      if (key === "metaData") return;
      if (key === "sidebar") return;
      value.split(",").forEach((val) => {
        filters.push(`${key}: ${val}`);
      });
    });
    return filters;
  }

  translateFilterNumber(filter) {
    let [key, value] = filter.split(": ");
    value = value.trim();

    function isNumber(num) {
      if (num === "" || num === null) {
        return false;
      }
      return !isNaN(num);
    }

    if (isNumber(value)) {
      const newValue = this.metaData[value] || value;
      return `${key}: ${newValue}`;
    }

    return filter;
  }

  insertToAppliedFilters(key, value, reload = true) {
    if (this.searchQuery.has(key)) {
      // if has same value skip
      const oldValue = this.searchQuery.get(key);
      if (oldValue.split(",").includes(value)) return;

      this.searchQuery.set(key, `${value},${this.searchQuery.get(key)}`);
    } else {
      this.searchQuery.append(key, value);
    }
    if (reload) {
      window.history.replaceState({}, "", `?${this.searchQuery.toString()}`);
      this.appliedFilters = this.appliedFiltersToHumanArray();
      this.reloadBookmarks();
    }
  }

  updateAppliedFilter(key, value) {
    this.searchQuery.set(key, value);
    window.history.replaceState({}, "", `?${this.searchQuery.toString()}`);
    this.appliedFilters = this.appliedFiltersToHumanArray();
    this.reloadBookmarks();
  }

  removeAppliedFilter(key) {
    this.searchQuery.delete(key);
    window.history.replaceState({}, "", `?${this.searchQuery.toString()}`);
    this.appliedFilters = this.appliedFiltersToHumanArray();
    this.reloadBookmarks();
  }

  removeFromAppliedFilters(key, value, reload = true) {
    if (this.searchQuery.has(key)) {
      let oldValue = this.searchQuery.get(key).split(",");
      oldValue.splice(oldValue.indexOf(value), 1);
      oldValue = oldValue.join(",");
      if (oldValue === "") this.searchQuery.delete(key);
      else this.searchQuery.set(key, oldValue);
    }
    if (reload) {
      window.history.replaceState({}, "", `?${this.searchQuery.toString()}`);
      this.appliedFilters = this.appliedFiltersToHumanArray();
      this.reloadBookmarks();
    }
  }

  reloadBookmarks() {
    this.bookmarks = [];
    this.nextPage = null;
    this.totalBookmarks = 0;
    this.loadingNewBookmarks = false;
    this.loadingBookmarks = false
    this.initialized = false;
    this.init();
    this.openFilterButtons && dispatchEvent(new Event("open"));
  }

  async init() {
    if (this.initialized) return;
    this.initialized = true;
    this.loadingBookmarks = true
    let response = await bookmarkList(this.searchQuery, this.sideBarActive);
    this.totalBookmarks = response.count;
    this.bookmarks = response.results;
    this.loadingBookmarks = false
    if (response.next) this.nextPage = urlToPath(response.next);
    else this.nextPage = null;

    document.addEventListener("scroll", async () => {
      const yAxis = window.scrollY + window.innerHeight;
      if (yAxis >= document.body.scrollHeight - 700) {
        if (this.nextPage && !this.loadingNewBookmarks) {
          this.loadingNewBookmarks = true;
          response = await get(this.nextPage);
          this.bookmarks = [...this.bookmarks, ...response.results];
          if (response.next) this.nextPage = urlToPath(response.next);
          else this.nextPage = null;
          this.loadingNewBookmarks = false;
        }
      }
    });
  }
}

class xBookmarkFiltersModal {
  constructor() {
    // TODO search
    this.websites = [];
    this.websitesNextURL = null;
    this.websiteSearchParam = "website_search";
    this.websiteLoading = false;
    this.websiteSearchTask = null;

    this.topics = [];
    this.topicsNextURL = null;
    this.topicsSearchParam = "tags_search";
    this.topicLoading = false;
    this.topicSearchTask = null;
  }

  onOpen(data) {
    bookmarkFilterWebsiteChoices(data.searchQuery).then((data) => {
      this.websites = data.results;
      this.websitesNextURL = urlToPath(data.next);
    });
    bookmarkFilterTopicChoices(data.searchQuery).then((data) => {
      this.topics = data.results;
      this.topicsNextURL = urlToPath(data.next);
    });
  }
  onClose() {
    this.websites = [];
    this.websitesNextURL = null;
    this.topics = [];
    this.topicsNextURL = null;
  }

  loadMoreWebsites() {
    if (!this.websitesNextURL || this.websiteLoading) return;
    this.websiteLoading = true;
    get(this.websitesNextURL).then((data) => {
      this.websites = [...this.websites, ...data.results];
      this.websitesNextURL = urlToPath(data.next);
      this.websiteLoading = false;
    });
  }

  loadMoreTopics() {
    if (!this.topicsNextURL || this.topicLoading) return;
    this.topicLoading = true;
    get(this.topicsNextURL).then((data) => {
      this.topics = [...this.topics, ...data.results];
      this.topicsNextURL = urlToPath(data.next);
      this.topicLoading = false;
    });
  }

  searchWebsites(data, query) {
    if (this.websiteSearchTask) clearTimeout(this.websiteSearchTask);

    this.websiteSearchTask = setTimeout(() => {
      let searchQuery = new URLSearchParams(data.searchQuery.toString());
      searchQuery.set(this.websiteSearchParam, query);
      bookmarkFilterWebsiteChoices(searchQuery).then((data) => {
        this.websites = data.results;
        this.websitesNextURL = urlToPath(data.next);
      });
    }, 500);
  }

  searchTopics(data, query) {
    if (this.topicSearchTask) clearTimeout(this.topicSearchTask);

    this.topicSearchTask = setTimeout(() => {
      let searchQuery = new URLSearchParams(data.searchQuery.toString());
      searchQuery.set(this.topicsSearchParam, query);
      bookmarkFilterTopicChoices(searchQuery).then((data) => {
        this.topics = data.results;
        this.topicsNextURL = urlToPath(data.next);
      });
    }, 500);
  }

  unpackWebsiteForChange(website) {
    return {
      key: "websites",
      excludeKey: "exclude_websites",
      id: website.id,
      humanText: website.domain,
    };
  }

  unpackTopicForChange(topic) {
    return {
      key: "topics",
      excludeKey: "exclude_topics",
      id: topic.id,
      humanText: topic.name,
    };
  }

  onChangeChoice($el, data, { key, excludeKey, id, humanText }) {
    if ($el.checked) {
      data.metaData[id] = humanText;
      data.searchQuery.set("metaData", JSON.stringify(data.metaData));

      data.insertToAppliedFilters(key, id);
    } else {
      delete data.metaData[key];
      data.searchQuery.set("metaData", JSON.stringify(data.metaData));

      data.removeFromAppliedFilters(key, id);
      data.removeFromAppliedFilters(excludeKey, id);
    }
  }

  choiceIsChecked(data, { key, excludeKey, id }) {
    return (
      (data.searchQuery.has(key) &&
        data.searchQuery.get(key).split(",").includes(id.toString())) ||
      (data.searchQuery.has(excludeKey) &&
        data.searchQuery.get(excludeKey).split(",").includes(id.toString()))
    );
  }

  choiceIsExcluded(data, { excludeKey, id }) {
    return (
      data.searchQuery.has(excludeKey) &&
      data.searchQuery.get(excludeKey).split(",").includes(id.toString())
    );
  }
}

class xCookieAlert {
  constructor() {
    this.cookiePromptShow = false;
  }

  cookiePrompt(status) {
    localStorage.setItem("cookieStatus", status);
    document.querySelector("#cookieAlert")?.remove();
  }

  init() {
    setTimeout(() => {
      if (localStorage.getItem("cookieStatus") !== "true") {
        this.cookiePromptShow = true;
      }
    }, 10000);
  }
}
