import craftUrl from "./craftUrl";

export default function getUserMemberships(username : string, 
                                            password_prehash: string, 
                                            subset: string, 
                                            set_value: React.Dispatch<React.SetStateAction<any>>, 
                                            set_admin?: React.Dispatch<React.SetStateAction<boolean>>) {
  const url = craftUrl("http://localhost:5000/api/fetch_memberships", {
    "username": username,
    "password_prehash": password_prehash,
    "return_subset": subset
  });

  fetch(url, {method: "POST"}).then((response) => {
    response.json().then((data) => {
      if (!data.success) {
        console.error("Failed to retrieve memberships", [data.note]);
        return;
      }
      if (set_admin) { set_admin(data.admin); }
      set_value(data.memberships);
    });
  });
}