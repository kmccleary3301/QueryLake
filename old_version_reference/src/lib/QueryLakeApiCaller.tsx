import EventSource from "../lib/react-native-server-sent-events";


class QueryLakeAPI {
  constructor(host_address : string) {
    this.host_address = host_address;
    this.query_opened = false;
  }

  hexToUtf8(s : string) {
    return decodeURIComponent(
      s.replace(/\s+/g, '') // remove spaces
      .replace(/[0-9a-f]{2}/g, '%$&') // add '%' before each 2 characters
    );
  }

  async fetch_query(api_route : string, params : object, on_finish : () => void, on_message : (token : string) => void) {
    const url = new URL(this.host_address+api_route);
    url.searchParams.append("parameters", JSON.stringify(params));

    const es = new EventSource(url, {
      method: "GET",
    });

    es.addEventListener("open", (event) => {
      console.log("Open SSE connection.");
      this.query_opened = true;
    });

    es.addEventListener("message", (event) => {
      if (event === undefined || event.data === undefined) return;
      let decoded = event.data.toString();
      decoded = this.hexToUtf8(decoded);
      if (decoded == "-DONE-") {
        es.close();
      } else {
        on_message(decoded);
      }
    });
  }

  call(api_route : string, params : object) {
    const url = new URL(this.host_address+api_route);
    url.searchParams.append("parameters", JSON.stringify(params));
    fetch(url, {method: "POST"}).then((response) => {
      response.json().then((data) => {
          if (data.success == false) {
            console.error("Error on call", api_route, "\nNote: ", data.note);
            return
          }
          return data.result;
      });
    });
  }
}

export default QueryLakeAPI;