export default function craftUrl(host : string, parameters : object) {
  const url = new URL(host);
  const stringed_json = JSON.stringify(parameters);
  url.searchParams.append("parameters", stringed_json);
  return url.toString();
}