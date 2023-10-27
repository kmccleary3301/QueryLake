export default function craftUrl(host : string, parameters : Object) {
  const url = new URL(host);
  url.searchParams.append("parameters", JSON.stringify(parameters));
  return url.toString();
}