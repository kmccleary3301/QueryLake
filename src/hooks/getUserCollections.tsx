type selectedState = [
  selected: boolean,
  setSelected: React.Dispatch<React.SetStateAction<boolean>>,
];

type collectionType = {
  title: string,
  items: number,
  hash_id: string,
  type: string,
}
  
type collectionGroup = {
  title: string,
  // toggleSelections: selectedState[],
  selected: selectedState,
  collections: collectionType[],
};

export default function getUserCollections(username : string, password_prehash: string, set_value: React.Dispatch<React.SetStateAction<any>>) {
  const url = new URL("http://localhost:5000/api/fetch_all_collections");
  url.searchParams.append("username", username);
  url.searchParams.append("password_prehash", password_prehash);
  let collection_groups_fetch : collectionGroup[] = [];

  let retrieved_data = {};

  fetch(url, {method: "POST"}).then((response) => {
    // console.log(response);
    response.json().then((data) => {
      // console.log(data);
      retrieved_data = data;
      if (data["success"] == false) {
        console.error("Collection error:", data["note"]);
        return;
      }
      try {
        let personal_collections : collectionGroup = {
          title: "My Collections",
          collections: [],
        };
        for (let i = 0; i < data.result.user_collections.length; i++) {
          console.log(data.result.user_collections[i]);
          personal_collections.collections.push({
            "title": data.result.user_collections[i]["name"],
            "hash_id": data.result.user_collections[i]["hash_id"],
            "items": data.result.user_collections[i]["document_count"],
            "type": data.result.user_collections[i]["type"]
          })
        }
        collection_groups_fetch.push(personal_collections);
      } catch { return; }
      try {
        let global_collections : collectionGroup = {
          title: "Global Collections",
          collections: [],
        };
        for (let i = 0; i < data["result"]["global_collections"].length; i++) {
          global_collections.collections.push({
            "title": data["result"]["global_collections"][i]["name"],
            "hash_id": data["result"]["global_collections"][i]["hash_id"],
            "items": data["result"]["global_collections"][i]["document_count"],
            "type": data["result"]["global_collections"][i]["type"]
          })
        }
        collection_groups_fetch.push(global_collections);
      } catch { return; }
      try {
        let organization_ids = Object.keys(retrieved_data.result.organization_collections)
        for (let j = 0; j < organization_ids.length; j++) {
          try {
            let org_id = organization_ids[j];
            let organization_specific_collections : collectionGroup = {
              title: retrieved_data.result.organization_collections[org_id].name,
              collections: [],
            };
            for (let i = 0; i < retrieved_data.result.organization_collections[org_id].collections.length; i++) {
              organization_specific_collections.collections.push({
                "title": retrieved_data.result.organization_collections[org_id].collections[i].name,
                "hash_id": retrieved_data.result.organization_collections[org_id].collections[i].hash_id,
                "items": retrieved_data.result.organization_collections[org_id].collections[i].document_count,
                "type": retrieved_data.result.organization_collections[org_id].collections[i].type,
              })
            }
            collection_groups_fetch.push(organization_specific_collections)
          } catch { return; }
        }
      } catch { return; }
      console.log("Start");
      set_value(collection_groups_fetch);
      console.log("End");
    });
  });
  // return collection_groups_fetch;
}